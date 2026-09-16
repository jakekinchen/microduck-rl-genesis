"""Offline yaw-reward sensitivity, not a realizable controller intervention."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = args.receipt / "SHA256SUMS"
    bound = {}
    for line in manifest.read_text().splitlines():
        sha, name = line.split("  ", 1)
        path = args.receipt / name
        if path.is_symlink() or digest(path) != sha:
            raise ValueError(f"input integrity failed: {name}")
        bound[name] = sha
    if "trajectory.jsonl" not in bound:
        raise ValueError("manifest must bind the trajectory")
    import numpy as np
    rows = defaultdict(list)
    for row in map(json.loads, (args.receipt / "trajectory.jsonl").open()):
        rows[row["case_id"]].append(row)
    reports = []
    for name, sequence in rows.items():
        moving = [r for r in sequence if 2 <= r["time_s"] <= 13]
        if len(moving) != 551:
            raise ValueError(f"complete moving interval required: {name}")
        error = np.array([r["yaw_rate_rad_s"] - r["command"][2] for r in moving])
        if not np.isfinite(error).all():
            raise ValueError("nonfinite error")
        bias = error.mean()
        centered = error - bias
        # Exact existing yaw-only reward contributions in reward units/second.
        score = lambda e: float((5 * np.exp(-(e / .35)**2)
                                - 10 * np.maximum(np.abs(e) - .05, 0)).mean())
        reports.append({"case_id": name, "mean_yaw_error_rad_s": float(bias),
                        "zero_mean_wobble_std_rad_s": float(error.std()),
                        "integrated_body_gyro_bias_deg": float(np.degrees(bias * 11)),
                        "observed_yaw_reward_per_s": score(error),
                        "counterfactual_centered_yaw_reward_per_s": score(centered),
                        "reward_improvement_if_only_bias_removed_per_s": score(centered) - score(error)})
    args.output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "microduck.walking-yaw-objective-audit/v1",
              "trajectory_sha256": bound["trajectory.jsonl"],
              "input_manifest_sha256": digest(manifest), "cases": reports,
              "boundary": "Offline algebra on exposed recorded traces. Subtracting the episode mean is NOT a realizable action, policy, causal learning result or acceptance score. Body gyro integral is not planar quaternion heading. Physics/actions/checkpoint are untouched."}
    (args.output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    shutil.copy2(Path(__file__), args.output / "audit-source.py")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(p)}  {p.relative_to(args.output)}\n"
        for p in sorted(args.output.rglob("*")) if p.is_file()))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
