"""Intermediate Torch feedback diagnostic; never a candidate or ONNX acceptance."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--iteration",type=int,required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--video",action="store_true");a=p.parse_args()
    if not a.run_id.replace("-","").isalnum() or a.iteration<0:raise ValueError("invalid diagnostic checkpoint")
    folder=ROOT/"logs"/a.run_id;checkpoint=folder/f"model_{a.iteration}.pt"
    sha=digest(checkpoint);record=json.loads((folder/"run.json").read_text())
    for path,value in record["source_sha256"].items():
        if digest(ROOT/path)!=value:raise ValueError("training source changed")
    a.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    from experiments.walking.world import WalkingWorld
    from experiments.walking.metrics import evaluate_case
    from experiments.laser.gait import GaitProbe
    torch.set_num_threads(1)
    cfg=copy.deepcopy(record["train_cfg"]);cfg["actor"].pop("class_name")
    actor=MLPModel(TensorDict({"policy":torch.zeros(1,61)},[1]),cfg["obs_groups"],"actor",14,**cfg["actor"])
    actor.load_state_dict(torch.load(checkpoint,map_location="cpu",weights_only=True)["actor_state_dict"])
    actor.eval();policy=ExportedPolicy(actor).eval()
    class TorchPolicy:
        def infer(self,obs):
            start=time.monotonic()
            with torch.no_grad():action=policy(torch.from_numpy(obs)).numpy()
            return action,(time.monotonic()-start)*1000
    suite=json.loads((ROOT/"experiments/walking/suite-v1.json").read_text());reports=[]
    for motor,sensor in ((4,1),(0,0)):
        for case in (suite["cases"][1],suite["cases"][3]):
            name=f'm{motor}s{sensor}-{case["id"]}'
            world=WalkingWorld(ROOT/"receipts/laser-gait/20260905-v4-evaluation/policy.onnx",ROOT/".workspace/bam",motor_ticks=motor,sensor_ticks=sensor,yaw=case["yaw"],render=a.video)
            world.core.policy=TorchPolicy();probe=GaitProbe(world.core);rows=[]
            writer=imageio.get_writer(a.output/f"{name}.mp4",fps=25,codec="libx264",quality=7) if a.video else None
            try:
                for i in range(900):
                    command=case["command"] if 1<=i*.02<13 else [0,0,0]
                    row=probe.sample(world.step_command(command));rows.append(row)
                    if writer and i%2==0:writer.append_data(world.walking_frame())
                    if world.fell:break
                (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
                result=evaluate_case(rows,case,suite);result["diagnostic_case"]=name
                result["median_swing_air_s"]=float(np.median([e["air_s"] for e in result["gait"]["swing_events"]])) if result["gait"]["swing_events"] else None
                reports.append(result)
                print(json.dumps({k:v for k,v in result.items() if k!="gait"}),flush=True)
            finally:
                if writer:writer.close()
                world.close()
    if digest(checkpoint)!=sha:raise ValueError("checkpoint changed during probe")
    (a.output/"probe.json").write_text(json.dumps({"schema":"microduck.walking-intermediate-probe/v1",
        "checkpoint_sha256":sha,"iteration":a.iteration,"candidate_selection_eligible":False,
        "inference":"Torch CPU; normalized actor, not ONNX acceptance","cases":reports},indent=2)+"\n")


if __name__=="__main__":main()
