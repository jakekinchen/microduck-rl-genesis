"""Close the bounded gait diagnosis with comparison and immutable payload hashes."""
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
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--focused-tests",type=Path,required=True)
    p.add_argument("--full-tests",type=Path,required=True)
    p.add_argument("--playground-events",type=Path,required=True)
    p.add_argument("--smoke-run",type=Path,required=True)
    p.add_argument("--smoke-stdout",type=Path,required=True)
    a=p.parse_args()
    output=ROOT/"receipts/laser-gait"
    if (output/"comparison.json").exists() or (output/"SHA256SUMS").exists():raise ValueError("gait package already frozen")
    before=json.loads((a.baseline/"evaluation.json").read_text())
    after=json.loads((a.candidate/"evaluation.json").read_text())
    training=json.loads((a.candidate/"training.json").read_text())
    if training["status"]!="completed" or training["variant"]!="gait-v4":raise ValueError("completed v4 required")
    if before["evaluator_freeze_sha256"]!=after["evaluator_freeze_sha256"]:raise ValueError("comparison evaluator differs")
    if after["policy_sha256"]!=digest(a.candidate/"policy.onnx"):raise ValueError("candidate changed")
    if before["policy_sha256"]!=digest(a.baseline/"policy.onnx"):raise ValueError("baseline changed")
    if [c["case_id"] for c in before["case_reports"]]!=[c["case_id"] for c in after["case_reports"]]:raise ValueError("case coverage differs")
    smoke=json.loads((a.smoke_run/"run.json").read_text())
    if smoke["status"]!="completed" or smoke["variant"]!="gait-v4" or smoke["new_transitions"]!=7680:
        raise ValueError("completed 64x5 v4 smoke required")
    for record in (training,smoke):
        for name,sha in record["source_sha256"].items():
            if digest(ROOT/name)!=sha:raise ValueError(f"source changed before retention: {name}")
    for manifest in output.rglob("SHA256SUMS"):
        for line in manifest.read_text().splitlines():
            sha,name=line.split("  ",1)
            if digest(manifest.parent/name)!=sha:raise ValueError(f"retained payload changed: {manifest.parent/name}")
    smoke_output=output/"20260905-v4-smoke"
    smoke_output.mkdir(exist_ok=False)
    shutil.copy2(a.smoke_run/"run.json",smoke_output/"training.json")
    shutil.copy2(a.smoke_run/smoke["checkpoint"],smoke_output/"source-checkpoint.pt")
    shutil.copy2(a.smoke_stdout,smoke_output/"training.stdout.log")
    for name in smoke["source_sha256"]:
        dest=smoke_output/"source"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    (smoke_output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(smoke_output)}\n" for f in sorted(smoke_output.rglob("*")) if f.is_file()))
    def compact(report):
        return {"policy_sha256":report["policy_sha256"],"target_passes":report["target_only_passed_cases"],
                "gait_passes":report["gait_rejection_passed_cases"],"composite_passes":report["passed_cases"],
                "cases":[{"case_id":c["case_id"],"failures":c["failures"],"target_pass":c["target"]["passed"],
                           "gait_pass":c["gait"]["rejection_gate_passed"],"fell":c["gait"]["fell"],
                           "swings_left_right":c["gait"]["qualified_swings_left_right"],
                           "bilateral_step_coverage":c["gait"]["bilateral_step_coverage_during_translation"],
                           "worst_joint_stop_fraction":max(c["gait"]["joint_hard_stop_fraction"] or [1.]),
                           "loaded_slip_p95_m_s":c["gait"]["loaded_slip_p95_m_s"]} for c in report["case_reports"]]}
    result={"schema":"microduck.gait-correction-comparison/v4","baseline":compact(before),"candidate":compact(after),
            "new_v4_transitions":training["new_transitions"],"elapsed_s":training["elapsed_s"],
            "all_visible_composite_gates_passed":after["passed_cases"]==len(after["case_reports"]),
            "physical_transfer_validated":False,"reserved_opened":after["reserved_opened"],
            "boundary":"Independent visible-development diagnostics. Camera correction is physics-neutral; no physical or canonical walking acceptance."}
    for source,name in ((a.focused_tests,"focused-tests.stdout.log"),(a.full_tests,"full-tests.stdout.log"),(a.playground_events,"playground-events.jsonl")):
        shutil.copy2(source,output/name)
    for source,name in ((Path("/private/tmp/laser-gait-ui-state.json"),"playground-state.json"),
                        (Path("/private/tmp/laser-gait-ui-frame.jpg"),"playground-frame.jpg")):
        shutil.copy2(source,output/name)
    source_names=["AGENTS.md","GOAL.md","TRAINING_ACTUALIZATION.md","experiments/laser/GAIT_DIAGNOSIS.md",
                  "experiments/laser/playground.html","experiments/laser/playground.css","experiments/laser/playground.js",
                  "scripts/laser_playground.py","scripts/package_laser_gait.py","scripts/retain_gait_attempt.py",
                  "tests/test_laser_gait.py","experiments/laser/gait-evaluator-freeze-v4.json"]
    for name in source_names:
        dest=output/"delivery-source"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    (output/"comparison.json").write_text(json.dumps(result,indent=2)+"\n")
    (output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(output)}\n" for f in sorted(output.rglob("*")) if f.is_file() and f!=output/"SHA256SUMS"))
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
