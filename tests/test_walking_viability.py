"""Reward composition must not change the actual control or physical contract."""
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
from microduck.walking_balance_env import MicroduckBalancedWalkingEnv
from microduck.walking_yaw_bias_env import (
    MicroduckYawBiasWalkingEnv, update_yaw_bias, yaw_bias_cost,
)
from microduck.walking_viability_env import (
    MicroduckViableWalkingEnv, posture_viability, positive_walking_return,
)
from scripts.train_walking_viability import verified_initializer
from scripts.evaluate_laser import digest


class ViabilityTests(unittest.TestCase):
    def test_yaw_filter_distinguishes_bias_from_four_hz_wobble(self):
        value = torch.zeros(3, dtype=torch.float64)
        samples = []
        for i in range(1000):
            wobble = .3 * math.sin(2 * math.pi * 4 * i * .02)
            value = update_yaw_bias(value, torch.tensor([wobble, .1, wobble + .1]), .02)
            if i >= 500:
                samples.append(value.clone())
        costs = yaw_bias_cost(torch.stack(samples)).mean(0)
        self.assertLess(float(costs[0]), .1)
        self.assertAlmostEqual(float(costs[1]), 1.9, places=4)
        self.assertAlmostEqual(float(costs[2]), 1.9, places=3)

    def test_head_average_uses_absolute_error_not_signed_cancellation(self):
        value = torch.zeros(2, 4)
        for i in range(1000):
            error = torch.zeros(2, 4)
            error[:, 0] = torch.tensor([.25, .6]) * math.sin(2 * math.pi * 4 * i * .02)
            value = update_yaw_bias(value, error.abs(), .02)
        gate = posture_viability(value, torch.tensor([[0., 0., -1.]]).repeat(2, 1))
        self.assertAlmostEqual(float(gate[0]), 1., places=6)
        self.assertLess(float(gate[1]), .5)

    def test_gate_bounds_and_non_compensatory_head_and_trunk(self):
        heads = torch.zeros(4, 4, dtype=torch.float64)
        heads[:, 0] = torch.tensor([0., .2, .4, 1.])
        gravity = torch.tensor([[0., 0., -1.]], dtype=torch.float64).repeat(4, 1)
        gate = posture_viability(heads, gravity)
        torch.testing.assert_close(gate[:2], torch.ones(2, dtype=torch.float64))
        self.assertAlmostEqual(float(gate[2]), math.exp(-1), places=6)
        self.assertLess(float(gate[3]), 1e-6)
        gravity[:] = torch.tensor([math.sin(math.radians(30)), 0, -math.cos(math.radians(30))])
        self.assertLess(float(posture_viability(heads[:1], gravity[:1])[0]), 1e-6)

    def test_action_observation_physics_reset_sampling_unchanged(self):
        for name in ("step", "_build_scene", "_build_actuator", "_refresh_state", "_update_contacts",
                     "_compute_observations", "reset_idx", "_check_termination", "_resample_twist",
                     "_apply_curricula", "_startup_randomization"):
            self.assertIs(getattr(MicroduckViableWalkingEnv, name), getattr(MicroduckBalancedWalkingEnv, name))

    def test_yaw_reward_reset_does_not_retain_previous_episode(self):
        env = object.__new__(MicroduckYawBiasWalkingEnv)
        env.episode_length_buf = torch.tensor([1, 3])
        env.walking_yaw_bias_ema = torch.tensor([7., .1])
        env.base_ang_vel = torch.zeros(2, 3)
        env.twist_cmd = torch.zeros(2, 3)
        env.dt = .02
        env.rew_buf = torch.tensor([2., -3.])
        env.episode_sums = {k: torch.zeros(2) for k in ("yaw_bias_cost", "absolute_yaw_bias_rad_s")}
        with patch.object(MicroduckBalancedWalkingEnv, "_compute_rewards"):
            env._compute_rewards()
        self.assertEqual(float(env.walking_yaw_bias_ema[0]), 0.)
        self.assertEqual(float(env.rew_buf[0]), 2.)
        self.assertLess(float(env.rew_buf[1]), -3.)

    def test_viability_only_removes_positive_return_and_resets_head_history(self):
        env = object.__new__(MicroduckViableWalkingEnv)
        env.episode_length_buf = torch.tensor([1, 50])
        env.walking_head_absolute_ema = torch.ones(2, 4)
        env.projected_gravity = torch.tensor([[0., 0., -1.]]).repeat(2, 1)
        env.dt = .02
        env.rew_buf = torch.tensor([-.2, -.2])
        env.episode_sums = {k: torch.zeros(2) for k in
                            ("posture_gate_cost", "posture_viability", "ungated_positive_return")}
        env._head_pose_error = lambda: torch.zeros(2, 4)
        with patch.object(MicroduckYawBiasWalkingEnv, "_compute_rewards"), \
                patch("microduck.walking_viability_env.positive_walking_return", return_value=torch.ones(2)):
            env._compute_rewards()
        self.assertTrue(torch.equal(env.walking_head_absolute_ema[0], torch.zeros(4)))
        self.assertAlmostEqual(float(env.rew_buf[0]), -.2, places=6)
        self.assertLess(float(env.rew_buf[1]), -1.19)

    def test_unknown_positive_term_fails_closed(self):
        env = object.__new__(MicroduckViableWalkingEnv)
        env.reward_weights = {"new_unhandled_reward": 1.}
        with self.assertRaisesRegex(ValueError, "unhandled positive"):
            positive_walking_return(env)


class ViableTrainingAdmissionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.receipt = self.root / "receipts/walking/20260905-v8-training-complete"
        self.receipt.mkdir(parents=True)
        self.checkpoint = self.receipt / "model_999.pt"
        self.checkpoint.write_bytes(b"synthetic admission fixture; never executed")
        self.record = {"status": "completed", "variant": "walking-v8", "checkpoint": "model_999.pt",
                       "new_transitions": 24_576_000, "checkpoint_sha256": digest(self.checkpoint), "source_sha256": {}}
        (self.receipt / "training.json").write_text(json.dumps(self.record))
        identity = patch("scripts.train_walking_viability.V8_FINAL_CHECKPOINT_SHA256", digest(self.checkpoint))
        identity.start()
        self.addCleanup(identity.stop)
        self.folders = []
        for suffix in ("old-regression", "final", "current-sensor"):
            folder = self.root / "receipts/walking" / f"20260905-v8-{suffix}"
            folder.mkdir()
            self.folders.append(folder)
            (folder / "training.json").write_text(json.dumps(self.record))
            (folder / "trajectory.jsonl").write_text("synthetic fixture; not rollout data\n")
            (folder / "policy.onnx").write_bytes(b"synthetic identity; never executed")
            (folder / "evaluation.json").write_text(json.dumps({"total_cases": 21, "case_reports": [{}] * 21,
                                                               "policy_sha256": digest(folder / "policy.onnx")}))
            heading = folder.with_name(folder.name + "-heading")
            heading.mkdir()
            (heading / "evaluation.json").write_text(json.dumps({
                "total_cases": 21, "case_reports": [{}] * 21, "combined_passed_cases": 0,
                "checkpoint_sha256": digest(self.checkpoint), "policy_sha256": digest(folder / "policy.onnx"),
                "input_sha256": {name: digest(folder / name) for name in ("evaluation.json", "trajectory.jsonl")}}))
            (folder / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(folder.iterdir())))

    def test_complete_retained_final_admitted(self):
        checkpoint, _, evidence = verified_initializer(self.root)
        self.assertEqual(checkpoint, self.checkpoint)
        self.assertEqual(len(evidence), 6)

    def test_intermediate_or_incomplete_final_rejected(self):
        self.record["checkpoint"] = "model_500.pt"
        (self.receipt / "training.json").write_text(json.dumps(self.record))
        with self.assertRaisesRegex(ValueError, "full completed v8 final"):
            verified_initializer(self.root)

    def test_changed_input_trajectory_rejected(self):
        (self.folders[0] / "trajectory.jsonl").write_text("tampered")
        with self.assertRaisesRegex(ValueError, "manifest mismatch"):
            verified_initializer(self.root)

    def test_heading_for_different_final_rejected(self):
        path = self.folders[0].with_name(self.folders[0].name + "-heading") / "evaluation.json"
        value = json.loads(path.read_text())
        value["checkpoint_sha256"] = "wrong"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "declared v8 final"):
            verified_initializer(self.root)

    def test_no_intervention_when_all_combined_gates_pass(self):
        for folder in self.folders:
            path = folder.with_name(folder.name + "-heading") / "evaluation.json"
            value = json.loads(path.read_text())
            value["combined_passed_cases"] = 21
            path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "not needed"):
            verified_initializer(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
