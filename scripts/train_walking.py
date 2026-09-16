"""Bounded local walking foundation; source-bound and no automatic continuation."""
import argparse
import copy
import importlib.metadata
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--num-envs",type=int,default=1024)
    p.add_argument("--iterations",type=int,default=1000)
    p.add_argument("--seed",type=int,default=26090511)
    a=p.parse_args()
    if not a.run_id.replace("-","").isalnum() or not 1<=a.num_envs<=1024 or not 1<=a.iterations<=1000:
        p.error("new simple run id; at most 1024 environments and 1000 iterations")
    output=ROOT/"logs"/a.run_id
    output.mkdir(parents=True,exist_ok=False)
    checkpoint=ROOT/"receipts/laser-gait/20260905-v4-evaluation/source-checkpoint.pt"
    expected="aa6cb4c3b1dcca6c3d4f60dc0e8de0095f10607776879fd70033f986526e5bb0"
    record={"schema":"microduck.walking-training/v1","variant":"walking-v1",
            "proof_class":"first_party_development","held_out":False,"target_source":"velocity-command",
            "args":vars(a),"status":"starting","new_transitions":a.num_envs*a.iterations*24}
    start=time.monotonic()
    try:
        (output/"run.json").write_text(json.dumps(record,indent=2)+"\n")
        if checkpoint.is_symlink() or digest(checkpoint)!=expected:raise ValueError("warm-start identity mismatch")
        import genesis as gs
        from rsl_rl.runners import OnPolicyRunner
        from microduck.velocity_cfg import TRAIN_CFG
        from microduck.walking_env import MicroduckWalkingEnv
        cfg=copy.deepcopy(TRAIN_CFG)
        cfg.update(seed=a.seed,run_name=a.run_id)
        cfg["algorithm"]["learning_rate"]=5e-4
        sources=["scripts/train_walking.py","microduck/walking_env.py","microduck/velocity_env.py",
                 "microduck/velocity_cfg.py","microduck/bam_actuator.py","microduck/constants.py",
                 "microduck/terrain.py","microduck/laser_gait_env.py","microduck/laser_robust_env.py",
                 "microduck/laser_env.py","microduck/laser_task.py","experiments/walking/PLAN.md"]
        record.update(train_cfg=cfg,source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                      source_sha256={s:digest(ROOT/s) for s in sources},
                      packages={n:importlib.metadata.version(n) for n in ("genesis-world","torch","rsl-rl-lib","mujoco")},
                      warm_start={"path":str(checkpoint.relative_to(ROOT)),"sha256":expected,"optimizer_loaded":False})
        gs.init(backend=gs.metal,logging_level="warning",seed=a.seed)
        env=MicroduckWalkingEnv(a.num_envs)
        record["env_cfg"]=env.cfg
        runner=OnPolicyRunner(env,copy.deepcopy(cfg),str(output),device="mps")
        runner.load(str(checkpoint),load_cfg={"actor":True,"critic":True,"optimizer":False,"iteration":False})
        def stop(signum,frame):raise KeyboardInterrupt(f"owned walking run interrupted: {signum}")
        signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
        record["status"]="running"
        (output/"run.json").write_text(json.dumps(record,indent=2)+"\n")
        runner.learn(num_learning_iterations=a.iterations,init_at_random_ep_len=False)
        final=output/f"model_{runner.current_learning_iteration}.pt"
        record.update(status="completed",checkpoint=final.name,checkpoint_sha256=digest(final))
    except BaseException as exc:
        record.update(status="failed",failure=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        record["elapsed_s"]=time.monotonic()-start
        (output/"run.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({k:record[k] for k in ("status","elapsed_s","new_transitions","checkpoint")}),flush=True)


if __name__=="__main__":main()
