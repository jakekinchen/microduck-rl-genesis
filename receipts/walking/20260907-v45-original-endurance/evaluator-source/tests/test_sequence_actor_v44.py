"""Meaningful routing/probability/gradient checks for joint PPO and reset ABI."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
import torch
from tensordict import TensorDict
from rsl_rl.models import MLPModel
from microduck.sequence_actor_v44 import SequenceActor
from microduck.velocity_cfg import TRAIN_CFG
from microduck.native_sequence_env_v44 import request_at

ROOT=Path(__file__).resolve().parents[1]

class SequenceActorTests(unittest.TestCase):
    def test_parents_routing_probability_and_gradients(self):
        torch.set_num_threads(1)
        raw=torch.randn(12,61);raw[::2,48:51]=0
        raw[1,48:51]=torch.tensor([1e-9,0,0])
        obs=TensorDict({'policy':raw},[12]);cfg=copy.deepcopy(TRAIN_CFG['actor']);cfg.pop('class_name')
        actor=SequenceActor(obs,{'actor':['policy']},'actor',14,**copy.deepcopy(cfg))
        for role,run in [('walking','walking-20260906-v21'),('standing','standing-20260906-v15')]:
            folder=ROOT/'logs'/run;meta=json.loads((folder/'run.json').read_text())
            getattr(actor,role).load_state_dict(torch.load(folder/meta['checkpoint'],weights_only=True,map_location='cpu')['actor_state_dict'])
        before={key:v.clone() for key,v in actor.state_dict().items()}
        actor.update_normalization(obs)
        for key,value in before.items():torch.testing.assert_close(actor.state_dict()[key],value,rtol=0,atol=0)
        mean=actor(obs)
        torch.testing.assert_close(mean[::2],actor.standing(obs)[::2],rtol=0,atol=0)
        torch.testing.assert_close(mean[1::2],actor.walking(obs)[1::2],rtol=0,atol=0)
        sampled=actor(obs,stochastic_output=True)
        expected=torch.distributions.Normal(mean,actor.output_std)
        torch.testing.assert_close(actor.get_output_log_prob(sampled),expected.log_prob(sampled).sum(-1))
        torch.testing.assert_close(actor.output_entropy,expected.entropy().sum(-1))
        old=actor.output_distribution_params
        torch.testing.assert_close(actor.get_kl_divergence(old,old),torch.zeros(12),atol=1e-5,rtol=0)
        actor.zero_grad();mean[::2].sum().backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in actor.standing.mlp.parameters()))
        self.assertTrue(all(p.grad is None or p.grad.abs().sum()==0 for p in actor.walking.mlp.parameters()))

    def test_continuous_command_phases(self):
        for b in range(4):
            for step in [0,49,650,899,900,949,1550,1799]:np.testing.assert_array_equal(request_at(step,b,0),0)
            for step in [50,649,950,1549,1850,2449]:self.assertTrue(np.any(request_at(step,b,0)))
        self.assertFalse(np.array_equal(request_at(50,0,0),request_at(950,0,0)))

if __name__=='__main__':unittest.main()
