from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from types import SimpleNamespace
import torch
from microduck.walking_unbraced_env import MicroduckUnbracedWalkingEnv
from microduck.walking_persistent_contact_env import MicroduckPersistentCompleteWalkingEnv
from microduck.standing_env import standing_load_delta


class UnbracedWalkingTests(unittest.TestCase):
    def test_commands_and_actions_are_inherited_unchanged(self):
        for name in ("_resample_twist", "_compute_observations", "step", "_build_actuator", "_check_termination"):
            self.assertIs(getattr(MicroduckUnbracedWalkingEnv, name),
                          getattr(MicroduckPersistentCompleteWalkingEnv, name))

    def test_moving_and_standing_commands_both_remain_present(self):
        torch.manual_seed(26090618)
        env = SimpleNamespace(device="cpu", twist_cmd=torch.zeros(2048,3),
              is_standing_env=torch.zeros(2048,dtype=torch.bool),
              twist_resample_at=torch.zeros(2048,dtype=torch.long),
              episode_length_buf=torch.zeros(2048,dtype=torch.long))
        MicroduckUnbracedWalkingEnv._resample_twist(env, torch.arange(2048))
        self.assertGreater(torch.count_nonzero(env.twist_cmd[:,0]).item(), 0)
        self.assertGreater(torch.count_nonzero(env.twist_cmd[:,2]).item(), 0)
        self.assertGreater(env.is_standing_env.sum().item(), 0)
        self.assertTrue(torch.all(env.twist_cmd[env.is_standing_env] == 0))

    def test_load_penalty_cannot_reward_or_erase_penalties(self):
        positive = torch.tensor([.1,.3,.5])
        posture = torch.tensor([1.,.5,0.])
        delta = standing_load_delta(positive,posture,torch.tensor([0.,1.,3.]),.02)
        self.assertTrue(torch.all(delta <= 0))
        self.assertEqual(delta[0].item(),0.)
        self.assertLess(delta[2].item(),0.)


if __name__ == "__main__":
    unittest.main()
