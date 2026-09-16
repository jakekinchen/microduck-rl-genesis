"""Curriculum boundaries and genuine parameter sharing under both command modes."""
import copy
import unittest
import numpy as np
import torch
from tensordict import TensorDict
from microduck.velocity_cfg import TRAIN_CFG
from microduck.recipe_actor_v54 import SharedActor,RoutedActor,mode_pools,balanced_indices
from microduck.native_sequence_env_v54 import request_at,next_level,LAYOUTS


class RecipeTests(unittest.TestCase):
    def test_curriculum_requires_outcomes_and_budget_and_advances_once(self):
        self.assertEqual(next_level(0,[True]*8,5999),0)
        self.assertEqual(next_level(0,[True]*5+[False]*3,6000),0)
        self.assertEqual(next_level(0,[True]*6+[False]*2,6000),1)
        self.assertEqual(next_level(1,[True]*8,17999),1)
        self.assertEqual(next_level(1,[True]*8,18000),2)
        self.assertEqual(next_level(0,[True]*8,18000),1)
        self.assertEqual(next_level(2,[True]*8,999999),2)
        self.assertEqual(next_level(1,[True]*7,18000),1)

    def test_actual_zero_commands_and_restarts_in_each_layout(self):
        for level,(width,stop,windows) in enumerate(LAYOUTS):
            for bucket in range(24):
                for window in range(windows):
                    offset=width*window
                    for tick in [0,49,stop,width-1]:
                        np.testing.assert_array_equal(request_at(offset+tick,bucket,0,level),0)
                    for tick in [50,stop-1]:
                        self.assertTrue(np.any(request_at(offset+tick,bucket,0,level)))

    def test_shared_gradients_normalizer_and_balanced_rehearsal(self):
        torch.set_num_threads(1);torch.manual_seed(54)
        raw=torch.randn(16,61);raw[::2,48:51]=0
        obs=TensorDict({'policy':raw},[16])
        cfg=copy.deepcopy(TRAIN_CFG['actor']);cfg.pop('class_name')
        cfg['hidden_dims']=[32,16]
        shared=SharedActor(obs,{'actor':['policy']},'actor',14,**copy.deepcopy(cfg))
        routed=RoutedActor(obs,{'actor':['policy']},'actor',14,**copy.deepcopy(cfg))
        self.assertFalse(hasattr(shared,'walking') or hasattr(shared,'standing'))
        before={k:v.clone() for k,v in shared.state_dict().items() if 'obs_normalizer' in k}
        shared.update_normalization(obs)
        for k,v in before.items(): torch.testing.assert_close(shared.state_dict()[k],v,atol=0,rtol=0)
        for indices in [slice(0,None,2),slice(1,None,2)]:
            shared.zero_grad();shared(obs)[indices].square().sum().backward()
            self.assertTrue(all(p.grad is not None for p in shared.mlp.parameters()))
            self.assertTrue(any(p.grad.abs().sum()>0 for p in shared.mlp.parameters()))
        mean=routed(obs);sample=routed(obs,stochastic_output=True)
        torch.testing.assert_close(routed.get_output_log_prob(sample),
            torch.distributions.Normal(mean,routed.output_std).log_prob(sample).sum(-1))
        indices=balanced_indices(mode_pools(raw),count=11)
        self.assertEqual(int((raw[indices,48:51]==0).all(-1).sum()),11)
        self.assertEqual(len(indices),22)
        with self.assertRaises(ValueError): mode_pools(raw[1::2])


if __name__=='__main__': unittest.main()
