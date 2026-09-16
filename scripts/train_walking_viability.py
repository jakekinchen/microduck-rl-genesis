"""Bounded v9 objective-composition intervention, retained v8 final only."""
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
from scripts.evaluate_walking_heading import verify_input_manifest
V8_FINAL_CHECKPOINT_SHA256 = "348030128f56145a5172fe8ad8469394cb5afab3fd5a6911ac124373493e818f"


def verified_initializer(root):
    receipt = root / "receipts/walking/20260905-v8-training-complete"
    prior = json.loads((receipt / "training.json").read_text())
    if (prior["status"] != "completed" or prior["variant"] != "walking-v8"
            or prior["checkpoint"] != "model_999.pt" or prior["new_transitions"] != 24_576_000):
        raise ValueError("full completed v8 final required, not an intermediate or smoke")
    checkpoint = receipt / prior["checkpoint"]
    if (prior["checkpoint_sha256"] != V8_FINAL_CHECKPOINT_SHA256
            or checkpoint.is_symlink() or digest(checkpoint) != V8_FINAL_CHECKPOINT_SHA256):
        raise ValueError("retained v8 final identity mismatch")
    for name, sha in prior["source_sha256"].items():
        if digest(receipt / "source" / name) != sha or digest(root / name) != sha:
            raise ValueError(f"parent training source changed: {name}")
    scores, evaluations = [], {}
    for suffix in ("old-regression", "final", "current-sensor"):
        folder = root / "receipts/walking" / f"20260905-v8-{suffix}"
        verify_input_manifest(folder)
        training = json.loads((folder / "training.json").read_text())
        evaluation = json.loads((folder / "evaluation.json").read_text())
        heading_path = folder.with_name(folder.name + "-heading") / "evaluation.json"
        heading = json.loads(heading_path.read_text())
        if (training["checkpoint_sha256"] != V8_FINAL_CHECKPOINT_SHA256
                or heading["checkpoint_sha256"] != V8_FINAL_CHECKPOINT_SHA256):
            raise ValueError("evaluation is not the declared v8 final")
        if (evaluation["total_cases"] != 21 or len(evaluation["case_reports"]) != 21
                or heading["total_cases"] != 21 or len(heading["case_reports"]) != 21):
            raise ValueError("all complete exposed evaluation and heading cases required")
        if (evaluation["policy_sha256"] != digest(folder / "policy.onnx")
                or heading["policy_sha256"] != evaluation["policy_sha256"]
                or heading["input_sha256"]["evaluation.json"] != digest(folder / "evaluation.json")
                or heading["input_sha256"]["trajectory.jsonl"] != digest(folder / "trajectory.jsonl")):
            raise ValueError("final evaluation/heading identity mismatch")
        scores.append(heading["combined_passed_cases"])
        for path in (folder / "evaluation.json", heading_path):
            evaluations[str(path.relative_to(root))] = digest(path)
    if all(score == 21 for score in scores):
        raise ValueError("all combined protocols pass; correction is not needed")
    return checkpoint, prior, evaluations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--iterations", type=int, default=750)
    parser.add_argument("--seed", type=int, default=26090519)
    args = parser.parse_args()
    if (not args.run_id.replace("-", "").isalnum() or not 1 <= args.num_envs <= 1024
            or not 1 <= args.iterations <= 750):
        parser.error("new simple run ID; at most 1024 environments and 750 iterations")
    checkpoint, prior, evaluations = verified_initializer(ROOT)
    output = ROOT / "logs" / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v9",
              "proof_class": "first_party_development", "held_out": False,
              "target_source": "velocity-command", "args": vars(args), "status": "starting",
              "planned_new_transitions": args.num_envs * args.iterations * 24,
              "new_transitions": 0, "pid": __import__("os").getpid()}
    started, runner = time.monotonic(), None
    try:
        (output / "run.json").write_text(json.dumps(record, indent=2) + "\n")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_viability_env import MicroduckViableWalkingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=args.seed, run_name=args.run_id)
        cfg["algorithm"]["learning_rate"] = 5e-4
        sources = list(prior["source_sha256"]) + [
            "scripts/train_walking_viability.py", "microduck/walking_yaw_bias_env.py",
            "microduck/walking_viability_env.py", "experiments/walking/VIABILITY-v9.md",
            "tests/test_walking_viability.py", "scripts/audit_walking_viability_reward.py"]
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
        env = MicroduckViableWalkingEnv(args.num_envs)
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True,
                                            "optimizer": False, "iteration": False})

        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned walking-v9 run interrupted: {signum}")

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
