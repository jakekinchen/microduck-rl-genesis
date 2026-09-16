from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from microduck.walking_yaw_refinement_env import MicroduckYawRefinementEnv, additional_yaw_cost
from microduck.walking_unbraced_env import MicroduckUnbracedWalkingEnv


class YawRefinementTests(unittest.TestCase):
    def test_turning_tracks_requested_yaw_instead_of_suppressing_turns(self):
        cmd = torch.tensor([[0.,0.,.5], [0.,0.,-.5], [.2,0.,0.]])
        self.assertTrue(torch.equal(additional_yaw_cost(cmd, cmd), torch.zeros(3)))
        wrong = cmd.clone(); wrong[:,2] = -cmd[:,2]
        self.assertTrue(torch.all(additional_yaw_cost(wrong, cmd)[:2] > 0))

    def test_stop_and_deadband_and_both_signs(self):
        cmd = torch.tensor([[0.,0.,0.], [.2,0.,0.], [.2,0.,0.], [.2,0.,0.]])
        gyro = torch.zeros_like(cmd); gyro[:,2] = torch.tensor([1.,.04,.25,-.25])
        torch.testing.assert_close(additional_yaw_cost(gyro,cmd), torch.tensor([0.,0.,1.,1.]))

    def test_cost_is_additive_even_when_parent_reward_is_negative(self):
        env = object.__new__(MicroduckYawRefinementEnv)
        env.base_ang_vel = torch.tensor([[0.,0.,.25]])
        env.twist_cmd = torch.tensor([[.2,0.,0.]])
        env.dt = .02
        env.rew_buf = torch.tensor([-3.])
        env.episode_sums = {"additional_yaw_error_cost":torch.zeros(1)}
        with patch.object(MicroduckUnbracedWalkingEnv, "_compute_rewards"):
            MicroduckYawRefinementEnv._compute_rewards(env)
        torch.testing.assert_close(env.rew_buf, torch.tensor([-3.04]))
        torch.testing.assert_close(env.episode_sums["additional_yaw_error_cost"], torch.tensor([-.04]))

    def test_physics_actions_timing_and_reset_are_inherited(self):
        for name in ("step", "_build_scene", "_build_actuator", "_resample_twist",
                     "reset_idx", "_compute_observations", "_update_contacts", "_check_termination"):
            self.assertIs(getattr(MicroduckYawRefinementEnv, name), getattr(MicroduckUnbracedWalkingEnv, name))


if __name__ == "__main__":
    unittest.main()
