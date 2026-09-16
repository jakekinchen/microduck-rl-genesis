"""Does a learned initial stopping stance contribute to long-delay collapse?

Only command-start time varies. This is feedback diagnosis, never permission
to bypass a required initial stand, alter actions or promote a shorter test.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from scripts.evaluate_laser import digest
    from scripts.evaluate_walking_heading import verify_input_manifest
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.laser.gait import GaitProbe
    import numpy as np
    receipt = ROOT / "receipts/walking/20260905-v6-current-sensor"
    verify_input_manifest(receipt)
    policy = receipt / "policy.onnx"
    expected = "948f6e601098845bf394c60de61cb38aa435d61934b86fc46dd39e4c9908c8cb"
    if digest(policy) != expected:
        raise ValueError("declared v6 final policy required")
    suite = json.loads((ROOT / "experiments/walking/tracking-suite-v1.json").read_text())
    case = next(case for case in suite["cases"] if case["id"] == "forward-20")
    args.output.mkdir(parents=True, exist_ok=False)
    reports = []
    for hold_ticks in (50, 12, 0):
        world = ConsistentSensorWalkingWorld(policy, ROOT / ".workspace/bam",
                                             motor_ticks=6, sensor_ticks=1,
                                             yaw=case["yaw"], seed=suite["seed"])
        probe = GaitProbe(world.core)
        rows = []
        onset_tilt = 0.
        try:
            for i in range(hold_ticks + 600 + 250):
                if i == hold_ticks and rows:
                    onset_tilt = rows[-1]["tilt_deg"]
                command = case["command"] if hold_ticks <= i < hold_ticks + 600 else [0, 0, 0]
                rows.append(probe.sample(world.step_command(command)))
                if world.fell:
                    break
            output = args.output / f"initial-stop-{hold_ticks}-ticks.jsonl"
            output.write_text("".join(json.dumps(row) + "\n" for row in rows))
            report = {"initial_hold_s": hold_ticks * .02, "tilt_at_motion_onset_deg": onset_tilt,
                      "scheduled_duration_s": (hold_ticks + 850) * .02,
                      "observed_duration_s": rows[-1]["time_s"], "fell": world.fell,
                      "fall_s_after_motion_command": rows[-1]["time_s"] - hold_ticks * .02 if world.fell else None,
                      "last_base_height_m": rows[-1]["robot_xyz_m"][2],
                      "last_tilt_deg": rows[-1]["tilt_deg"],
                      "minimum_actual_joint_margin_rad": min(row["minimum_actual_joint_margin_rad"] for row in rows),
                      "trace_sha256": digest(output)}
            reports.append(report)
            print(json.dumps(report), flush=True)
        finally:
            world.close()
    if digest(policy) != expected:
        raise ValueError("policy changed")
    report = {"schema": "microduck.walking-startup-stance-diagnostic/v1", "cases": reports,
              "policy_sha256": expected, "input_manifest_sha256": digest(receipt / "SHA256SUMS"),
              "acceptance_eligible": False,
              "boundary": "Same v6 final, native current-state clock, 30/20-ms timing, yaw, servo law and raw inference. Only initial zero-command duration changes. Feedback diagnostic, not fixed-action isolation, shorter-test acceptance, startup assistance or physical transfer."}
    (args.output / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n")
    shutil.copytree(receipt / "evaluator-source", args.output / "evaluator-source")
    for name in ("scripts/audit_walking_startup_stance.py", "scripts/evaluate_walking_heading.py",
                 "experiments/walking/heading.py"):
        target = args.output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    shutil.copy2(policy, args.output / "policy.onnx")
    (args.output / "SHA256SUMS").write_text("".join(
        f"{digest(path)}  {path.relative_to(args.output)}\n"
        for path in sorted(args.output.rglob("*")) if path.is_file()))


if __name__ == "__main__":
    main()
