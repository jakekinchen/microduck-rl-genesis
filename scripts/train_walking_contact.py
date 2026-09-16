"""Bounded v6 contact-default correction; every v5 reward is unchanged."""
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=1500)
    p.add_argument("--seed", type=int, default=26090516)
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or not 1 <= a.num_envs <= 1024 or not 1 <= a.iterations <= 1500:
        p.error("new simple run ID; at most 1024 environments and 1500 iterations")
    output = ROOT/"logs"/a.run_id
    output.mkdir(parents=True, exist_ok=False)
    checkpoint = ROOT/"receipts/walking/20260905-v5-training-complete/model_749.pt"
    expected = "19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1"
    record = {"schema": "microduck.walking-training/v1", "variant": "walking-v6",
        "proof_class": "first_party_development", "held_out": False, "target_source": "velocity-command",
        "args": vars(a), "status": "starting", "planned_new_transitions": a.num_envs*a.iterations*24,
        "new_transitions": 0, "pid": __import__("os").getpid()}
    start = time.monotonic()
    runner = None
    try:
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        if checkpoint.is_symlink() or digest(checkpoint) != expected:
            raise ValueError("warm-start identity mismatch")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_contact_env import MicroduckContactTrackingWalkingEnv
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        cfg["algorithm"]["learning_rate"] = 5e-4
        prior = json.loads((checkpoint.parent/"training.json").read_text())
        sources = list(prior["source_sha256"])+["scripts/train_walking_contact.py",
            "microduck/walking_contact_env.py", "experiments/walking/CONTACT-v6.md"]
        record.update(train_cfg=cfg,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            source_sha256={s: digest(ROOT/s) for s in sources},
            packages={n: importlib.metadata.version(n) for n in ("genesis-world", "torch", "rsl-rl-lib", "mujoco")},
            warm_start={"path": str(checkpoint.relative_to(ROOT)), "sha256": expected,
                        "optimizer_loaded": False, "initialization_only": True})
        for name, sha in record["source_sha256"].items():
            destination = output/"source"/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, destination)
            if digest(destination) != sha:
                raise ValueError("source capture changed")
        gs.init(backend=gs.metal, logging_level="warning", seed=a.seed)
        env = MicroduckContactTrackingWalkingEnv(a.num_envs)
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
        runner.load(str(checkpoint), load_cfg={"actor": True, "critic": True, "optimizer": False, "iteration": False})
        def stop(signum, frame):
            raise KeyboardInterrupt(f"owned walking-v6 run interrupted: {signum}")
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        record["status"] = "running"
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        final = output/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if runner is not None:
            record["new_transitions"] = runner.logger.tot_timesteps
        record["partial_iteration_transitions"] = "unknown" if record["status"] != "completed" else 0
        record["elapsed_s"] = time.monotonic()-start
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_s", "new_transitions", "checkpoint")}), flush=True)


if __name__ == "__main__":
    main()
