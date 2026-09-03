#!/usr/bin/env python3
"""Run one bounded Metal-physics/MPS-learner scaling measurement."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def synchronize(torch) -> float:
    started = time.perf_counter()
    torch.mps.synchronize()
    return time.perf_counter() - started


def thermal_snapshot() -> dict[str, str]:
    result = subprocess.run(["pmset", "-g", "therm"], capture_output=True, text=True)
    text = (result.stdout + result.stderr).strip()
    nominal = result.returncode == 0 and "No thermal warning level has been recorded" in text
    return {
        "state": "nominal" if nominal else "warning_or_unavailable",
        "raw": text,
    }


def all_finite(value, torch) -> bool:
    if isinstance(value, dict):
        return all(all_finite(item, torch) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(all_finite(item, torch) for item in value)
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all().item())
    return True


def learner_parameters_finite(algorithm, torch) -> bool:
    """Check the separate actor/critic modules exposed by RSL-RL 5.4."""
    parameters = list(algorithm.actor.parameters()) + list(algorithm.critic.parameters())
    return all_finite(parameters, torch)


def run(num_envs: int) -> dict[str, object]:
    if sys.platform != "darwin":
        raise RuntimeError("Apple scaling benchmark requires macOS")
    import genesis as gs
    import torch
    from rsl_rl.runners import OnPolicyRunner
    from microduck.velocity_cfg import TRAIN_CFG
    from microduck.velocity_env import MicroduckVelocityEnv

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS learner device is unavailable")
    thermal_before = thermal_snapshot()
    total_memory = int(command("sysctl", "-n", "hw.memsize"))
    gs.init(backend=gs.metal, logging_level="warning")
    if gs.backend != gs.metal:
        raise RuntimeError(f"Metal backend requested, got {gs.backend}")
    started = time.perf_counter()
    env = MicroduckVelocityEnv(num_envs=num_envs)
    construction_s = time.perf_counter() - started
    started = time.perf_counter()
    env.reset()
    synchronization_s = synchronize(torch)
    reset_s = time.perf_counter() - started

    cfg = dict(TRAIN_CFG)
    cfg["run_name"] = f"apple-scaling-{num_envs}"
    cfg["seed"] = 86000 + num_envs
    records: list[dict[str, float]] = []
    with tempfile.TemporaryDirectory(prefix=f"microduck-scaling-{num_envs}-") as log_dir:
        runner = OnPolicyRunner(env, cfg, log_dir, device="mps")
        runner.logger.init_logging_writer = lambda: None
        runner.logger.log = lambda **kwargs: records.append({
            "collection_s": float(kwargs["collect_time"]),
            "learner_update_s": float(kwargs["learn_time"]),
        })
        runner.save = lambda *_args, **_kwargs: None
        warm_started = time.perf_counter()
        runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)
        warmup_iteration_s = time.perf_counter() - warm_started
        records.clear()
        synchronization_s += synchronize(torch)
        measured_started = time.perf_counter()
        runner.learn(num_learning_iterations=1, init_at_random_ep_len=False)
        synchronization_s += synchronize(torch)
        total_iteration_s = time.perf_counter() - measured_started
    if len(records) != 1:
        raise RuntimeError("expected exactly one measured PPO iteration")
    finite = {
        "observations": all_finite(env.get_observations(), torch),
        "learner_parameters": learner_parameters_finite(runner.alg, torch),
    }
    if not all(finite.values()):
        raise RuntimeError(f"non-finite state after benchmark iteration: {finite}")
    env_steps = int(cfg["num_steps_per_env"]) * num_envs
    peak_rss_bytes = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    thermal_after = thermal_snapshot()
    return {
        "schema_version": "microduck.apple-scaling-row/v1",
        "num_envs": num_envs,
        "construction_s": construction_s,
        "warmup_iteration_s": warmup_iteration_s,
        "collection_s": records[0]["collection_s"],
        "learner_update_s": records[0]["learner_update_s"],
        "total_iteration_s": total_iteration_s,
        "reset_s": reset_s,
        "synchronization_s": synchronization_s,
        "env_steps_per_s": env_steps / records[0]["collection_s"],
        "samples_per_minute": env_steps * 60.0 / total_iteration_s,
        "peak_rss_bytes": peak_rss_bytes,
        "unified_memory": {
            "method": "peak_process_rss_proxy",
            "proxy_bytes": peak_rss_bytes,
            "system_physical_bytes": total_memory,
            "headroom_fraction_proxy": max(0.0, 1.0 - peak_rss_bytes / total_memory),
            "limitations": "ru_maxrss is process resident memory, not complete Metal allocation or system-wide unified-memory pressure",
        },
        "devices": {"physics": "metal", "learner": "mps"},
        "backend": {"genesis": str(gs.backend), "torch_mps_available": True},
        "thermal": {
            "method": "pmset_-g_therm_historical_warning_state",
            "state_before": thermal_before["state"],
            "state_after": thermal_after["state"],
            "raw_before": thermal_before["raw"],
            "raw_after": thermal_after["raw"],
            "limitations": "pmset exposes warning state, not temperature, power, fan speed, or continuous throttling telemetry",
        },
        "finite": finite,
        "termination_reason": "completed",
        "benchmark": {"warmup_iterations": 1, "measured_iterations": 1, "rollout_steps_per_env": int(cfg["num_steps_per_env"]), "seed": cfg["seed"]},
        "source": {"commit": command("git", "rev-parse", "HEAD"), "dirty": bool(command("git", "status", "--porcelain"))},
        "machine": {"model": command("sysctl", "-n", "hw.model"), "system": platform.system(), "release": platform.release(), "serial_recorded": False},
        "packages": {name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib")},
        "proof_class": "performance_characterization",
        "task_success": "not_evaluated",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-envs", type=int, required=True, choices=(64,128,256,512,1024))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.num_envs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
