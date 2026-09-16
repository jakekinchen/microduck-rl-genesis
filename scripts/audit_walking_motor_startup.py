"""Isolate motor-delay startup history in native closed-loop development."""
import argparse
from collections import deque
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class FirstTargetFill:
    """Training DelayBuffer semantics: fill initial history on its first call."""
    def __init__(self, ticks):
        self.ticks = ticks
        self.history = None

    def step(self, target):
        import numpy as np
        if self.history is None:
            self.history = deque([np.array(target, copy=True) for _ in range(self.ticks)])
        self.history.append(np.array(target, copy=True))
        return self.history.popleft()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import numpy as np
    from experiments.walking.world import WalkingWorld
    from experiments.walking.posture import evaluate_case
    from experiments.laser.gait import GaitProbe
    from scripts.evaluate_laser import digest
    a.output.mkdir(parents=True, exist_ok=False)
    suite = json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
    reports = []
    for fill in ("home", "first-target"):
        for case in (suite["cases"][1], suite["cases"][3]):
            name = f'{fill}--{case["id"]}'
            world = WalkingWorld(a.receipt/"policy.onnx", ROOT/".workspace/bam", motor_ticks=4, sensor_ticks=1, yaw=case["yaw"], seed=suite["seed"])
            if fill == "first-target":
                world.motor_delay = FirstTargetFill(4)
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
                report["startup_history"] = fill
                reports.append(report)
                (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
                np.save(a.output/f"{name}-actions-float32.npy", np.asarray(actions, np.float32))
                print(json.dumps({k: v for k, v in report.items() if k != "gait"}), flush=True)
            finally:
                world.close()
    result = {"schema": "microduck.motor-history-feedback-ablation/v1", "cases": reports,
        "policy_sha256": digest(a.receipt/"policy.onnx"), "acceptance_eligible": False,
        "boundary": "Closed-loop ablation changes only motor FIFO initial history, not its later lag. Policy bytes, command, nominal physics and thresholds are unchanged. Feedback actions can differ; this is not fixed-action replay or physical startup calibration."}
    (a.output/"audit.json").write_text(json.dumps(result, indent=2)+"\n")
    for name in ("scripts/audit_walking_motor_startup.py", "microduck/bam_actuator.py", "experiments/walking/world.py", "experiments/walking/posture.py", "experiments/walking/metrics.py", "experiments/walking/suite-v1.json"):
        dest = a.output/"source"/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, dest)
    (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file()))


if __name__ == "__main__":
    main()
