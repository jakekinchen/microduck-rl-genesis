"""Composite target AND gait development evaluation for the explicit v4 lane.

The old v1 target-only evaluator remains reproducible, but cannot admit a v3
candidate. This script deliberately has no reserved/physical promotion option.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import imageio.v2 as imageio
import mujoco
import numpy as np
from experiments.laser.face_world import FaceFirstLaserWorld
from experiments.laser.gait import GaitProbe, summarize_gait
from microduck.laser_dynamics import domain_draw, program_target
from scripts.evaluate_laser import digest, export_own
from scripts.evaluate_laser_dynamic import annotate, metrics


def combine_gates(target, gait, *, duration_s, required_s):
    complete=duration_s>=required_s
    failures=[]
    if not complete: failures.append("incomplete_case")
    if not target["passed"]: failures.append("target_pursuit_failed")
    failures.extend(gait["rejection_reasons"])
    return {"development_passed":bool(not failures and gait["rejection_gate_passed"]),
            "failures":failures, "physical_transfer_validated":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--bam-repo",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--video",action="store_true")
    a=p.parse_args()
    frozen_path=ROOT/"experiments/laser/gait-evaluator-freeze-v4.json"
    frozen=json.loads(frozen_path.read_text())
    for source,expected in frozen["source_sha256"].items():
        if digest(ROOT/source)!=expected:raise ValueError(f"gait evaluator changed after freeze: {source}")
    a.output.mkdir(parents=True,exist_ok=False)
    spec_path=ROOT/"experiments/laser/gait-correction-v4.json"
    spec=json.loads(spec_path.read_text())
    thresholds=json.loads((ROOT/"experiments/laser/dynamic-suite-v1.json").read_text())["thresholds"]
    policy,parity,exported=export_own(a.run_id,a.output)
    import torch
    reports=[]
    observed_parity=0.
    with (a.output/"trajectory.jsonl").open("w") as stream:
        for i,case in enumerate(spec["visible_cases"]):
            world=FaceFirstLaserWorld(policy,a.bam_repo,domain_draw(76341+i,False),render=a.video)
            probe=GaitProbe(world.core)
            rows=[];actions=[]
            writer=imageio.get_writer(a.output/f'{case["id"]}.mp4',fps=25,codec="libx264",quality=7) if a.video else None
            try:
                for step in range(round(case["seconds"]*50)):
                    target,visible,label,epoch=program_target(case["program"],step*.02,rotation=case["rotation_rad"])
                    row=world.step(target,visible)
                    row.update(case_id=case["id"],target_epoch=epoch,target_label=label)
                    with torch.no_grad():
                        expected=exported(torch.from_numpy(world.last_observation)).numpy()[0]
                    observed_parity=max(observed_parity,float(np.abs(expected-world.last_action).max()))
                    if observed_parity>=1e-4: raise ValueError("real-observation export parity failed")
                    measured=probe.sample(row)
                    rows.append(measured);actions.append(world.last_action.copy())
                    stream.write(json.dumps(measured)+"\n")
                    if writer and step%2==0:
                        frame=world.frame(target,visible,view="inspection")
                        writer.append_data(annotate(frame,row,"GAIT DEVELOPMENT — not a walking/transfer pass"))
                    if world.fell:break
                np.save(a.output/f'{case["id"]}-actions-float32.npy',np.array(actions,np.float32))
                target_result=metrics(rows,case["program"],thresholds)
                # Same old proximity/stop criteria, with the NEW preregistered
                # duration (16 s circles/eights, full 48 s retarget+loss case).
                proximity=(target_result["waypoints_acquired"]>=thresholds["minimum_waypoints_acquired"] if case["program"]=="retarget" else target_result["tracking_fraction"]>=thresholds["minimum_tracking_fraction_after_5s"])
                loss_speed=target_result["max_lost_target_speed_m_s"]
                target_result["passed"]=bool(proximity and not world.fell and rows[-1]["time_s"]>=case["seconds"] and (loss_speed is None or loss_speed<.08))
                gait=summarize_gait(rows)
                report={"case_id":case["id"],"target":target_result,"gait":gait,
                        **combine_gates(target_result,gait,duration_s=rows[-1]["time_s"],required_s=case["seconds"])}
                reports.append(report)
                print(json.dumps({k:v for k,v in report.items() if k not in ("gait","target")}),flush=True)
            finally:
                if writer:writer.close()
                world.close()
    result={"schema":"microduck.laser-gait-evaluation/v4","proof_class":"visible_development",
            "policy_sha256":digest(policy),"spec_sha256":digest(spec_path),
            "evaluator_freeze_sha256":digest(frozen_path),
            "model_root_sha256":world.core.model_root_digest,"bam_commit":"62bd8ce12154340be97e06f7f41a0ca8f116d967",
            "camera_revision":world.camera_revision,
            "target_only_passed_cases":sum(r["target"]["passed"] for r in reports),
            "gait_rejection_passed_cases":sum(r["gait"]["rejection_gate_passed"] for r in reports),
            "passed_cases":sum(r["development_passed"] for r in reports),"case_reports":reports,
            "export_parity":parity,"max_real_observation_action_error_rad":observed_parity,
            "reserved_opened":False,"physical_transfer_validated":False,
            "boundary":"Composite development rejection gate. No candidate promotion or hardware operation; flat oracle task, uncalibrated gait envelope."}
    (a.output/"evaluation.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(spec_path,a.output/"gait-spec.json")
    shutil.copy2(frozen_path,a.output/"evaluator-freeze.json")
    for source in ("scripts/evaluate_laser_gait.py","experiments/laser/gait.py","experiments/laser/world.py","experiments/laser/face_world.py","experiments/laser/camera_alignment.py","microduck/laser_face_command.py"):
        dest=a.output/"evaluator-source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"))
    print(f'{result["passed_cases"]}/{len(reports)} composite cases passed',flush=True)


if __name__=="__main__":main()
