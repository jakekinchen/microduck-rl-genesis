"""Default-update equivalence on synthetic batches with the pinned RSL imports.

This is not an on-robot test or a reproduction of a training run.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
import numpy as np
import torch

AVAILABLE = (importlib.util.find_spec('rsl_rl') is not None
             and importlib.util.find_spec('tensordict') is not None)


@unittest.skipUnless(AVAILABLE, 'pinned RSL-RL/TensorDict unavailable in this sandbox')
class UpdateParityTests(unittest.TestCase):
    def test_default_candidate_matches_frozen_update(self):
        from tensordict import TensorDict
        from microduck.recipe_actor_v54 import RecipePPO, mode_pools
        from microduck.recipe_ppo_review import ReviewPPO

        class Actor(torch.nn.Module):
            is_recurrent=False
            def __init__(self):
                super().__init__(); self.net=torch.nn.Linear(61,14)
            def forward(self,obs,stochastic_output=False):
                mean=self.net(obs['policy'])
                if stochastic_output:
                    self.dist=torch.distributions.Normal(mean,torch.ones_like(mean)*.1)
                    return self.dist.sample()
                return mean
            def get_output_log_prob(self,actions):return self.dist.log_prob(actions).sum(-1)

        class Critic(torch.nn.Module):
            def __init__(self):super().__init__();self.net=torch.nn.Linear(61,1)
            def forward(self,obs):return self.net(obs['policy'])

        class Storage:
            def __init__(self,batch):self.batch=batch;self.cleared=False
            def mini_batch_generator(self,*args):yield self.batch;yield self.batch
            def clear(self):self.cleared=True

        torch.manual_seed(13)
        policy=torch.randn(8,61);policy[:4,48:51]=0
        obs=TensorDict({'policy':policy,'flat_retention':torch.tensor([[True],[False]]*4)},[8])
        actor,critic=Actor(),Critic();actor(obs,stochastic_output=True)
        actions=actor(obs).detach()+.01
        batch=NS(observations=obs,actions=actions,masks=None,
                 old_actions_log_prob=actor.get_output_log_prob(actions).detach()[:,None],
                 advantages=torch.linspace(-1,1,8)[:,None],values=critic(obs).detach(),
                 returns=critic(obs).detach()+torch.linspace(-.5,.5,8)[:,None])
        del actor.dist
        outputs=[]
        with tempfile.TemporaryDirectory() as tmp:
            for candidate in (False,True):
                a,c=copy.deepcopy(actor),copy.deepcopy(critic)
                # Detach cached distributions before deepcopying modules elsewhere.
                alg=NS(actor=a,critic=c,rnd=None,symmetry=None,is_multi_gpu=False,schedule='fixed',
                       entropy_coef=0.,num_mini_batches=1,num_learning_epochs=1,clip_param=.2,
                       use_clipped_value_loss=True,value_loss_coef=1.,max_grad_norm=1.,
                       teacher=copy.deepcopy(a).requires_grad_(False),
                       replay_obs=policy.clone(),replay_actions=actor(obs).detach(),
                       replay_pools=mode_pools(policy),storage=Storage(batch),
                       online_coef=1.,replay_coef=1.,replay_sampling='mode',
                       update_index=0,diag_every=1,diag_path=Path(tmp)/'diagnostics.jsonl')
                alg.optimizer=torch.optim.Adam(list(a.parameters())+list(c.parameters()),lr=3e-5)
                torch.manual_seed(99)
                losses=(ReviewPPO.update if candidate else RecipePPO.update)(alg)
                self.assertTrue(alg.storage.cleared)
                outputs.append((copy.deepcopy(a.state_dict()),copy.deepcopy(c.state_dict()),losses,torch.get_rng_state()))
            for i in (0,1):
                for name in outputs[0][i]:self.assertTrue(torch.equal(outputs[0][i][name],outputs[1][i][name]),name)
            self.assertTrue(torch.equal(outputs[0][3],outputs[1][3]))
            for key in outputs[0][2]:self.assertEqual(outputs[0][2][key],outputs[1][2][key])
            record=json.loads((Path(tmp)/'diagnostics.jsonl').read_text())
            self.assertIn('surrogate/online_retention',record['gradient_cosine'])
            self.assertEqual(sum(g['rows'] for g in record['groups'].values()),8)


if __name__=='__main__':unittest.main()
