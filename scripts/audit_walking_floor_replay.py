"""Paired fixed-action Genesis replay: old versus native-aligned floor only."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    import torch
    import genesis as gs
    from microduck.walking_posture_env import MicroduckPostureWalkingEnv
    from microduck.walking_ground_env import MicroduckGroundAlignedWalkingEnv
    from microduck.bam_actuator import DelayBuffer
    from scripts.evaluate_laser import digest
    source=ROOT/"receipts/walking/20260905-v2-probe250/m4s1-forward-12.jsonl"
    inputs=np.asarray([json.loads(s)["action_rad"] for s in source.read_text().splitlines()][:100],np.float32)
    torch.set_num_threads(1);gs.init(backend=gs.cpu,logging_level="warning",seed=76531)
    envs=[MicroduckPostureWalkingEnv(1,demo=True),MicroduckGroundAlignedWalkingEnv(1,demo=True)]
    for env in envs:
        env.bam.vin_nominal.fill_(7.35);env.bam.vin_drop_resistance.zero_()
        env.bam._delay=DelayBuffer((1,14),4,4,0,env.device)
        env.reset();env.place([0,0,.125],yaw=.2)
    states=[[],[]];applied=[[],[]]
    for action in inputs:
        for i,env in enumerate(envs):
            env.step(torch.from_numpy(action[None].copy()).to(env.device))
            actual=env.actions[0].cpu().numpy().copy()
            if actual.tobytes()!=action.tobytes():raise ValueError("paired replay altered action bytes")
            applied[i].append(actual)
            states[i].append(np.r_[env.base_pos[0].cpu().numpy(),env.base_quat[0].cpu().numpy(),env.dof_pos[0].cpu().numpy()])
    states=np.asarray(states);applied=np.asarray(applied,np.float32)
    np.save(a.output/"inputs-float32.npy",inputs);np.save(a.output/"applied-float32.npy",applied)
    np.save(a.output/"states.npy",states)
    report={"schema":"microduck.paired-floor-replay/v1","steps":len(inputs),"source_json_sha256":digest(source),
        "paired_action_bytes_equal":applied[0].tobytes()==applied[1].tobytes()==inputs.tobytes(),
        "paired_state_bytes_equal":states[0].tobytes()==states[1].tobytes(),
        "maximum_absolute_state_difference":float(np.max(np.abs(states[0]-states[1]))),
        "old_floor_masks":[envs[0].ground.geoms[0].contype,envs[0].ground.geoms[0].conaffinity],
        "new_floor_masks":[envs[1].ground.geoms[0].contype,envs[1].ground.geoms[0].conaffinity],
        "physics_condition":{"voltage_v":7.35,"drop_ohm":0.,"motor_delay_physics_ticks":4},
        "physical_transfer_validated":False,
        "boundary":"Two-second fixed-input diagnostic, not gait acceptance. Input tensors reconstructed from retained JSON, then captured and kept byte-identical between these two simulations; not a claim about an absent original tensor file."}
    (a.output/"replay.json").write_text(json.dumps(report,indent=2)+"\n")
    for source in ("scripts/audit_walking_floor_replay.py","microduck/walking_ground_env.py",
                   "microduck/walking_posture_env.py","microduck/walking_controlled_env.py",
                   "microduck/walking_env.py","microduck/velocity_env.py","microduck/bam_actuator.py","microduck/constants.py"):
        dest=a.output/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(report),flush=True)


if __name__=="__main__":main()
