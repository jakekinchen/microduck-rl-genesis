"""V21: stronger instantaneous yaw tracking, with V18 physics unchanged."""
import torch
from .walking_unbraced_env import MicroduckUnbracedWalkingEnv


def additional_yaw_cost(angular_velocity, command):
    # Same deadband and scale as V5; double only its yaw-error coefficient.
    # Zero commanded twist retains the independently trained V15 STOP behavior.
    moving = torch.any(command != 0, dim=-1)
    return ((angular_velocity[:, 2] - command[:, 2]).abs() - .05).clamp_min(0) / .20 * moving


class MicroduckYawRefinementEnv(MicroduckUnbracedWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Instantaneous-Yaw-v21", walking_version="v21",
                        additional_yaw_error_weight=-2., additional_yaw_deadband_rad_s=.05,
                        additional_yaw_scale_rad_s=.20, additional_yaw_scope="nonzero twist commands only",
                        inherited_physics_and_commands="V18 unchanged")

    def _build_buffers(self):
        super()._build_buffers()
        self.episode_sums["additional_yaw_error_cost"] = torch.zeros(self.num_envs, device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        value = -2 * additional_yaw_cost(self.base_ang_vel, self.twist_cmd) * self.dt
        self.rew_buf += value
        self.episode_sums["additional_yaw_error_cost"] += value
