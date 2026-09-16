"""Command-error cost distinguishes wrong tracking and persists past stop caps."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from microduck.walking_tracking_env import command_error_cost, MicroduckTrackingWalkingEnv


class TrackingWalkingTests(unittest.TestCase):
    def test_fresh_bank_preserves_all_commands_timing_and_numerical_gates(self):
        import json
        old = json.loads((ROOT/"experiments/walking/suite-v1.json").read_text())
        new = json.loads((ROOT/"experiments/walking/tracking-suite-v1.json").read_text())
        for key in ("thresholds", "timing_profiles", "duration_s", "move_start_s", "stop_start_s"):
            self.assertEqual(old[key], new[key])
        for a, b in zip(old["cases"], new["cases"]):
            self.assertEqual(a["command"], b["command"])
            self.assertNotEqual(a["yaw"], b["yaw"])
        self.assertNotEqual(old["seed"], new["seed"])

    def test_correct_command_and_deadband_have_zero_extra_cost(self):
        command = torch.tensor([[.12, 0., .5], [0., 0., 0.]])
        v = torch.tensor([[.12, 0., 0.], [.005, -.005, 0.]])
        w = torch.tensor([[0., 0., .5], [0., 0., .02]])
        self.assertTrue(torch.equal(command_error_cost(v, w, command), torch.zeros(2)))

    def test_wrong_turn_and_straight_drift_cost_more(self):
        c = torch.tensor([[.12, 0., .5]]).repeat(3, 1)
        v = torch.tensor([[.12, 0., 0.]]).repeat(3, 1)
        w = torch.tensor([[0., 0., .5], [0., 0., 0.], [0., 0., -.5]])
        cost = command_error_cost(v, w, c)
        self.assertTrue(bool((cost[1:] > cost[:-1]).all()))
        c.zero_()
        self.assertGreater(float(command_error_cost(v, w, c)[0]), 0.)

    def test_stop_cost_does_not_flatten_at_large_motion(self):
        c = torch.zeros(3, 3)
        v = torch.tensor([[.1, 0., 0.], [.2, 0., 0.], [.4, 0., 0.]])
        w = torch.tensor([[0., 0., .4], [0., 0., .8], [0., 0., 1.6]])
        cost = command_error_cost(v, w, c)
        self.assertTrue(bool((cost[1:] > cost[:-1]).all()))

    def test_intervention_does_not_override_actions_observations_or_commands(self):
        for name in ("step", "_compute_observations", "_resample_twist", "reset_idx", "_build_actuator"):
            self.assertNotIn(name, MicroduckTrackingWalkingEnv.__dict__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
