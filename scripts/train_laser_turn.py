"""Bounded turn-correction PPO, preserving all prior source/weight receipts."""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.train_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=250)
    p.add_argument("--seed", type=int, default=26090502)
    args = p.parse_args()
    if not args.run_id.replace("-", "").isalnum() or not 1 <= args.num_envs <= 1024 or not 1 <= args.iterations <= 1000:
        p.error("unique simple run id, 1..1024 envs, and 1..1000 iterations required")
    output = ROOT/"logs"/args.run_id
    output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    from rsl_rl.runners import OnPolicyRunner
    from microduck.velocity_cfg import TRAIN_CFG
    from microduck.laser_turn_env import MicroduckLaserTurnEnv, TURN_CONFIG
    checkpoint = ROOT/"receipts/laser-dynamic/20260905-robust-dev/source-checkpoint.pt"
    expected = "3ff9bddbf123e4abd62e486fe5fb308cfd159c0924093b12f2f49669cb05b35a"
    if checkpoint.is_symlink() or digest(checkpoint) != expected:
        raise ValueError("first-party warm-start digest mismatch")
    cfg = copy.deepcopy(TRAIN_CFG)
    cfg.update(seed=args.seed, run_name=args.run_id)
    sources = ["scripts/train_laser_turn.py", "microduck/laser_turn_env.py", "scripts/train_laser_robust.py", "microduck/laser_robust_env.py", "scripts/train_laser.py",
               "microduck/laser_env.py", "microduck/laser_task.py", "microduck/velocity_env.py", "microduck/velocity_cfg.py", "microduck/bam_actuator.py"]
    record = {"schema": "microduck.laser-training/v1", "variant": "turn-v2", "proof_class": "first_party_development",
              "held_out": False, "target_source": "simulated-ground-truth", "args": vars(args),
              "train_cfg": cfg, "robustness": TURN_CONFIG, "new_transitions": args.num_envs*24*args.iterations,
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_sha256": {s: digest(ROOT/s) for s in sources},
              "packages": {n: importlib.metadata.version(n) for n in ("genesis-world", "torch", "rsl-rl-lib")},
              "warm_start": {"path": str(checkpoint.relative_to(ROOT)), "sha256": expected, "prior_transitions": 24576000},
              "status": "starting"}
    started = time.monotonic()
    try:
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        gs.init(backend=gs.metal, logging_level="warning", seed=args.seed)
        env = MicroduckLaserTurnEnv(args.num_envs)
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
        runner.load(str(checkpoint))
        runner.current_learning_iteration = 0
        record["status"] = "running"
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=False)
        final = output/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        record["elapsed_s"] = time.monotonic()-started
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_s", "checkpoint", "new_transitions")}))


if __name__ == "__main__":
    main()
