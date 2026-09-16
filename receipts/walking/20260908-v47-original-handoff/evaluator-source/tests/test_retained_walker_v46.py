import copy
import unittest
import numpy as np
import torch
from tensordict import TensorDict
from microduck.retained_walker_v46 import RetainedWalkerActor
from microduck.native_sequence_env_v46 import joint_margin_cost,BUCKETS
from microduck.velocity_cfg import TRAIN_CFG

class RetainedWalkerTests(unittest.TestCase):
    def test_fixed_standing_has_no_noise_or_parameter_gradient(self):
        torch.set_num_threads(1)
        obs=TensorDict({'policy':torch.randn(8,61)},[8]);obs['policy'][:,48:51]=0
        cfg=copy.deepcopy(TRAIN_CFG['actor']);cfg.pop('class_name')
        model=RetainedWalkerActor(obs,{'actor':['policy']},'actor',14,**cfg)
        exact=model.standing(obs)
        first=model(obs,stochastic_output=True)
        torch.testing.assert_close(first,exact,rtol=0,atol=0)
        torch.testing.assert_close(model(obs,stochastic_output=True),first,rtol=0,atol=0)
        model.get_output_log_prob(first).sum().backward()
        self.assertTrue(all(p.grad is None or not p.grad.any() for p in model.walking.parameters()))
        self.assertTrue(all(not p.requires_grad and p.grad is None for p in model.standing.parameters()))
        self.assertTrue(all(not p.requires_grad for p in model.teacher.parameters()))
        obs['policy'][:,48]=.1
        sample=model(obs,stochastic_output=True)
        self.assertFalse(torch.equal(sample,model.walking(obs)))

    def test_margin_penalty_acts_before_gate_and_is_range_normalized(self):
        limits=np.array([[0.,2.],[0.,4.]])
        self.assertEqual(joint_margin_cost(np.array([.2,.4]),limits),0.)
        a=joint_margin_cost(np.array([.12,.24]),limits)
        b=joint_margin_cost(np.array([.08,.16]),limits)
        self.assertGreater(a,0.);self.assertGreater(b,a)
        self.assertAlmostEqual(a,joint_margin_cost(np.array([.24,.48]),limits*2))
        self.assertEqual(len(BUCKETS),12)
        self.assertEqual({(b[3],b[4]) for b in BUCKETS},{(4,1),(0,0),(6,1)})

if __name__=='__main__':unittest.main()
