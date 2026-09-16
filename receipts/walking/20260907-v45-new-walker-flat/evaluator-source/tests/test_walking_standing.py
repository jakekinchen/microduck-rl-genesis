import unittest
from unittest.mock import patch
import numpy as np
from experiments.walking.self_load import evaluate_self_load
from experiments.walking.standing_world import standing_command, StandingSwitchWalkingWorld


class LoadGateTests(unittest.TestCase):
    def samples(self):
        return [{"interval_start_s": i*.005, "total_normal_n": 0., "largest_pair_normal_n": 0.}
                for i in range(3600)]

    def test_zero_load_passes(self):
        self.assertTrue(evaluate_self_load(self.samples())["passed"])

    def test_missing_terminal_stop_fails(self):
        self.assertIn("incomplete_duration", evaluate_self_load(self.samples()[:2996])["failures"])
        self.assertFalse(evaluate_self_load([])["passed"])

    def test_bracing_rejected_without_penetration(self):
        s = self.samples()
        for row in s[3200:]:
            row.update(total_normal_n=14., largest_pair_normal_n=6.)
        r = evaluate_self_load(s)
        self.assertIn("continuous_body_bracing", r["failures"])
        self.assertIn("sustained_self_load_occupancy", r["failures"])

    def test_fragmented_load_occupancy(self):
        s = self.samples()
        for row in s[::50]:
            row.update(total_normal_n=2., largest_pair_normal_n=1.)
        self.assertIn("sustained_self_load_occupancy", evaluate_self_load(s)["failures"])

    def test_continuous_limit_and_short_transient(self):
        s = self.samples()
        for row in s[100:110]:
            row.update(total_normal_n=2., largest_pair_normal_n=1.)
        self.assertTrue(evaluate_self_load(s)["passed"])
        s[110].update(total_normal_n=2., largest_pair_normal_n=1.)
        self.assertIn("continuous_body_bracing", evaluate_self_load(s)["failures"])

    def test_bad_load_or_time_rejected(self):
        for field, value in (("total_normal_n", float("nan")), ("largest_pair_normal_n", -1.),
                             ("interval_start_s", 1.), ("largest_pair_normal_n", 1.)):
            s = self.samples()
            s[0][field] = value
            self.assertFalse(evaluate_self_load(s)["passed"])


class StandingSwitchTests(unittest.TestCase):
    def test_exact_zero_only(self):
        self.assertTrue(standing_command([0, 0, 0]))
        for command in ([.001, 0, 0], [0, -.001, 0], [0, 0, .001]):
            self.assertFalse(standing_command(command))
        with self.assertRaises(ValueError):
            standing_command([float("nan"), 0, 0])

    def test_switch_preserves_previous_raw_action_and_command(self):
        from types import SimpleNamespace
        from experiments.walking.heading_servo_world import HeadingServoWalkingWorld
        world = object.__new__(StandingSwitchWalkingWorld)
        world.core = SimpleNamespace(policy=None)
        world.standing_policy, world.walking_policy = object(), object()
        world.last_action = np.arange(14, dtype=np.float32)
        before = world.last_action.tobytes()
        with patch.object(HeadingServoWalkingWorld, "step_command", return_value={}) as step:
            for command, policy, mode in (([0, 0, 0], world.standing_policy, "standing"),
                                          ([.12, 0, 0], world.walking_policy, "walking"),
                                          ([0, 0, 0], world.standing_policy, "standing")):
                self.assertEqual(world.step_command(command)["actor_mode"], mode)
                self.assertIs(world.core.policy, policy)
                self.assertEqual(world.last_action.tobytes(), before)
                step.assert_called_with(command, None)


if __name__ == "__main__":
    unittest.main()
