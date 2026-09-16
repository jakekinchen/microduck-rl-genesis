"""Additive whole-session heading audit; preserves original V23 window scores."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(rows, duration):
    if len(rows)!=round(duration*50): raise ValueError("complete session required")
    times=np.array([r["session_time_s"] for r in rows])
    np.testing.assert_allclose(times,(np.arange(len(rows))+1)*.02,rtol=0,atol=1e-8)
    selected=[r for r in rows if r["session_time_s"]>=2-1e-9]
    q=np.array([r["qpos"][3:7] for r in selected]);cmd=np.array([r["command"][2] for r in selected])
    if not np.isfinite(np.r_[q.ravel(),cmd]).all(): raise ValueError("finite telemetry required")
    np.testing.assert_allclose(np.linalg.norm(q,axis=1),1.,atol=1e-5)
    w,x,y,z=q.T
    fx,fy=1-2*(y*y+z*z),2*(x*y+w*z)
    if (np.hypot(fx,fy)<.25).any(): raise ValueError("horizontal heading unobservable")
    actual=np.unwrap(np.arctan2(fy,fx))
    requested=np.r_[0.,np.cumsum(cmd[:-1]*.02)]
    error=np.rad2deg(actual-actual[0]-requested)
    metrics={"endpoint_heading_error_deg":float(abs(error[-1])),"maximum_heading_error_deg":float(abs(error).max())}
    limits={"endpoint_heading_error_deg":15.,"maximum_heading_error_deg":20.}
    return {"passed":all(metrics[k]<=limit for k,limit in limits.items()),"metrics":metrics,"thresholds":limits,
            "samples":len(rows),"duration_s":duration,"heading_origin_reset_between_windows":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=json.loads((a.receipt/"probe.json").read_text())
    if not result["complete"] or result["bank"]!="endurance": raise ValueError("completed endurance receipt required")
    for line in (a.receipt/"SHA256SUMS").read_text().splitlines():
        sha,name=line.split("  ",1)
        path=(a.receipt/name).resolve()
        if not path.is_relative_to(a.receipt.resolve()) or digest(path)!=sha: raise ValueError("input manifest mismatch")
    rows={s["session_id"]:[] for s in result["session_reports"]}
    for line in (a.receipt/"trajectory.jsonl").open():
        row=json.loads(line)
        rows[row["session_id"]].append(row)
    reports={s["session_id"]:audit(rows[s["session_id"]],s["required_duration_s"]) for s in result["session_reports"]}
    out={"schema":"microduck.v23-whole-session-heading/v1","session_reports":reports,
         "passed_sessions":sum(r["passed"] for r in reports.values()),"total_sessions":len(reports),
         "input_manifest_sha256":digest(a.receipt/"SHA256SUMS"),"audit_source_sha256":digest(__file__),
         "proof_class":"additive_exposed_development_audit","original_scores_changed":False,
         "boundary":"Additional whole-session check identified during review of the V23 implementation. Original evaluator resets scoring origins per window, although physical/controller histories are continuous. This audit keeps one origin across all stops, with the existing 15/20 degree tolerances. Not an untouched final bank or physical yaw calibration."}
    with a.output.open("x") as f: json.dump(out,f,indent=2);f.write("\n")
    print(json.dumps({k:out[k] for k in ("passed_sessions","total_sessions")}),flush=True)


if __name__=="__main__": main()
