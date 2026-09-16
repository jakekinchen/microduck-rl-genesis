"""Retain an intermediate diagnostic and score its additive posture rejection."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from experiments.walking.posture import posture_metrics,POSTURE_LIMITS


def main():
    p=argparse.ArgumentParser();p.add_argument("--probe",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--stdout",type=Path,required=True);a=p.parse_args()
    original=json.loads((a.probe/"probe.json").read_text())
    if original.get("candidate_selection_eligible") is not False:raise ValueError("diagnostic probe required")
    a.output.mkdir(parents=True,exist_ok=False)
    reports=[]
    for path in sorted(a.probe.iterdir()):
        if not path.is_file() or path.is_symlink():raise ValueError("regular probe files only")
        if path.suffix==".jsonl":
            if path.stat().st_size>16*1024*1024:raise ValueError("bounded probe required")
            rows=[json.loads(line) for line in path.read_text().splitlines()]
            metrics=posture_metrics(rows)
            reports.append({"case":path.stem,"source_sha256":digest(path),"metrics":metrics,
                "passed":all(metrics[k]<=limit for k,limit in POSTURE_LIMITS.items())})
        shutil.copy2(path,a.output/path.name)
    shutil.copy2(a.stdout,a.output/"stdout.log")
    sources=["scripts/probe_walking_checkpoint.py","scripts/audit_walking_posture.py",
             "experiments/walking/posture.py","microduck/constants.py",
             "experiments/walking/evaluator-freeze-posture-v1.json"]
    for source in sources:
        dest=a.output/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    (a.output/"posture-audit.json").write_text(json.dumps({"schema":"microduck.intermediate-posture-audit/v1",
        "candidate_selection_eligible":False,"checkpoint_sha256":original["checkpoint_sha256"],
        "thresholds":POSTURE_LIMITS,"cases":reports,"physical_transfer_validated":False,
        "boundary":"Posture rejection applied to retained intermediate feedback traces; not a final candidate evaluation."},indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps(reports),flush=True)


if __name__=="__main__":main()
