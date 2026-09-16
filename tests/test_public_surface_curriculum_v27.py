import unittest
from types import SimpleNamespace
from unittest.mock import patch
import torch
from microduck.public_surface_curriculum_v27 import probabilities, ConservativeSurfaceWalkingEnv


class CurriculumTests(unittest.TestCase):
    def test_stage_boundaries_and_nominal_retention(self):
        self.assertEqual(probabilities(1999),(.8,.2,0.,0.))
        self.assertEqual(probabilities(2000),(.6,.3,.1,0.))
        self.assertEqual(probabilities(4000),(.5,.3,.2,0.))
        for i in [0,1999,2000,3999,4000,5999]:
            p=probabilities(i)
            self.assertAlmostEqual(sum(p),1.)
            self.assertGreaterEqual(p[0],.5)
            self.assertEqual(p[3],0.)

    def test_applied_subset_reset_does_not_accumulate_origins(self):
        env = SimpleNamespace(device="cpu", common_step_counter=4000,
            env_origins=torch.full((5, 3), 99.), surface_resets=torch.zeros(4, dtype=torch.long))
        ids = torch.tensor([0, 2, 4])
        with patch("microduck.public_surface_curriculum_v27.torch.rand", return_value=torch.tensor([.1, .6, .9])):
            ConservativeSurfaceWalkingEnv._terrain_curriculum(env, ids)
            first = env.env_origins.clone()
            ConservativeSurfaceWalkingEnv._terrain_curriculum(env, ids)
        torch.testing.assert_close(first, env.env_origins)
        torch.testing.assert_close(first[ids], torch.tensor([[0.,0.,0.],[0.,16.,0.],[0.,32.,0.]]))
        torch.testing.assert_close(first[[1,3]], torch.full((2,3), 99.))
        self.assertEqual(env.surface_resets.tolist(), [2,2,2,0])
