"""Offline passive-measurement intake. This script cannot command hardware."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.calibration_v1 import template,validate_manifest,analyze,sha

SOURCES=["experiments/walking/calibration_v1.py","scripts/calibrate_walking_physics.py",
         "experiments/walking/PHYSICAL-CALIBRATION-v1.md","tests/test_walking_calibration.py"]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("init","freeze","analyze"))
    p.add_argument("--bundle",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    path=a.bundle/"measurements.json"
    if a.mode=="init":
        a.bundle.mkdir(parents=True,exist_ok=False)
        (a.bundle/"raw").mkdir()
        path.write_text(json.dumps(template(),indent=2)+"\n")
        print(path)
        return 0
    manifest=json.loads(path.read_text())
    frozen_path=a.bundle/"measurement-freeze.json"
    if a.mode=="freeze":
        failures=validate_manifest(a.bundle,manifest)
        if failures:
            print(json.dumps({"status":"blocked_inputs","failures":failures},indent=2))
            return 2
        with frozen_path.open("x") as f:
            json.dump({"created_at":datetime.now(timezone.utc).isoformat(),"manifest_sha256":sha(path),
                       "source_sha256":{s:sha(ROOT/s) for s in SOURCES},
                       "split_boundary":"Preassigned acquisition sessions; validation outcomes become exposed on analysis."},f,indent=2)
            f.write("\n")
        return 0
    failures=validate_manifest(a.bundle,manifest)
    if not failures:
        if not frozen_path.is_file(): raise ValueError("freeze measurement identities before fitting")
        frozen=json.loads(frozen_path.read_text())
        if frozen["manifest_sha256"]!=sha(path): raise ValueError("frozen manifest changed")
        for source,digest in frozen["source_sha256"].items():
            if sha(ROOT/source)!=digest: raise ValueError("frozen source changed:"+source)
    try:
        report=analyze(a.bundle,manifest)
    except (ValueError,KeyError,TypeError,OverflowError) as error:
        report={"schema":"microduck.passive-calibration-result/v1","status":"invalid_measurements",
                "failures":[str(error)],"physical_calibration_complete":False,"simulator_parameters_changed":False}
    report.update(manifest_sha256=sha(path),created_at=datetime.now(timezone.utc).isoformat(),
                  source_sha256={s:sha(ROOT/s) for s in SOURCES})
    if a.output is not None:
        with a.output.open("x") as f: json.dump(report,f,indent=2); f.write("\n")
    print(json.dumps({k:report[k] for k in ("status","physical_calibration_complete","failures")},indent=2))
    return 0 if report["status"]=="passive_stage_passed" else 2


if __name__=="__main__": raise SystemExit(main())
