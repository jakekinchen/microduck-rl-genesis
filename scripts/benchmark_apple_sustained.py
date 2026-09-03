#!/usr/bin/env python3
"""Run the preregistered 1024-environment Apple sustained PPO slice."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))

from benchmarks.apple_scaling import summarize_sustained, validate_sustained
from scripts.benchmark_apple_scaling import all_finite, command, learner_parameters_finite, synchronize, thermal_snapshot


NUM_ENVS = 1024
WARMUP_ITERATIONS = 2
MEASURED_ITERATIONS = 120


def run() -> dict[str, object]:
    if sys.platform != "darwin":
        raise RuntimeError("Apple sustained benchmark requires macOS")
    import genesis as gs
    import torch
    from rsl_rl.runners import OnPolicyRunner
    from microduck.velocity_cfg import TRAIN_CFG
    from microduck.velocity_env import MicroduckVelocityEnv

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS learner device is unavailable")
    source = {"commit": command("git", "rev-parse", "HEAD"), "dirty": bool(command("git", "status", "--porcelain"))}
    if source["dirty"]:
        raise RuntimeError("sustained benchmark requires a clean source commit")
    total_memory = int(command("sysctl", "-n", "hw.memsize"))
    thermal_samples = [{"point": "before_construction", **thermal_snapshot()}]
    gs.init(backend=gs.metal, logging_level="warning")
    construction_started = time.perf_counter()
    env = MicroduckVelocityEnv(num_envs=NUM_ENVS)
    construction_s = time.perf_counter() - construction_started
    reset_started = time.perf_counter()
    env.reset()
    synchronization_s = synchronize(torch)
    reset_s = time.perf_counter() - reset_started

    cfg = dict(TRAIN_CFG)
    cfg["run_name"] = "apple-sustained-1024"
    cfg["seed"] = 871024
    iterations: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="microduck-sustained-1024-") as log_dir:
        runner = OnPolicyRunner(env, cfg, log_dir, device="mps")
        runner.logger.init_logging_writer = lambda: None
        runner.logger.log = lambda **_kwargs: None
        runner.save = lambda *_args, **_kwargs: None
        warmup_started = time.perf_counter()
        runner.learn(num_learning_iterations=WARMUP_ITERATIONS, init_at_random_ep_len=False)
        synchronization_s += synchronize(torch)
        warmup_s = time.perf_counter() - warmup_started
        thermal_samples.append({"point": "after_warmup", **thermal_snapshot()})

        iteration_started = time.perf_counter()

        def record_iteration(**kwargs) -> None:
            nonlocal iteration_started, synchronization_s
            sync_s = synchronize(torch)
            synchronization_s += sync_s
            now = time.perf_counter()
            index = len(iterations) + 1
            finite = {
                "observations": all_finite(env.get_observations(), torch),
                "learner_parameters": learner_parameters_finite(runner.alg, torch),
            }
            iterations.append({
                "index": index,
                "collection_s": float(kwargs["collect_time"]),
                "learner_update_s": float(kwargs["learn_time"]),
                "synchronization_s": sync_s,
                "total_iteration_s": now - iteration_started,
                "finite": finite,
            })
            if not all(finite.values()):
                raise RuntimeError(f"non-finite state at measured iteration {index}")
            if index % 10 == 0:
                sample = {"point": f"iteration_{index}", **thermal_snapshot()}
                thermal_samples.append(sample)
                if sample["state"] != "nominal":
                    raise RuntimeError(f"thermal warning at measured iteration {index}")
            iteration_started = time.perf_counter()

        runner.logger.log = record_iteration
        runner.learn(num_learning_iterations=MEASURED_ITERATIONS, init_at_random_ep_len=False)
    thermal_samples.append({"point": "after_completion", **thermal_snapshot()})
    peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    steps_per_env = int(cfg["num_steps_per_env"])
    receipt = {
        "schema_version": "microduck.apple-sustained/v1",
        "num_envs": NUM_ENVS,
        "construction_s": construction_s,
        "reset_s": reset_s,
        "warmup_s": warmup_s,
        "synchronization_s": synchronization_s,
        "iterations": iterations,
        "summary": summarize_sustained(iterations, NUM_ENVS, steps_per_env),
        "peak_rss_bytes": peak_rss_bytes,
        "unified_memory": {
            "method": "peak_process_rss_proxy",
            "proxy_bytes": peak_rss_bytes,
            "system_physical_bytes": total_memory,
            "headroom_fraction_proxy": max(0.0, 1.0 - peak_rss_bytes / total_memory),
            "limitations": "ru_maxrss omits complete Metal allocation and system-wide unified-memory pressure",
        },
        "devices": {"physics": "metal", "learner": "mps"},
        "backend": {"genesis": str(gs.backend), "torch_mps_available": True},
        "thermal_samples": thermal_samples,
        "benchmark": {"warmup_iterations": WARMUP_ITERATIONS, "measured_iterations": MEASURED_ITERATIONS, "rollout_steps_per_env": steps_per_env, "seed": cfg["seed"]},
        "source": source,
        "machine": {"model": command("sysctl", "-n", "hw.model"), "system": platform.system(), "release": platform.release(), "serial_recorded": False},
        "packages": {name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib")},
        "termination_reason": "completed",
        "proof_class": "performance_characterization",
        "task_success": "not_evaluated",
        "limitations": "Public development workload; pmset warning state is not continuous temperature, power, fan, or throttling telemetry; no checkpoint retained",
    }
    validate_sustained(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
