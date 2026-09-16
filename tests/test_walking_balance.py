"""Separate torso-lean objective, preserving v6 dynamics and action interface."""
import math
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from microduck.walking_contact_env import MicroduckContactTrackingWalkingEnv
from microduck.walking_balance_env import (
    MicroduckBalancedWalkingEnv, TRUNK_LEAN_WEIGHT, trunk_lean_cost, trunk_lean_radians,
)
from scripts.train_walking_balance import verified_initializer
from scripts.evaluate_laser import digest


def gravity(degrees):
    angles = torch.tensor(degrees, dtype=torch.float64) * math.pi / 180
    return torch.stack((angles.sin(), torch.zeros_like(angles), -angles.cos()), -1)


class WalkingBalanceTests(unittest.TestCase):
    def test_deadband_and_non_saturating_large_lean(self):
        got = -TRUNK_LEAN_WEIGHT * trunk_lean_cost(gravity([0, 5, 10, 15, 30, 60, 180]))
        want = torch.tensor([0, 0, 0, 5, 20, 50, 170], dtype=torch.float64) * math.pi / 9
        torch.testing.assert_close(got, want, atol=1e-12, rtol=1e-12)
        self.assertTrue(torch.isfinite(got).all())

    def test_roll_pitch_sign_and_axis_do_not_change_tilt(self):
        g = gravity([0, 10, 35, 90, 179])
        torch.testing.assert_close(trunk_lean_radians(g), trunk_lean_radians(g * torch.tensor([-1, 1, 1])))
        torch.testing.assert_close(trunk_lean_radians(g), trunk_lean_radians(g[:, [1, 0, 2]]))

    def test_reward_adds_exact_cost_and_telemetry_without_mutating_state(self):
        env = object.__new__(MicroduckBalancedWalkingEnv)
        env.projected_gravity = gravity([0, 30])
        before = env.projected_gravity.clone()
        env.dt = .02
        env.rew_buf = torch.tensor([2., 3.], dtype=torch.float64)
        env.episode_sums = {name: torch.zeros(2, dtype=torch.float64)
                            for name in ("trunk_lean_cost", "trunk_lean_rad")}
        with patch.object(MicroduckContactTrackingWalkingEnv, "_compute_rewards") as parent:
            env._compute_rewards()
        parent.assert_called_once_with()
        cost = TRUNK_LEAN_WEIGHT * trunk_lean_cost(before) * .02
        torch.testing.assert_close(env.rew_buf, torch.tensor([2., 3.], dtype=torch.float64) + cost)
        torch.testing.assert_close(env.episode_sums["trunk_lean_cost"], cost)
        torch.testing.assert_close(env.episode_sums["trunk_lean_rad"], trunk_lean_radians(before) * .02)
        self.assertTrue(torch.equal(env.projected_gravity, before))

    def test_physics_action_observation_timing_and_reset_unchanged(self):
        for name in ("step", "_build_scene", "_build_actuator", "_compute_observations",
                     "reset_idx", "_check_termination", "_resample_twist", "_apply_curricula"):
            self.assertIs(getattr(MicroduckBalancedWalkingEnv, name),
                          getattr(MicroduckContactTrackingWalkingEnv, name))


class BalancedTrainingAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.receipt = self.root / "receipts/walking/20260905-v6-training-complete"
        self.receipt.mkdir(parents=True)
        self.checkpoint = self.receipt / "model_1499.pt"
        self.checkpoint.write_bytes(b"synthetic admission test fixture; never executed")
        self.record = {"status": "completed", "variant": "walking-v6",
                       "checkpoint": "model_1499.pt", "new_transitions": 36_864_000,
                       "checkpoint_sha256": digest(self.checkpoint), "source_sha256": {}}
        identity = patch("scripts.train_walking_balance.V6_FINAL_CHECKPOINT_SHA256", digest(self.checkpoint))
        identity.start()
        self.addCleanup(identity.stop)
        self.write_record()
        for name in ("20260905-v6-old-regression", "20260905-v6-final", "20260905-v6-current-sensor"):
            folder = self.root / "receipts/walking" / name
            folder.mkdir()
            (folder / "training.json").write_text(json.dumps(self.record))
            (folder / "policy.onnx").write_bytes(b"synthetic ONNX identity fixture; never executed")
            (folder / "evaluation.json").write_text(json.dumps({
                "policy_sha256": digest(folder / "policy.onnx"), "total_cases": 21,
                "case_reports": [{}] * 21, "passed_cases": 0}))

    def write_record(self):
        (self.receipt / "training.json").write_text(json.dumps(self.record))

    def test_retained_final_with_complete_negative_evaluations_can_initialize(self):
        checkpoint, prior, evidence = verified_initializer(self.root)
        self.assertEqual(checkpoint, self.checkpoint)
        self.assertEqual(prior["checkpoint_sha256"], digest(self.checkpoint))
        self.assertEqual(len(evidence), 3)

    def test_interrupted_or_smoke_records_cannot_initialize(self):
        for key, value in (("status", "running"), ("checkpoint", "model_750.pt"),
                           ("new_transitions", 7680)):
            original = self.record[key]
            self.record[key] = value
            self.write_record()
            with self.assertRaisesRegex(ValueError, "full completed v6 final"):
                verified_initializer(self.root)
            self.record[key] = original

    def test_tampered_checkpoint_rejected(self):
        self.checkpoint.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            verified_initializer(self.root)

    def test_incomplete_evaluation_rejected(self):
        path = self.root / "receipts/walking/20260905-v6-final/evaluation.json"
        data = json.loads(path.read_text())
        data["case_reports"].pop()
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "complete exposed evaluations"):
            verified_initializer(self.root)

    def test_unnecessary_intervention_rejected_when_all_old_protocols_pass(self):
        for path in self.root.glob("receipts/walking/*/evaluation.json"):
            data = json.loads(path.read_text())
            data["passed_cases"] = 21
            path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "not needed"):
            verified_initializer(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
