"""Retain fixed walking diagnosis/smoke evidence without rewriting old receipts."""
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    summaries=[]
    for name in ("walking-20260905-v1-smoke","walking-20260905-v2-smoke"):
        run=ROOT/"logs"/name;record=json.loads((run/"run.json").read_text())
        if record["status"]!="completed":raise ValueError("completed smoke required")
        out=a.output/name;out.mkdir()
        shutil.copy2(run/"run.json",out/"run.json")
        checkpoint=run/record["checkpoint"]
        if checkpoint.parent!=run or digest(checkpoint)!=record["checkpoint_sha256"]:raise ValueError("checkpoint drift")
        shutil.copy2(checkpoint,out/checkpoint.name)
        shutil.copy2(Path("/private/tmp")/(name+".log"),out/"stdout.log")
        for source,sha in record["source_sha256"].items():
            if digest(ROOT/source)!=sha:raise ValueError("smoke source changed")
            dest=out/"source"/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,dest)
        summaries.append({"run":name,"status":"completed","new_transitions":record["new_transitions"],
                          "boundary":"Five-iteration software smoke only; no gait acceptance."})
    probe=ROOT/"receipts/walking/20260905-v1-probe250"
    shutil.copytree(probe,a.output/"v1-intermediate-probe250")
    shutil.copy2("/private/tmp/walking-v1-probe250.log",a.output/"probe250.stdout.log")
    shutil.copy2(ROOT/"scripts/probe_walking_checkpoint.py",a.output/"probe250-source.py")
    source=ROOT/"receipts/walking/20260905-timing-diagnosis/genesis-nominal-diagnostic/audit.json"
    import numpy as np
    audit=json.loads(source.read_text())
    inertials=[{"body":r["body"],"mass_delta_kg":r["genesis_mass"]-r["mujoco_mass"],
        "max_sorted_principal_inertia_delta_kg_m2":float(np.abs(np.sort(np.linalg.eigvalsh(r["genesis_inertia"]))-
            np.sort(r["mujoco_principal_inertia"])).max())} for r in audit["inertials"]]
    result={"schema":"microduck.walking-support/v1","smokes":summaries,
        "inertia_source_sha256":digest(source),"per_link_mass_and_principal_inertia_comparison":inertials,
        "inertia_boundary":"Numerical principal values and masses agree; not a full COM/frame/contact or hardware calibration.",
        "training_domain_clarification":"V1/v2 have nominal rigid model and explicit timing variation. Inherited BAM initialization also retains 6.5–8.2 V supply and 0–0.2 ohm voltage-drop draws. The original timing-only cfg label is incomplete; sources and historical run records remain unchanged. Native evaluator is 7.35 V, zero drop, within that envelope.",
        "candidate_accepted":False,"physical_transfer_validated":False}
    (a.output/"support.json").write_text(json.dumps(result,indent=2)+"\n")
    shutil.copy2(Path(__file__),a.output/"retention-source.py")
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))
    print(json.dumps({"output":str(a.output),"smokes":summaries}),flush=True)


if __name__=="__main__":main()
