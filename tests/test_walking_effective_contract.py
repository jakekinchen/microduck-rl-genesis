"""Check the inherited command contract without constructing a simulator.

V18's frozen prose mistakenly said 5% stop commands. The actual V2 sampler
and retained V18 run configuration both specify 25%; preserve that behavior.
"""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microduck.walking_controlled_env import MicroduckControlledWalkingEnv
from microduck.walking_env import MicroduckWalkingEnv
from microduck.walking_unbraced_env import MicroduckUnbracedWalkingEnv


class EffectiveWalkingContractTests(unittest.TestCase):
    def test_v18_resolves_to_v2_command_sampler_not_v1(self):
        self.assertIs(MicroduckUnbracedWalkingEnv._resample_twist,
                      MicroduckControlledWalkingEnv._resample_twist)
        self.assertIsNot(MicroduckUnbracedWalkingEnv._resample_twist,
                         MicroduckWalkingEnv._resample_twist)

    def test_effective_command_buckets_bounds_and_resample_interval(self):
        # Stratify choices exactly, including every boundary. This checks the
        # distribution contract deterministically, not a lucky random sample.
        n = 1000
        env = SimpleNamespace(
            device="cpu", twist_cmd=torch.zeros(n, 3),
            is_standing_env=torch.zeros(n, dtype=torch.bool),
            twist_resample_at=torch.zeros(n, dtype=torch.long),
            episode_length_buf=torch.full((n,), 17, dtype=torch.long),
        )
        choices = torch.arange(n, dtype=torch.float32) / n
        signs = (torch.arange(n) % 2).float()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(26090619)
            with patch("torch.rand", side_effect=[choices, signs]) as rng:
                MicroduckUnbracedWalkingEnv._resample_twist(env, torch.arange(n))
            self.assertEqual(rng.call_count, 2)
        moving = env.twist_cmd[:, 0] != 0
        turning = env.twist_cmd[:, 2] != 0
        masks = [moving & ~turning, ~moving & turning,
                 moving & turning, ~moving & ~turning]
        self.assertEqual([int(m.sum()) for m in masks], [400, 250, 100, 250])
        torch.testing.assert_close(env.is_standing_env, masks[-1])
        self.assertTrue(torch.all(env.twist_cmd[:, 1] == 0))
        speed = env.twist_cmd[moving, 0]
        yaw = env.twist_cmd[turning, 2].abs()
        self.assertTrue(torch.all((speed >= .08) & (speed <= .22)))
        self.assertTrue(torch.all((yaw >= .35) & (yaw <= .75)))
        interval = env.twist_resample_at - env.episode_length_buf
        self.assertTrue(torch.all((interval >= 150) & (interval <= 300)))

    def test_v2_metadata_records_effective_distribution(self):
        def initialize_parent(env, num_envs, **kwargs):
            env.cfg = {}
            env.reward_weights = {}

        with patch.object(MicroduckWalkingEnv, "__init__", initialize_parent):
            env = MicroduckControlledWalkingEnv(1)
        self.assertEqual(env.cfg["command_mix"],
                         {"forward": .4, "turn": .25, "arc": .1, "stop": .25})


if __name__ == "__main__":
    unittest.main(verbosity=2)
