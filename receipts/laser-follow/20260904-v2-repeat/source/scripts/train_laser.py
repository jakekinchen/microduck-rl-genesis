"""Bounded, local-only first-party laser-goal PPO experiment.

Run from repo root: .venv-apple/bin/python scripts/train_laser.py --help
No cloud resources, activation, hidden acceptance cases, or third-party weights.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=400)
    p.add_argument("--seed", type=int, default=26090402)
    p.add_argument("--warm-start-own-baseline", action="store_true")
    args = p.parse_args()
    if not args.run_id.replace("-", "").replace("_", "").isalnum():
        p.error("run-id must be a simple identifier")
    if not 1 <= args.iterations <= 2000 or not 1 <= args.num_envs <= 1024:
        p.error("local bounds: 1..2000 iterations and 1..1024 environments")
    output = ROOT / "logs" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    from rsl_rl.runners import OnPolicyRunner
    from microduck import velocity_cfg as C
    from microduck.laser_env import MicroduckLaserEnv
    if not torch.backends.mps.is_available():
        raise RuntimeError("This explicitly local Apple experiment requires MPS")
    gs.init(backend=gs.metal, logging_level="warning", seed=args.seed)
    cfg = copy.deepcopy(C.TRAIN_CFG)
    cfg.update(seed=args.seed, run_name=args.run_id)
    sources = ["scripts/train_laser.py", "microduck/laser_env.py", "microduck/laser_task.py",
               "microduck/velocity_env.py", "microduck/velocity_cfg.py", "microduck/bam_actuator.py"]
    record = {"schema": "microduck.laser-training/v1", "proof_class": "first_party_development",
              "target_source": "simulated-ground-truth", "held_out": False,
              "args": vars(args), "train_cfg": cfg,
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_sha256": {name: digest(ROOT/name) for name in sources},
              "packages": {name: importlib.metadata.version(name) for name in ("genesis-world", "torch", "rsl-rl-lib")},
              "status": "starting", "new_transitions": args.num_envs*args.iterations*24}
    (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    started = time.monotonic()
    env = MicroduckLaserEnv(args.num_envs)
    record["env_cfg"] = env.cfg
    # rsl-rl consumes config keys in-place while constructing the models.
    # Keep the receipt's complete, replayable configuration untouched.
    runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
    if args.warm_start_own_baseline:
        checkpoint = ROOT/"receipts/first-party-development/20260904-walking-seed-26090401-v1/training/source-checkpoint.pt"
        expected = "30648b221c189fd2ddd3f81cd0217eb648a372057319497d8c50e2378766dd07"
        if digest(checkpoint) != expected or checkpoint.is_symlink():
            raise RuntimeError("first-party baseline digest/path changed")
        runner.load(str(checkpoint))
        # New task curriculum starts at zero; retain policy/normalizer but label
        # previous 100 iterations separately from this target-training budget.
        runner.current_learning_iteration = 0
        record["warm_start"] = {"path": str(checkpoint.relative_to(ROOT)), "sha256": expected,
                                "prior_transitions": 2457600}
    (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    try:
        runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=False)
        checkpoint = output/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", elapsed_s=time.monotonic()-started,
                      checkpoint=checkpoint.name, checkpoint_sha256=digest(checkpoint))
    except BaseException as exc:
        record.update(status="failed", elapsed_s=time.monotonic()-started,
                      failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
