"""Predeclared six-window handoff diagnostic, original user-command scoring."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_heading import verify_input_manifest

BASE=ROOT/"receipts/walking/20260906-v15-standing-pair"
EXPOSED=ROOT/"receipts/walking/20260906-v15-standing-fresh"
FREEZE=ROOT/"experiments/walking/ramp-diagnostic-freeze-v16.json"
CASES=[("motor-10ms-sensor-20ms","forward-211"),
       ("motor-15ms-sensor-0ms","forward-201"),
       ("motor-15ms-sensor-0ms","turn-right-380")]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--freeze",action="store_true")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    verify_input_manifest(BASE)
    verify_input_manifest(EXPOSED)
    from scripts.evaluate_walking_standing_trained import SOURCES as V15_SOURCES
    sources=dict(json.loads((BASE/"standing/training.json").read_text())["source_sha256"])
    sources.update({n:digest(ROOT/n) for n in V15_SOURCES})
    sources.update({n:digest(ROOT/n) for n in ["scripts/probe_walking_command_ramp.py",
        "experiments/walking/command_ramp.py","tests/test_command_ramp.py",
        "experiments/walking/COMMAND-RAMP-DIAGNOSTIC-v16.md"]})
    inputs={str(folder.relative_to(ROOT)):digest(folder/"SHA256SUMS") for folder in (BASE,EXPOSED)}
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema":"microduck.command-ramp-diagnostic-freeze/v1","source_sha256":sources,
                       "input_manifest_sha256":inputs,"cases":CASES,"repeated_windows":2,
                       "ramp_rollouts_started":False,"candidate_selection_eligible":False},f,indent=2)
            f.write("\n")
        return
    if a.output is None:
        p.error("new output required")
    frozen=json.loads(FREEZE.read_text())
    if frozen["source_sha256"]!=sources or frozen["input_manifest_sha256"]!=inputs:
        raise ValueError("frozen source or input changed")
    import numpy as np
    import imageio.v2 as imageio
    from PIL import Image,ImageDraw
    from experiments.walking.command_ramp import RampedStandingSwitchWorld
    from experiments.walking.posture import evaluate_case
    from experiments.walking.heading import evaluate_heading
    from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
    from experiments.walking.self_load import record_self_loads,evaluate_self_load
    from experiments.laser.gait import GaitProbe
    a.output.mkdir(parents=True,exist_ok=False)
    suite=json.loads((EXPOSED/"suite.json").read_text())
    model=ROOT/"experiments/walking/models/contact-v11"
    geometry=SelfContactProbe(model/"scene.xml")
    reports=[]
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for timing_id,case_id in CASES:
            timing=next(t for t in suite["timing_profiles"] if t["id"]==timing_id)
            case=next(c for c in suite["cases"] if c["id"]==case_id)
            world=RampedStandingSwitchWorld(BASE/"policy.onnx",ROOT/".workspace/bam",
                standing_policy=BASE/"standing/policy.onnx",model_directory=model,
                motor_ticks=timing["motor_ticks"],sensor_ticks=timing["sensor_ticks"],yaw=case["yaw"],seed=suite["seed"],render=True)
            probe=GaitProbe(world.core)
            try:
                with record_self_loads(world) as loads:
                    for repeat in range(2):
                        name=f"{timing_id}--{case_id}--repeat-{repeat+1}"
                        rows,actions=[],[]
                        start=len(loads)
                        writer=imageio.get_writer(a.output/f"{name}.mp4",fps=25,codec="libx264",quality=7)
                        try:
                            for i in range(900):
                                if world.fell:
                                    break
                                command=case["command"] if 1<=i*.02<13 else [0,0,0]
                                row=probe.sample(world.step_command(command))
                                row.update(case_id=name,session_time_s=row["time_s"],time_s=(i+1)*.02,
                                    actor_observation=world.last_observation[0].tolist(),
                                    self_load_physics=[{**s,"interval_start_s":(i*4+j)*.005} for j,s in enumerate(loads[-4:])])
                                np.testing.assert_array_equal(np.asarray(row["command"],np.float32),np.asarray(command,np.float32))
                                rows.append(row);actions.append(world.last_action.copy())
                                stream.write(json.dumps(row)+"\n")
                                if i%2==0:
                                    frame=Image.fromarray(world.walking_frame());draw=ImageDraw.Draw(frame)
                                    draw.rectangle((0,0,720,38),fill=(15,20,30))
                                    draw.text((10,8),f"V16 COMMAND RAMP | {row['actor_mode']} | {name} | {row['session_time_s']:.2f}s",fill="white")
                                    writer.append_data(np.asarray(frame))
                            np.save(a.output/f"{name}-actions-float32.npy",np.asarray(actions,np.float32).reshape(-1,14))
                            if rows:
                                report=evaluate_case(rows,case,suite)
                                report.update(case_id=name,heading=evaluate_heading(rows),self_contact=evaluate_self_contact(rows,geometry),
                                    self_load=evaluate_self_load([s for row in rows for s in row["self_load_physics"]]))
                                report["combined_passed"]=report["passed"] and all(report[k]["passed"] for k in ("heading","self_contact","self_load"))
                            else:
                                report={"case_id":name,"passed":False,"combined_passed":False,"failures":["not_run_after_terminal_fall"]}
                            if len(loads)-start!=len(rows)*4:
                                raise ValueError("missing physical load evidence")
                            reports.append(report)
                            print(json.dumps({k:v for k,v in report.items() if k!="gait"}),flush=True)
                        finally:
                            writer.close()
            finally:
                world.close()
    for name,sha in sources.items():
        if digest(ROOT/name)!=sha:
            raise ValueError("source changed during diagnostic")
        dest=a.output/"source"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    result={"schema":"microduck.command-ramp-diagnostic/v1","total_cases":6,"combined_passed_cases":sum(c["combined_passed"] for c in reports),
            "case_reports":reports,"source_sha256":sources,"input_manifest_sha256":inputs,
            "policy_sha256":digest(BASE/"policy.onnx"),"standing_policy_sha256":digest(BASE/"standing/policy.onnx"),
            "candidate_selection_eligible":False,"physical_transfer_validated":False,"held_out":False,
            "boundary":"Six exposed handoff diagnostic windows; command-rate intervention, not altered actions/physics, full walking acceptance or physical transfer."}
    (a.output/"probe.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(FREEZE,a.output/"diagnostic-freeze.json")
    shutil.copy2(EXPOSED/"suite.json",a.output/"suite.json")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(f"{result['combined_passed_cases']}/6 diagnostic windows passed",flush=True)


if __name__=="__main__":
    main()
