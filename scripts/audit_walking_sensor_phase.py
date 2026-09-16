"""Isolate hidden pre-integration IMU age in native closed-loop development."""
import argparse
from collections import deque
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    from experiments.walking.world import WalkingWorld
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    from scripts.evaluate_laser import digest
    a.output.mkdir(parents=True, exist_ok=False)
    suite = json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
    reports = []
    for phase in ("legacy-pre-integration", "fresh-post-integration"):
        for case in (suite["cases"][1], suite["cases"][3]):
            name = f'{phase}--{case["id"]}'
            world_cls = WalkingWorld if phase == "legacy-pre-integration" else ConsistentSensorWalkingWorld
            world = world_cls(a.receipt/"policy.onnx", ROOT/".workspace/bam", motor_ticks=4, sensor_ticks=1, yaw=case["yaw"], seed=suite["seed"])
            probe = GaitProbe(world.core)
            rows, actions = [], []
            try:
                for i in range(900):
                    command = case["command"] if 1 <= i*.02 < 13 else [0, 0, 0]
                    row = probe.sample(world.step_command(command))
                    rows.append(row)
                    actions.append(world.last_action.copy())
                    if world.fell:
                        break
                report = evaluate_case(rows, case, suite)
                report["sensor_phase"] = phase
                reports.append(report)
                (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
                np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
                print(json.dumps({k: v for k, v in report.items() if k != "gait"}), flush=True)
            finally:
                world.close()
    result = {"schema": "microduck.sensor-phase-feedback-ablation/v1", "cases": reports,
        "policy_sha256": digest(a.receipt/"policy.onnx"), "acceptance_eligible": False,
        "boundary": "Closed-loop ablation changes only sensor sampling to copied current state, removing implicit 5-ms IMU age. Policy bytes, commands, physical forces and explicit FIFO delay are unchanged. Feedback actions can differ. This is not fixed-action or hardware calibration; reported yaw also uses current copied state."}
    (a.output/"audit.json").write_text(json.dumps(result, indent=2)+"\n")
    for name in ("scripts/audit_walking_sensor_phase.py", "microduck/bam_actuator.py", "experiments/walking/world.py", "experiments/walking/sensor_world.py", "experiments/walking/posture.py", "experiments/walking/metrics.py", "experiments/walking/suite-v1.json"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
