"""Bounded V18 internal-load-aware walking refinement from exact V13 FINAL."""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
PARENT_SHA = "f31d47a5343b1283a1bbd28c2f7efb78f95ddd6940554b9c755b73d337c2b7f8"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=250)
    p.add_argument("--seed", type=int, default=26090618)
    a = p.parse_args()
    if (not a.run_id.replace("-", "").isalnum() or (a.num_envs, a.iterations) not in ((64,5),(1024,250)) or a.seed != 26090618):
        p.error("new simple ID, frozen 64x5 smoke or 1024x250 full run, seed26090618")
    parent = ROOT/"receipts/walking/20260905-v13-training-complete"
    prior = json.loads((parent/"training.json").read_text())
    checkpoint = parent/"model_749.pt"
    if prior["status"] != "completed" or prior["checkpoint_sha256"] != PARENT_SHA or digest(checkpoint) != PARENT_SHA:
        raise ValueError("exact V13 FINAL required")
    for name, sha in prior["source_sha256"].items():
        if digest(ROOT/name) != sha or digest(parent/"source"/name) != sha:
            raise ValueError("parent source drift")
    baseline = ROOT/"receipts/walking/20260906-v16-command-ramp-diagnostic"
    # This is a diagnostic, not a final-policy receipt. Verify its actual
    # schema-specific evidence instead of demanding nonexistent policy files.
    covered = set()
    for line in (baseline/"SHA256SUMS").read_text().splitlines():
        sha, name = line.split("  ", 1)
        path = (baseline/name).resolve()
        if not path.is_relative_to(baseline.resolve()) or digest(path) != sha or name in covered:
            raise ValueError("diagnostic manifest mismatch")
        covered.add(name)
    if not {"probe.json", "trajectory.jsonl", "suite.json", "diagnostic-freeze.json"} <= covered:
        raise ValueError("incomplete diagnostic evidence")
    evaluation = json.loads((baseline/"probe.json").read_text())
    if (evaluation["combined_passed_cases"] != 5 or evaluation["total_cases"] != 6
            or evaluation["candidate_selection_eligible"]):
        raise ValueError("retained 5/6 V16 diagnostic required")
    for case in evaluation["case_reports"]:
        if not {case["case_id"]+".mp4", case["case_id"]+"-actions-float32.npy"} <= covered:
            raise ValueError("missing diagnostic video/actions")
    from scripts.evaluate_walking_unbraced import FREEZE, SOURCES
    for name, sha in json.loads(FREEZE.read_text())["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"frozen source drift: {name}")
    out = ROOT/"logs"/a.run_id
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v18",
              "proof_class": "first_party_development", "held_out": False, "target_source": "velocity-command",
              "args": vars(a), "status": "starting", "planned_new_transitions": a.num_envs*a.iterations*24,
              "new_transitions": 0, "pid": __import__("os").getpid(),
              "standing_pair_baseline_manifest_sha256": digest(baseline/"SHA256SUMS")}
    started, runner = time.monotonic(), None
    try:
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        import torch
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_unbraced_env import MicroduckUnbracedWalkingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        cfg["algorithm"]["learning_rate"] = 2e-4
        sources = list(dict.fromkeys(list(prior["source_sha256"])+SOURCES+[
            "scripts/train_walking_unbraced.py", "experiments/walking/evaluator-freeze-unbraced-v18-r2.json"]))
        sources += ["microduck/assets/microduck/robot_allcollisions.xml", "microduck/assets/microduck/scene.xml"]
        sources += [str(path.relative_to(ROOT)) for path in sorted((ROOT/"microduck/assets/microduck/assets").iterdir()) if path.is_file()]
        record.update(train_cfg=cfg,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            source_sha256={name: digest(ROOT/name) for name in sources},
            packages={name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib", "mujoco")},
            warm_start={"path": str(checkpoint.relative_to(ROOT)), "sha256": PARENT_SHA,
                        "optimizer_loaded": False, "initialization_only": True})
        for name, sha in record["source_sha256"].items():
            dest = out/"source"/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)
            if digest(dest) != sha:
                raise ValueError("source capture changed")
        gs.init(backend=gs.metal, logging_level="warning", seed=a.seed)
        env = MicroduckUnbracedWalkingEnv(a.num_envs, model_directory=ROOT/"experiments/walking/models/contact-v11")
        if env.num_obs != 61 or env.num_actions != 14:
            raise ValueError("walking actor contract drift")
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(out), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True, "optimizer": False, "iteration": False})
        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned unbraced walking run interrupted: {signum}")
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        if (torch.count_nonzero(env.head_cmd).item() or torch.count_nonzero(env.body_cmd).item()
                or not torch.isfinite(env.rew_buf).all().item()
                or not torch.isfinite(env.walking_internal_n).all().item()):
            raise ValueError("nonzero pose command or nonfinite final training telemetry")
        final = out/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final),
                      final_zero_pose_commands_verified=True, final_finite_reward_and_internal_load_verified=True)
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if runner is not None:
            record["new_transitions"] = runner.logger.tot_timesteps
        record["partial_iteration_transitions"] = "unknown" if record["status"] != "completed" else 0
        record["elapsed_s"] = time.monotonic()-started
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({key: record[key] for key in ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
