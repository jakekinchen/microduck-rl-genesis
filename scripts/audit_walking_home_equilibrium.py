"""Fixed HOME targets: equilibrium feasibility diagnostic, not walking proof."""
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    import mujoco
    from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
    from experiments.laser.gait import GaitProbe
    from scripts.evaluate_laser import digest
    a.output.mkdir(parents=True, exist_ok=False)
    rows, reports = [], []
    for axis, angle in ((0, 0.), (0, .02), (0, -.02), (1, .02), (1, -.02)):
        world = ConsistentSensorWalkingWorld(ROOT/"receipts/walking/20260905-v3-final/policy.onnx", ROOT/".workspace/bam")
        c = world.core
        quat = np.array([np.cos(angle/2), 0., 0., 0.])
        quat[1+axis] = np.sin(angle/2)
        c.reset([0., 0., .125], quat)
        probe = GaitProbe(c)
        case_rows = []
        try:
            for i in range(250):
                row = probe.sample(world.step_command([0., 0., 0.], action_override=np.zeros(14, np.float32)))
                row["case_id"] = f"axis{axis}-angle{angle}"
                if any(row["action_rad"]):
                    raise ValueError("HOME action changed")
                case_rows.append(row)
                if world.fell:
                    break
            settled = [r for r in case_rows if r["time_s"] >= 3]
            report = {"case_id": case_rows[0]["case_id"], "initial_tilt_rad": angle,
                "duration_s": case_rows[-1]["time_s"], "fell": world.fell,
                "settled_max_tilt_deg": max((r["tilt_deg"] for r in settled), default=None),
                "settled_max_speed_m_s": max((r["speed_m_s"] for r in settled), default=None),
                "minimum_actual_joint_margin_rad": min(r["minimum_actual_joint_margin_rad"] for r in case_rows)}
            reports.append(report)
            rows.extend(case_rows)
            print(json.dumps(report), flush=True)
        finally:
            world.close()
    (a.output/"trajectory.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
    (a.output/"audit.json").write_text(json.dumps({"schema": "microduck.home-equilibrium-diagnostic/v1",
        "cases": reports, "action": "constant 14D zero delta = HOME servo targets", "acceptance_eligible": False,
        "boundary": "Five-second native rigid-model feasibility diagnostic from five initial tilts. Fixed targets are a diagnostic input, never action assistance to a policy. No walking or physical acceptance."}, indent=2)+"\n")
    for name in ("scripts/audit_walking_home_equilibrium.py", "experiments/walking/world.py", "experiments/walking/sensor_world.py", "experiments/laser/gait.py", "evaluator/core.py", "microduck/constants.py"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
