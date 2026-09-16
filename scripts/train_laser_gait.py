"""One bounded, source-bound local gait correction; no auto continuation."""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time
import signal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.train_laser import digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--num-envs", type=int, default=1024)
    p.add_argument("--iterations", type=int, default=600)
    p.add_argument("--seed", type=int, default=26090504)
    a = p.parse_args()
    if not a.run_id.replace("-", "").isalnum() or not 1<=a.num_envs<=1024 or not 1<=a.iterations<=600:
        p.error("simple new id, <=1024 environments and <=600 iterations required")
    output = ROOT/"logs"/a.run_id
    output.mkdir(parents=True, exist_ok=False)
    checkpoint = ROOT/"receipts/first-party-development/20260904-walking-seed-26090401-v1/training/source-checkpoint.pt"
    expected = "30648b221c189fd2ddd3f81cd0217eb648a372057319497d8c50e2378766dd07"
    record = {"schema":"microduck.laser-training/v1", "variant":"gait-v4", "proof_class":"first_party_development",
              "held_out":False, "target_source":"simulated-ground-truth", "args":vars(a),
              "status":"starting", "new_transitions":a.num_envs*a.iterations*24}
    started = time.monotonic()
    try:
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        if checkpoint.is_symlink() or digest(checkpoint)!=expected: raise ValueError("baseline identity mismatch")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.laser_gait_env import MicroduckLaserGaitEnv, GAIT_CONFIG
        cfg = copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed, run_name=a.run_id)
        sources = ["scripts/train_laser_gait.py", "microduck/laser_gait_env.py", "microduck/laser_face_command.py",
                   "microduck/laser_robust_env.py", "microduck/laser_env.py", "microduck/laser_task.py",
                   "microduck/velocity_env.py", "microduck/velocity_cfg.py", "microduck/bam_actuator.py",
                   "experiments/laser/gait-correction-v4.json"]
        record.update(train_cfg=cfg, gait=GAIT_CONFIG,
                      source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                      source_sha256={s:digest(ROOT/s) for s in sources},
                      packages={n:importlib.metadata.version(n) for n in ("genesis-world","torch","rsl-rl-lib")},
                      warm_start={"path":str(checkpoint.relative_to(ROOT)),"sha256":expected,"prior_transitions":2457600})
        gs.init(backend=gs.metal, logging_level="warning", seed=a.seed)
        env = MicroduckLaserGaitEnv(a.num_envs)
        record["env_cfg"] = env.cfg
        runner = OnPolicyRunner(env, copy.deepcopy(cfg), str(output), device="mps")
        runner.load(str(checkpoint))
        runner.current_learning_iteration = 0
        # Genesis may install handlers that do not stop a redirected process.
        # Restore an explicit stop path after construction so finally retains
        # the terminal result for this owned, bounded training process.
        def stop_training(signum, frame):
            raise KeyboardInterrupt(f"training interrupted by signal {signum}")
        signal.signal(signal.SIGINT,stop_training)
        signal.signal(signal.SIGTERM,stop_training)
        record["status"] = "running"
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations, init_at_random_ep_len=False)
        final = output/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed", checkpoint=final.name, checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        record["elapsed_s"] = time.monotonic()-started
        (output/"run.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({k:record[k] for k in ("status","elapsed_s","new_transitions","checkpoint")}))


if __name__ == "__main__": main()
