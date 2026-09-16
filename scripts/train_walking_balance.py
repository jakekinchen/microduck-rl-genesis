"""Conditional v8 trunk-balance correction from retained v6 final only."""
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
V6_FINAL_CHECKPOINT_SHA256 = "0f0cad5839cf22c492e69dfd1d1e41c26ce430a0363018bf5fa13faf6333afba"


def verified_initializer(root):
    receipt = root / "receipts/walking/20260905-v6-training-complete"
    prior = json.loads((receipt / "training.json").read_text())
    if (prior["status"] != "completed" or prior["variant"] != "walking-v6"
            or prior["checkpoint"] != "model_1499.pt"
            or prior["new_transitions"] != 36_864_000):
        raise ValueError("full completed v6 final required, not an intermediate or smoke")
    checkpoint = receipt / prior["checkpoint"]
    if (prior["checkpoint_sha256"] != V6_FINAL_CHECKPOINT_SHA256
            or checkpoint.is_symlink() or digest(checkpoint) != prior["checkpoint_sha256"]):
        raise ValueError("retained v6 final identity mismatch")
    for name, sha in prior["source_sha256"].items():
        if digest(receipt / "source" / name) != sha or digest(root / name) != sha:
            raise ValueError(f"parent training source changed: {name}")
    scores = []
    evaluations = {}
    for name in ("20260905-v6-old-regression", "20260905-v6-final", "20260905-v6-current-sensor"):
        folder = root / "receipts/walking" / name
        training = json.loads((folder / "training.json").read_text())
        evaluation = json.loads((folder / "evaluation.json").read_text())
        if training["checkpoint_sha256"] != prior["checkpoint_sha256"]:
            raise ValueError("evaluation is not the same v6 final")
        if evaluation["total_cases"] != 21 or len(evaluation["case_reports"]) != 21:
            raise ValueError("all three complete exposed evaluations required")
        if evaluation["policy_sha256"] != digest(folder / "policy.onnx"):
            raise ValueError("evaluated ONNX identity mismatch")
        scores.append(evaluation["passed_cases"])
        evaluations[str((folder / "evaluation.json").relative_to(root))] = digest(folder / "evaluation.json")
    if all(score == 21 for score in scores):
        raise ValueError("v6 passes all visible protocols; conditional correction is not needed")
    return checkpoint, prior, evaluations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=26090518)
    args = parser.parse_args()
    if (not args.run_id.replace("-", "").isalnum() or not 1 <= args.num_envs <= 1024
            or not 1 <= args.iterations <= 1000):
        parser.error("new simple run ID; at most 1024 environments and 1000 iterations")
    checkpoint, prior, evaluations = verified_initializer(ROOT)
    output = ROOT / "logs" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v8",
              "proof_class": "first_party_development", "held_out": False,
              "target_source": "velocity-command", "args": vars(args), "status": "starting",
              "planned_new_transitions": args.num_envs * args.iterations * 24,
              "new_transitions": 0, "pid": __import__("os").getpid()}
    started = time.monotonic()
    runner = None
    try:
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_balance_env import MicroduckBalancedWalkingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=args.seed, run_name=args.run_id)
        cfg["algorithm"]["learning_rate"] = 5e-4
        sources = list(prior["source_sha256"]) + [
            "scripts/train_walking_balance.py", "microduck/walking_balance_env.py",
            "experiments/walking/BALANCE-v8.md", "tests/test_walking_balance.py"]
        record.update(train_cfg=cfg,
                      source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      source_sha256={name: digest(ROOT / name) for name in sources},
                      packages={name: importlib.metadata.version(name) for name in
                                ("genesis-world", "torch", "rsl-rl-lib", "mujoco")},
                      initialization_evaluations_sha256=evaluations,
                      warm_start={"path": str(checkpoint.relative_to(ROOT)),
                                  "sha256": prior["checkpoint_sha256"], "optimizer_loaded": False,
                                  "initialization_only": True})
        for name, sha in record["source_sha256"].items():
            destination = output / "source" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
            if digest(destination) != sha:
                raise ValueError("source capture changed")
        gs.init(backend=gs.metal, logging_level="warning", seed=args.seed)
        env = MicroduckBalancedWalkingEnv(args.num_envs)
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True,
                                            "optimizer": False, "iteration": False})

        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned walking-v8 run interrupted: {signum}")

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=False)
        final = output / f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if runner is not None:
            record["new_transitions"] = runner.logger.tot_timesteps
        record["partial_iteration_transitions"] = "unknown" if record["status"] != "completed" else 0
        record["elapsed_s"] = time.monotonic() - started
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in
                     ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
