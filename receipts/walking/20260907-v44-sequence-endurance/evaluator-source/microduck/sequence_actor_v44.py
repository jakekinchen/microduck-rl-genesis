"""Two compatible MLP actors, one PPO distribution routed by raw command."""
import copy
import torch
from torch import nn
from torch.distributions import Normal
from rsl_rl.models import MLPModel
from rsl_rl.modules.distribution import GaussianDistribution


class SequenceActor(MLPModel):
    def __init__(self, obs, obs_groups, obs_set, output_dim, **kwargs):
        nn.Module.__init__(self)
        self.obs_groups = obs_groups[obs_set]
        self.obs_dim = 61
        self.walking = MLPModel(obs, obs_groups, obs_set, output_dim, **copy.deepcopy(kwargs))
        self.standing = MLPModel(obs, obs_groups, obs_set, output_dim, **copy.deepcopy(kwargs))
        # Inherited probability and KL interfaces operate on the selected Normal.
        self.distribution = GaussianDistribution(output_dim, learn_std=False)

    def forward(self, obs, masks=None, hidden_state=None, stochastic_output=False):
        if masks is not None:
            raise ValueError('V44 is a nonrecurrent, unpadded PPO experiment')
        stand = (obs['policy'][..., 48:51] == 0).all(-1, keepdim=True)
        wm, sm = self.walking(obs), self.standing(obs)
        mean = torch.where(stand, sm, wm)
        if not stochastic_output:
            return mean
        wd, sd = self.walking.distribution, self.standing.distribution
        wd.update(wm)
        sd.update(sm)
        self.distribution._distribution = Normal(mean, torch.where(stand, sd.std, wd.std))
        return self.distribution.sample()

    def update_normalization(self, obs):
        # Preserve the separately learned parent coordinate systems. Updating
        # both with mixed standing/moving populations changes the policy itself.
        pass
