"""Produce a compact measured comparison and bind a finished dynamic receipt tree."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def compact(path):
    path = path.resolve()
    record = json.loads((path/"evaluation.json").read_text())
    if digest(path/"policy.onnx") != record["policy_sha256"]:
        raise ValueError("policy hash mismatch")
    cases = record.get("case_reports", [])
    distances = [c["mean_visible_distance_m"] for c in cases if c["mean_visible_distance_m"] is not None]
    return {"receipt": str(path.relative_to(ROOT)), "policy_sha256": record["policy_sha256"],
            "passed": record["passed_cases"], "total": record["total_cases"], "falls": record["falls"],
            "mean_tracking_fraction": float(np.mean([c["tracking_fraction"] for c in cases])) if cases else None,
            "mean_distance_m": float(np.mean(distances)) if distances else None,
            "cases_with_post_warmup_distance": len(distances)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--baseline-development", required=True, type=Path)
    p.add_argument("--candidate-development", required=True, type=Path)
    p.add_argument("--baseline-reserved", required=True, type=Path)
    p.add_argument("--candidate-reserved", required=True, type=Path)
    args = p.parse_args()
    output = args.root/"comparison.json"
    if output.exists():
        raise ValueError("refusing to overwrite a finished comparison")
    records = {k: compact(getattr(args, k)) for k in ("baseline_development", "candidate_development", "baseline_reserved", "candidate_reserved")}
    result = {"schema": "microduck.dynamic-laser-comparison/v1", "evidence": "flat-ground simulated-coordinate development only", **records}
    output.write_text(json.dumps(result, indent=2)+"\n")
    source_root = args.root/"delivery-source"
    for name in ("scripts/laser_playground.py", "scripts/package_laser_dynamic.py", "scripts/audit_laser_dynamic_replay.py", "tests/test_laser_dynamic.py", "tests/test_first_party_development.py",
                 "experiments/laser/playground.html", "experiments/laser/playground.css", "experiments/laser/playground.js",
                 "experiments/laser/DYNAMIC_BUILD.md"):
        dest = source_root/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    manifest = args.root/"SHA256SUMS"
    manifest.write_text("".join(f"{digest(f)}  {f.relative_to(args.root)}\n" for f in sorted(args.root.rglob("*")) if f.is_file() and f != manifest))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
