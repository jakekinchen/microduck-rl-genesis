"""Walking v8: explicitly price trunk lean, not exact HOME leg targets.

This is a separate reward intervention on v6's native-contact environment.
It does not alter physics, actions, observations, sampling or termination.
"""
import math
import torch
from .walking_contact_env import MicroduckContactTrackingWalkingEnv

TRUNK_LEAN_DEADBAND_RAD = math.radians(10.)
TRUNK_LEAN_WEIGHT = -20.


def trunk_lean_radians(projected_gravity):
    """0..pi, including inverted states; no Gaussian saturation or XY ambiguity."""
    return torch.atan2(projected_gravity[:, :2].norm(dim=-1), -projected_gravity[:, 2])


def trunk_lean_cost(projected_gravity):
    return (trunk_lean_radians(projected_gravity) - TRUNK_LEAN_DEADBAND_RAD).clamp_min(0.)


class MicroduckBalancedWalkingEnv(MicroduckContactTrackingWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Balanced-Trunk-v8", walking_version="v8",
                        trunk_lean_deadband_rad=TRUNK_LEAN_DEADBAND_RAD,
                        trunk_lean_weight=TRUNK_LEAN_WEIGHT,
                        trunk_lean_scope="all commands including stopping; true current state")

    def _build_buffers(self):
        super()._build_buffers()
        for name in ("trunk_lean_cost", "trunk_lean_rad"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        value = TRUNK_LEAN_WEIGHT * trunk_lean_cost(self.projected_gravity) * self.dt
        self.rew_buf += value
        self.episode_sums["trunk_lean_cost"] += value
        self.episode_sums["trunk_lean_rad"] += trunk_lean_radians(self.projected_gravity) * self.dt
