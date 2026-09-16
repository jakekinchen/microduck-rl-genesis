"""Offline comparison of consumed V19 native and V20 Genesis traces."""
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.analyze_walking_residuals import spectrum
from scripts.evaluate_laser import digest
from scripts.probe_walking_pair_genesis_r2 import CASES, NATIVE


def main():
    genesis = ROOT / "receipts/walking/20260906-v20-paired-genesis-r2"
    output = ROOT / "receipts/walking/20260906-v20-engine-comparison"
    for folder in (genesis, NATIVE):
        for line in (folder / "SHA256SUMS").read_text().splitlines():
            sha, name = line.split("  ", 1)
            assert digest(folder / name) == sha
    native = {}
    with (NATIVE / "trajectory.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            native.setdefault(row["case_id"], []).append(row)
    reports = []
    for timing, case in CASES:
        name = timing + "--" + case
        rows = {"Genesis_CPU": [json.loads(line) for line in (genesis / (name+".jsonl")).read_text().splitlines()],
                "native_MuJoCo": native[name+"--repeat-1"]}
        report = {"case_id": name}
        for engine, trace in rows.items():
            moving = [r for r in trace if 2 <= r["time_s"] <= 13]
            report[engine] = {"control_rows": len(trace), "moving_rows": len(moving),
                "yaw_error": spectrum([r["yaw_rate_rad_s"]-r["command"][2] for r in moving]),
                "heading_correction": spectrum([r["heading_control"]["correction_rad_s"] for r in moving])}
        reports.append(report)
    result = {"cases": reports, "physics_executed": False,
        "input_manifest_sha256": {str(p.relative_to(ROOT)): digest(p/"SHA256SUMS") for p in (genesis, NATIVE)},
        "boundary": "Same paired actors and controller; independent closed loops produce different actions. Spectral association is not fixed-action causality or calibrated physics."}
    output.mkdir(parents=True, exist_ok=False)
    (output / "analysis.json").write_text(json.dumps(result, indent=2)+"\n")
    shutil.copy2(__file__, output / "analysis-source.py")
    (output / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(output.iterdir()) if p.is_file()))
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
