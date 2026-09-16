import copy
import unittest
import torch
from tensordict import TensorDict
from microduck.retained_stander_v48 import RetainedStanderActor
from microduck.native_sequence_env_v48 import BUCKETS, request_at
from microduck.velocity_cfg import TRAIN_CFG


class RetainedStanderTests(unittest.TestCase):
    def test_walking_is_deterministic_frozen_and_ignores_optimizer_label(self):
        torch.set_num_threads(1)
        obs = TensorDict({'policy':torch.randn(8,61), 'flat_retention':torch.ones(8,1,dtype=torch.bool)}, [8])
        obs['policy'][:,48:51] = .1
        cfg = copy.deepcopy(TRAIN_CFG['actor']); cfg.pop('class_name')
        model = RetainedStanderActor(obs, {'actor':['policy']}, 'actor', 14, **cfg)
        expected = model.walking(obs)
        actual = model(obs, stochastic_output=True)
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)
        model.get_output_log_prob(actual).sum().backward()
        self.assertTrue(all(not p.requires_grad and p.grad is None for p in model.walking.parameters()))
        self.assertTrue(all(p.grad is None or not p.grad.any() for p in model.standing.parameters()))
        obs['flat_retention'][:] = False
        torch.testing.assert_close(model(obs), expected, rtol=0, atol=0)
        obs['policy'][:,48:51] = 0
        self.assertFalse(torch.equal(model(obs, stochastic_output=True), model.standing(obs)))
        self.assertTrue(all(not p.requires_grad for p in model.teacher.parameters()))

    def test_declared_cells_and_stop_restart_requests(self):
        self.assertEqual(len(BUCKETS),24)
        self.assertEqual({(b[3],b[4],b[5]) for b in BUCKETS},
                         {(m,s,y) for m,s in [(4,1),(0,0),(6,1)] for y in [0.,.12]})
        for bucket in range(24):
            self.assertTrue(request_at(650,bucket,0).tolist() == [0.,0.,0.])
            self.assertTrue(request_at(899,bucket,0).tolist() == [0.,0.,0.])
            self.assertTrue(request_at(950,bucket,0).any())


if __name__ == '__main__':
    unittest.main()
