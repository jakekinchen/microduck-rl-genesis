"""Reproduce the bounded timing factorial and bind it to exact sources."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    policy=ROOT/"receipts/laser-gait/20260905-v4-evaluation/policy.onnx"
    sources=["scripts/audit_walk_mujoco.py","scripts/audit_walk_foundation.py","scripts/retain_walking_diagnosis.py",
             "experiments/laser/gait.py","experiments/laser/world.py","experiments/laser/face_world.py","evaluator/core.py"]
    hashes={s:digest(ROOT/s) for s in sources}
    reports=[]
    for motor,sensor in ((0,0),(0,1),(4,0),(4,1),(6,1)):
        name=f"motor-{motor}-sensor-{sensor}"
        command=[sys.executable,"scripts/audit_walk_mujoco.py","--output",str(a.output/name),"--policy",str(policy),"--motor-delay",str(motor),"--sensor-delay",str(sensor)]
        with (a.output/f"{name}.stdout.log").open("w") as stream:
            subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
        rows=json.loads((a.output/name/"audit.json").read_text())
        reports.extend({k:r[k] for k in ("case","motor_delay_physics_steps","sensor_delay_control_steps","qualified_swings_left_right","rejection_reasons","path_length_m")} for r in rows)
        print(name,"complete",flush=True)
    for source,sha in hashes.items():
        if digest(ROOT/source)!=sha:raise ValueError("diagnostic source changed during execution")
        dest=a.output/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
    shutil.copytree("/private/tmp/walk-foundation-v4-20260905",a.output/"genesis-nominal-diagnostic")
    shutil.copy2("/private/tmp/walk-foundation-v4-20260905.log",a.output/"genesis-nominal.stdout.log")
    (a.output/"comparison.json").write_text(json.dumps({"policy_sha256":digest(policy),"source_sha256":hashes,"cases":reports,
        "boundary":"Native timing factorial, fresh feedback at each condition. Not identical-action isolation or physical timing calibration. Genesis mass/site diagnostic is retained from the preceding run."},indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__=="__main__":main()
