"""Replay captured float32 actions in Genesis; no policy/command intervention.

This is a simulator-isolation diagnostic, not task evaluation: once states
diverge, these fixed actions are no longer feedback from the current robot.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-audit",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--seconds",type=float,default=8)
    a=p.parse_args()
    if not 1<=a.seconds<=16:raise ValueError("bounded diagnostic required")
    import genesis as gs
    import torch
    import numpy as np
    from microduck.laser_env import MicroduckLaserEnv
    actions=np.load(a.source_audit/"original-actions-float32.npy",allow_pickle=False)
    if actions.dtype!=np.float32 or actions.ndim!=2 or actions.shape[1]!=14 or not np.isfinite(actions).all():
        raise ValueError("exact float32 action capture required")
    a.output.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu,logging_level="warning",seed=76350)
    env=MicroduckLaserEnv(1,demo=True)
    env.reset();env.place([0,0,.125],yaw=0)
    lower,upper=env.robot.get_dofs_limit(env.motors_dof_idx)
    lower,upper=lower.cpu().numpy().reshape(-1)[:14],upper.cpu().numpy().reshape(-1)[:14]
    rows=[];applied=[]
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for i,action in enumerate(actions[:round(a.seconds*50)]):
            tensor=torch.from_numpy(action[None].copy()).to(env.device)
            _,_,done,_=env.step(tensor)
            actual=env.actions[0].cpu().numpy()
            if actual.tobytes()!=action.tobytes():raise ValueError("action bytes changed")
            applied.append(actual.copy())
            q=env.dof_pos[0].cpu().numpy()
            margin=np.minimum(q-lower,upper-q)/(upper-lower)
            row={"time_s":(i+1)*.02,"robot_xyz_m":env.base_pos[0].cpu().tolist(),
                 "joint_position_rad":q.tolist(),"joint_limit_margin_fraction":margin.tolist(),
                 "foot_site_height_m":env.foot_height[0].cpu().tolist(),
                 "foot_contact_force_n":env.foot_contact_force[0].cpu().tolist(),
                 "action_rad":actual.tolist(),"invalid_reset":bool(done.any())}
            rows.append(row);stream.write(json.dumps(row)+"\n")
            if bool(done.any()):break
    np.save(a.output/"applied-actions-float32.npy",np.array(applied,np.float32))
    completed=len(applied)
    parked=np.array([r["joint_limit_margin_fraction"] for r in rows if r["time_s"]>=1])<.05
    result={"schema":"microduck.genesis-fixed-gait-replay/v1","engine":"Genesis CPU",
            "source_action_file_sha256":digest(a.source_audit/"original-actions-float32.npy"),
            "captured_dtype":"float32", "matched_action_steps":completed,
            "original_tensor_bytes_equal_on_replayed_prefix":np.array(applied,np.float32).tobytes()==actions[:completed].tobytes(),
            "joint_stop_fraction_after_1s":parked.mean(axis=0).tolist(),
            "last_root_xyz_m":rows[-1]["robot_xyz_m"],
            "boundary":"Fixed-action cross-engine diagnostic, not a current feedback policy or gait/transfer acceptance."}
    (a.output/"replay.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(Path(__file__),a.output/"replay-source.py")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"))
    print(json.dumps(result),flush=True)


if __name__=="__main__":main()
