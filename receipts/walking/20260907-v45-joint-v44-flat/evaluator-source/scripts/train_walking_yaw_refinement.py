"""V21 bounded reward-only refinement from source-bound V18 FINAL."""
import argparse
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
PARENT_SHA = "922bd58e2ad2d6657dc7797f28b638f8294ab57ab9963c458569130b4d13e70b"


def timing_snapshot(env):
    import torch
    names = ["motor", "base_ang_vel", "projected_gravity", "joint_vel"]
    buffers = [env.bam._delay] + [env.obs_delays[key] for key in names[1:]]
    values = torch.stack([buf._lag for buf in buffers], dim=1).cpu()
    if not ((values[:,0] >= 0).all() and (values[:,0] <= 6).all()
            and (values[:,1:] >= 0).all() and (values[:,1:] <= 1).all()
            and all(buf.update_period == 0 for buf in buffers)):
        raise ValueError("effective persistent timing bounds changed")
    unique, counts = torch.unique(values, dim=0, return_counts=True)
    return {"columns": names, "per_environment_lags": values.tolist(),
            "joint_bucket_counts": [{"lags": row.tolist(), "environments": int(count)}
                                    for row, count in zip(unique, counts)],
            "boundary": "Applied lag snapshot, not cumulative episode or non-timing physics coverage."}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=250)
    p.add_argument("--seed", type=int, default=26090621)
    a = p.parse_args()
    if (not a.run_id.replace("-", "").isalnum()
            or (a.num_envs, a.iterations) not in ((64, 5), (1024, 250)) or a.seed != 26090621):
        p.error("new simple ID; frozen 64x5 smoke or 1024x250 full run; seed26090621")
    parent = ROOT / "logs/walking-20260906-v18"
    prior = json.loads((parent / "run.json").read_text())
    checkpoint = parent / "model_249.pt"
    if prior["status"] != "completed" or prior["checkpoint_sha256"] != PARENT_SHA or digest(checkpoint) != PARENT_SHA:
        raise ValueError("exact V18 FINAL required")
    for name, sha in prior["source_sha256"].items():
        if digest(ROOT/name) != sha or digest(parent/"source"/name) != sha:
            raise ValueError("parent source drift")
    diagnostic = ROOT / "receipts/walking/20260906-v20-paired-genesis-r2"
    for line in (diagnostic / "SHA256SUMS").read_text().splitlines():
        sha, name = line.split("  ", 1)
        path = (diagnostic / name).resolve()
        if not path.is_relative_to(diagnostic.resolve()) or digest(path) != sha:
            raise ValueError("diagnostic manifest mismatch")
    evidence = json.loads((diagnostic / "probe.json").read_text())
    if (evidence["status"] != "completed" or len(evidence["cases"]) != 3
            or not all(c["complete"] and c["all_actor_observations_and_motor_targets_verified"] for c in evidence["cases"])
            or not all(c["response"]["mean_abs_yaw_error_rad_s"] > .20 for c in evidence["cases"][:2])):
        raise ValueError("verified shared yaw-failure diagnosis required")
    from scripts.evaluate_walking_yaw_refinement import FREEZE, SOURCES
    frozen = json.loads(FREEZE.read_text())
    for name, sha in frozen["source_sha256"].items():
        if digest(ROOT / name) != sha:
            raise ValueError(f"frozen source drift: {name}")
    out = ROOT / "logs" / a.run_id
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v21",
        "proof_class": "first_party_development", "held_out": False, "target_source": "velocity-command",
        "args": vars(a), "status": "starting", "planned_new_transitions": a.num_envs*a.iterations*24,
        "new_transitions": 0, "pid": os.getpid(),
        "genesis_diagnostic_manifest_sha256": digest(diagnostic / "SHA256SUMS")}
    started, runner = time.monotonic(), None
    try:
        (out / "run.json").write_text(json.dumps(record, indent=2)+"\n")
        import torch
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_yaw_refinement_env import MicroduckYawRefinementEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        cfg["algorithm"]["learning_rate"] = 2e-4
        sources = list(dict.fromkeys(list(prior["source_sha256"]) + SOURCES + [str(FREEZE.relative_to(ROOT))]))
        record.update(train_cfg=cfg,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            source_sha256={name: digest(ROOT/name) for name in sources},
            packages={name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib", "mujoco")},
            warm_start={"path": str(checkpoint.relative_to(ROOT)), "sha256": PARENT_SHA,
                        "optimizer_loaded": False, "initialization_only": True})
        for name, sha in record["source_sha256"].items():
            dest = out / "source" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, dest)
            if digest(dest) != sha:
                raise ValueError("source capture changed")
        gs.init(backend=gs.metal, logging_level="warning", seed=a.seed)
        env = MicroduckYawRefinementEnv(a.num_envs, model_directory=ROOT/"experiments/walking/models/contact-v11")
        if env.num_obs != 61 or env.num_actions != 14:
            raise ValueError("actor contract changed")
        record.update(env_cfg=env.cfg, initial_effective_timing=timing_snapshot(env))
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(out), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True, "optimizer": False, "iteration": False})

        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned V21 training interrupted: {signum}")

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (out / "run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        if (torch.count_nonzero(env.head_cmd).item() or torch.count_nonzero(env.body_cmd).item()
                or not all(torch.isfinite(value).all().item() for value in
                           (env.rew_buf, env.walking_internal_n, env.actions, env.get_observations()["policy"]))):
            raise ValueError("nonzero pose command or nonfinite final training telemetry")
        final = out / f"model_{runner.current_learning_iteration}.pt"
        parameters = torch.load(final, map_location="cpu", weights_only=True)["actor_state_dict"]
        if not all(torch.isfinite(tensor).all().item() for tensor in parameters.values()):
            raise ValueError("nonfinite final actor parameters")
        for name, sha in record["source_sha256"].items():
            if digest(ROOT/name) != sha:
                raise ValueError(f"source changed during training: {name}")
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final),
            final_zero_pose_commands_verified=True, final_finite_telemetry_and_actor_verified=True,
            final_effective_timing=timing_snapshot(env))
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if runner is not None:
            record["new_transitions"] = runner.logger.tot_timesteps
        record["partial_iteration_transitions"] = "unknown" if record["status"] != "completed" else 0
        record["elapsed_s"] = time.monotonic()-started
        (out / "run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({key: record[key] for key in ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
