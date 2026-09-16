import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.walking.heading import evaluate_heading
from scripts.evaluate_walking_heading import verify_input_manifest
from scripts.evaluate_laser import digest


def trajectory(rate, requested=0., initial=2.9):
    rows = []
    for i in range(551):
        yaw = initial + rate * i * .02
        rows.append({"time_s": 2 + i * .02, "command": [0, 0, requested],
                     "qpos": [0, 0, .125, math.cos(yaw/2), 0, 0, math.sin(yaw/2)] + [0] * 14})
    return rows


class HeadingFidelityTests(unittest.TestCase):
    def test_small_persistent_yaw_error_is_not_straight_walking(self):
        result = evaluate_heading(trajectory(math.radians(35)/11))
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["metrics"]["endpoint_heading_error_deg"], 35.)

    def test_left_and_right_turns_cross_angle_wrap_without_false_failure(self):
        for rate in (-.5, .5):
            result = evaluate_heading(trajectory(rate, requested=rate))
            self.assertTrue(result["passed"])
            self.assertLess(result["metrics"]["maximum_heading_error_deg"], 1e-10)

    def test_static_robot_cannot_pass_turn_command(self):
        self.assertFalse(evaluate_heading(trajectory(0, requested=.5))["passed"])

    def test_absolute_initial_heading_is_not_an_error(self):
        for initial in (-2.9, 0, 2.9):
            self.assertTrue(evaluate_heading(trajectory(0, initial=initial))["passed"])

    def test_absent_nonfinite_mistimed_or_invalid_quaternion_fails_closed(self):
        for change in (lambda r: r.pop(),
                       lambda r: r[2]["qpos"].__setitem__(0, float("nan")),
                       lambda r: r[2].__setitem__("time_s", 2.03),
                       lambda r: r[2]["qpos"].__setitem__(3, 2.)):
            rows = trajectory(0)
            change(rows)
            self.assertFalse(evaluate_heading(rows)["passed"])

    def test_manifest_must_cover_every_consumed_evidence_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = [root / name for name in
                     ("training.json", "evaluation.json", "trajectory.jsonl", "policy.onnx")]
            for path in files:
                path.write_bytes(b"synthetic identity fixture; never executed")
            manifest = root / "SHA256SUMS"
            manifest.write_text("".join(f"{digest(path)}  {path.name}\n" for path in files[:3]))
            with self.assertRaisesRegex(ValueError, "cover all required"):
                verify_input_manifest(root)
            manifest.write_text("".join(f"{digest(path)}  {path.name}\n" for path in files))
            verify_input_manifest(root)
            files[0].write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                verify_input_manifest(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
