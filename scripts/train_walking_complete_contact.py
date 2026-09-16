"""Bounded complete-contact v11, retained v9 FINAL initializer only."""
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
PARENT_SHA = "c79e02bc00dabca146b83592582926fc2053114cc5e44cdf822f95aa8ff8fb17"


def initializer(root):
    folder = root/"receipts/walking/20260905-v9-training-complete"
    prior = json.loads((folder/"training.json").read_text())
    checkpoint = folder/"model_749.pt"
    if (prior["status"] != "completed" or prior["variant"] != "walking-v9"
            or prior["new_transitions"] != 18_432_000 or prior["checkpoint"] != checkpoint.name
            or prior["checkpoint_sha256"] != PARENT_SHA or checkpoint.is_symlink()
            or digest(checkpoint) != PARENT_SHA):
        raise ValueError("exact completed v9 final required")
    for name, sha in prior["source_sha256"].items():
        if digest(root/name) != sha or digest(folder/"source"/name) != sha:
            raise ValueError(f"parent training source changed: {name}")
    baseline = root/"receipts/walking/20260905-v11-native-baseline"
    verify_input_manifest(baseline)
    evaluation = json.loads((baseline/"evaluation.json").read_text())
    if (evaluation["acceptance_variant"] != "complete-contact-heading-self-v11"
            or evaluation["total_cases"] != 21 or len(evaluation["case_reports"]) != 21
            or json.loads((baseline/"training.json").read_text())["checkpoint_sha256"] != PARENT_SHA):
        raise ValueError("complete v9-on-v11 baseline required")
    if evaluation["passed_cases"] == 21:
        raise ValueError("full baseline passes; collision relearning is not needed")
    return checkpoint, prior, digest(baseline/"SHA256SUMS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=750)
    p.add_argument("--seed", type=int, default=26090521)
    a = p.parse_args()
    if (not a.run_id.replace("-", "").isalnum() or not 1 <= a.num_envs <= 1024
            or not 1 <= a.iterations <= 750 or a.seed != 26090521):
        p.error("simple new run ID, at most 1024x750, frozen seed 26090521")
    checkpoint, prior, baseline_sha = initializer(ROOT)
    from scripts.evaluate_walking_complete_contact import FREEZE, SOURCES
    for name, sha in json.loads(FREEZE.read_text())["source_sha256"].items():
        if digest(ROOT/name) != sha:
            raise ValueError(f"frozen evaluator drift: {name}")
    out = ROOT/"logs"/a.run_id
    out.mkdir(parents=True, exist_ok=False)
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v11",
              "proof_class": "first_party_development", "held_out": False,
              "target_source": "velocity-command", "args": vars(a), "status": "starting",
              "planned_new_transitions": a.num_envs*a.iterations*24, "new_transitions": 0,
              "pid": __import__("os").getpid(), "complete_model_baseline_manifest_sha256": baseline_sha}
    started, runner = time.monotonic(), None
    try:
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_collision_env import MicroduckCompleteContactWalkingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        cfg["algorithm"]["learning_rate"] = 5e-4
        sources = list(dict.fromkeys(list(prior["source_sha256"])+SOURCES+[
            "scripts/train_walking_complete_contact.py", "microduck/walking_collision_env.py",
            "experiments/walking/evaluator-freeze-collision-v11.json"]))
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
        env = MicroduckCompleteContactWalkingEnv(a.num_envs,
                      model_directory=ROOT/"experiments/walking/models/contact-v11")
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(out), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True, "optimizer": False, "iteration": False})
        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned v11 run interrupted: {signum}")
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (out/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        final = out/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      failure=f"{type(exc).__name__}: {exc}")
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
