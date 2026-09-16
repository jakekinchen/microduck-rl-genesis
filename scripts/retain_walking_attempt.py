"""Preserve a stopped/failed diagnostic attempt without rewriting its run log."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--stdout",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--reason",required=True)
    a=p.parse_args()
    if not a.run_id.replace("-","").isalnum():raise ValueError("invalid run id")
    run=ROOT/"logs"/a.run_id
    record=json.loads((run/"run.json").read_text())
    a.output.mkdir(parents=True,exist_ok=False)
    shutil.copy2(run/"run.json",a.output/"original-run.json")
    shutil.copy2(a.stdout,a.output/"stdout.log")
    for name,sha in record.get("source_sha256",{}).items():
        source=ROOT/name
        if digest(source)!=sha:raise ValueError(f"source changed before retention: {name}")
        destination=a.output/"source"/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
    for checkpoint in sorted(run.glob("model_*.pt")):
        shutil.copy2(checkpoint,a.output/checkpoint.name)
    text=a.stdout.read_text()
    counts=[int(n) for n in re.findall(r"Total steps:\s*(\d+)",text)]
    terminal={"schema":"microduck.walking-attempt-terminal/v1","status":"quarantined",
              "reason":a.reason,"policy_accepted":False,
              "planned_transitions_not_completed":record.get("planned_new_transitions",record["new_transitions"]),
              "last_logged_completed_transitions":max(counts,default=0),
              "partial_iteration_transitions":"unknown; not represented by completed count",
              "original_run_status_is_historical":True}
    (a.output/"terminal.json").write_text(json.dumps(terminal,indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"))
    print(json.dumps(terminal))


if __name__=="__main__":main()
