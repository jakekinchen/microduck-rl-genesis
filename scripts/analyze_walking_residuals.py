"""Read-only V18 residual analysis; spectral association is not causal proof."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_walking_heading import verify_input_manifest
from scripts.evaluate_laser import digest


def spectrum(values):
    values = np.asarray(values, float)
    centered = values-values.mean()
    power = np.abs(np.fft.rfft(centered*np.hanning(len(values))))**2
    frequencies = np.fft.rfftfreq(len(values), .02)
    power[0] = 0
    return {"mean": float(values.mean()), "mean_abs": float(np.abs(values).mean()),
            "std": float(values.std()), "peak_hz": float(frequencies[np.argmax(power)]),
            "power_over_1hz_fraction": float(power[frequencies>1].sum()/power.sum()) if power.sum() else 0.}


def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    folders=[ROOT/"receipts/walking/20260906-v18-current", ROOT/"receipts/walking/20260906-v18-exposed-repeated"]
    records=[]
    for folder in folders:
        verify_input_manifest(folder)
        report=json.loads((folder/"evaluation.json").read_text())
        selected={c["case_id"]: c for c in report["case_reports"] if not c["passed"]}
        if folder==folders[0]:
            selected.update({c["case_id"]:c for c in report["case_reports"] if c["case_id"]=="nominal-20-20ms--forward-20"})
        rows={k:[] for k in selected}
        with (folder/"trajectory.jsonl").open() as f:
            for line in f:
                row=json.loads(line)
                if row["case_id"] in rows:rows[row["case_id"]].append(row)
        for name,case in selected.items():
            trace=rows[name];moving=[r for r in trace if 2<=r["time_s"]<=13]
            yaw=np.array([r["yaw_rate_rad_s"]-r["command"][2] for r in moving])
            correction=np.array([r["heading_control"]["correction_rad_s"] for r in moving])
            measured=np.array([r["heading_control"]["measured_unwrapped_heading_rad"] for r in moving])
            orientation_rate=np.diff(measured)/.02
            record={"receipt":str(folder.relative_to(ROOT)),"case_id":name,"failures":case["failures"],
                "body_yaw_error":spectrum(yaw),"command_correction":spectrum(correction),
                "imu_heading_rate":spectrum(orientation_rate),
                "correction_limit_fraction":float(np.mean(np.abs(correction)>=.24999)),
                "control_to_body_yaw_correlation":float(np.corrcoef(correction,yaw)[0,1]),
                "maximum_heading_excursion_rad":float(np.ptp(measured)),
                "heading":case["heading"],"self_contact":case["self_contact"],"self_load":case["self_load"]}
            if not case["self_contact"]["passed"]:
                witness=case["self_contact"]["first_violation"]["time_s"]
                record["startup_witness"]=[{k:r.get(k) for k in ("time_s","actor_mode","command","routing_command",
                    "policy_command","qpos","qvel","action_rad","self_load_physics")}
                    for r in trace if abs(r["time_s"]-witness)<=.040001 or .98<=r["time_s"]<=1.06]
            records.append(record)
    result={"schema":"microduck.walking-residual-analysis/v1","case_reports":records,
        "input_manifests":{str(f.relative_to(ROOT)):digest(f/"SHA256SUMS") for f in folders},
        "source_sha256":digest(Path(__file__)),"physics_executed":False,"policy_accepted":False,
        "boundary":"Recorded trace spectra and transition witnesses; closed-loop association cannot identify controller causality."}
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"analysis.json").write_text(json.dumps(result,indent=2)+"\n")
    (a.output/"SHA256SUMS").write_text(f"{digest(a.output/'analysis.json')}  analysis.json\n")
    for r in records:
        print(json.dumps({k:v for k,v in r.items() if k in ("case_id","failures","body_yaw_error","command_correction",
              "imu_heading_rate","correction_limit_fraction","control_to_body_yaw_correlation")}))


if __name__=="__main__":main()
