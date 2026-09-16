from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from types import SimpleNamespace
import torch
from microduck.standing_env import summed_internal_force, standing_load_delta, MicroduckStandingEnv


class StandingRewardTests(unittest.TestCase):
    def test_valid_internal_force_magnitudes_sum_once(self):
        c = {"force_a": torch.tensor([[[3., 4., 0.], [0., 0., 100.]], [[0., 0., 2.], [0., 0., 3.]]]),
             "valid_mask": torch.tensor([[True, False], [True, True]])}
        torch.testing.assert_close(summed_internal_force(c), torch.tensor([5., 5.]))

    def test_empty_internal_contacts(self):
        c = {"force_a": torch.zeros(3, 0, 3), "valid_mask": torch.zeros(3, 0, dtype=torch.bool)}
        torch.testing.assert_close(summed_internal_force(c), torch.zeros(3))

    def test_no_load_leaves_all_parent_reward_unchanged(self):
        result = standing_load_delta(torch.ones(3), torch.tensor([0., .5, 1.]), torch.tensor([0., .25, .5]), .02)
        torch.testing.assert_close(result, torch.zeros(3))

    def test_gate_composition_retains_penalties(self):
        positive = torch.tensor([.1, .2, .3])
        posture = torch.tensor([0., .4, 1.])
        force = torch.tensor([.5, 1., 5.])
        negative = torch.tensor([-.1, -.02, -.4])
        excess = (force-.5).clamp_min(0)
        actual = posture*positive + negative + standing_load_delta(positive, posture, force, .02)
        expected = torch.exp(-(excess/.5).square())*posture*positive + negative - 2*excess*.02
        torch.testing.assert_close(actual, expected)

    def test_only_selected_environments_get_zero_command(self):
        env = SimpleNamespace(twist_cmd=torch.ones(4,3), is_standing_env=torch.zeros(4,dtype=torch.bool),
                              twist_resample_at=torch.zeros(4,dtype=torch.long), episode_length_buf=torch.arange(4))
        MicroduckStandingEnv._resample_twist(env, torch.tensor([1,3]))
        torch.testing.assert_close(env.twist_cmd[[1,3]], torch.zeros(2,3))
        torch.testing.assert_close(env.twist_cmd[[0,2]], torch.ones(2,3))
        self.assertEqual(env.twist_resample_at.tolist(), [0,251,0,253])


if __name__ == "__main__":
    unittest.main()
