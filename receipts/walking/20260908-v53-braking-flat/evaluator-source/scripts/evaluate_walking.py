"""Frozen visible command/timing battery, independent of the walking reward."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
SOURCES=["scripts/evaluate_walking.py","scripts/export_walking.py","experiments/walking/world.py",
         "experiments/walking/metrics.py","experiments/walking/suite-v1.json","experiments/laser/gait.py",
         "experiments/laser/face_world.py","experiments/laser/world.py","experiments/laser/camera_alignment.py",
         "evaluator/core.py","evaluator/config-v1.json","export_onnx.py"]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--freeze",action="store_true")
    p.add_argument("--run-id")
    p.add_argument("--policy",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--video",action="store_true")
    a=p.parse_args()
    frozen=ROOT/"experiments/walking/evaluator-freeze-v1.json"
    if a.freeze:
        if frozen.exists():raise ValueError("evaluator already frozen")
        frozen.write_text(json.dumps({"schema":"microduck.walking-evaluator-freeze/v1","source_sha256":{s:digest(ROOT/s) for s in SOURCES},
                                     "candidate":"declared final walking-v1 checkpoint, not yet inspected", "held_out":False},indent=2)+"\n")
        print("Walking evaluator frozen");return
    if a.output is None or bool(a.run_id)==bool(a.policy):p.error("one run-id or policy and a new output required")
    for source,sha in json.loads(frozen.read_text())["source_sha256"].items():
        if digest(ROOT/source)!=sha:raise ValueError(f"evaluator source drift: {source}")
    a.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image,ImageDraw
    from experiments.walking.world import WalkingWorld
    from experiments.walking.metrics import evaluate_case
    from experiments.laser.gait import GaitProbe
    from scripts.export_walking import export_walking
    exported=None;parity=None
    if a.run_id:policy,parity,exported=export_walking(a.run_id,a.output)
    else:
        policy=a.output/"policy.onnx";shutil.copy2(a.policy,policy)
    suite=json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
    reports=[];real_error=0.
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing in suite["timing_profiles"]:
            for case in suite["cases"]:
                case_id=f'{timing["id"]}--{case["id"]}'
                world=WalkingWorld(policy,ROOT/".workspace/bam",motor_ticks=timing["motor_ticks"],sensor_ticks=timing["sensor_ticks"],yaw=case["yaw"],seed=suite["seed"],render=a.video)
                probe=GaitProbe(world.core);rows=[];actions=[]
                writer=imageio.get_writer(a.output/f"{case_id}.mp4",fps=25,codec="libx264",quality=7) if a.video else None
                try:
                    for i in range(round(suite["duration_s"]*50)):
                        t=i*.02
                        command=case["command"] if suite["move_start_s"]<=t<suite["stop_start_s"] else [0,0,0]
                        row=probe.sample(world.step_command(command));row["case_id"]=case_id
                        row["actor_observation"]=world.last_observation[0].tolist()
                        if exported is not None:
                            with torch.no_grad():expected=exported(torch.from_numpy(world.last_observation)).numpy()[0]
                            real_error=max(real_error,float(np.abs(expected-world.last_action).max()))
                            if real_error>=1e-4:raise ValueError("real-observation export parity failed")
                        rows.append(row);actions.append(world.last_action.copy());stream.write(json.dumps(row)+"\n")
                        if writer and i%2==0:
                            frame=Image.fromarray(world.walking_frame());draw=ImageDraw.Draw(frame)
                            draw.rectangle((0,0,720,38),fill=(15,20,30))
                            draw.text((10,8),f"WALKING DEVELOPMENT | {case_id} | {row['time_s']:.2f}s | cmd {command}",fill="white")
                            writer.append_data(np.asarray(frame))
                        if world.fell:break
                    np.save(a.output/f"{case_id}-actions-float32.npy",np.asarray(actions,np.float32))
                    report=evaluate_case(rows,case,suite);report.update(case_id=case_id,timing_profile=timing["id"])
                    reports.append(report)
                    print(json.dumps({k:v for k,v in report.items() if k!="gait"}),flush=True)
                finally:
                    if writer:writer.close()
                    world.close()
    result={"schema":"microduck.walking-evaluation/v1","proof_class":"visible_development","held_out":False,
            "policy_sha256":digest(policy),"suite_sha256":digest(ROOT/"experiments/walking/suite-v1.json"),
            "evaluator_freeze_sha256":digest(frozen),"passed_cases":sum(c["passed"] for c in reports),"total_cases":len(reports),
            "case_reports":reports,"export_parity":parity,"max_real_observation_action_error_rad":real_error if exported is not None else None,
            "physical_transfer_validated":False,"reserved_opened":False,
            "boundary":"Command/timing visible development, no physical calibration. Raw ONNX action is unchanged; declared FIFO latency is a physical-loop parameter, not action smoothing."}
    (a.output/"evaluation.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(frozen,a.output/"evaluator-freeze.json")
    for name in SOURCES:
        dest=a.output/"evaluator-source"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(f'{result["passed_cases"]}/{len(reports)} command/timing cases passed',flush=True)


if __name__=="__main__":main()
