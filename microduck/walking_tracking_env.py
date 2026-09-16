"""Walking v5: command error remains costly outside bounded reward peaks."""
import torch
from .walking_ground_env import MicroduckGroundAlignedWalkingEnv


def command_error_cost(velocity, angular_velocity, command):
    linear = ((velocity[:, :2]-command[:, :2]).abs()-.01).clamp_min(0)/.05
    yaw = ((angular_velocity[:, 2]-command[:, 2]).abs()-.05).clamp_min(0)/.20
    return linear.sum(-1)+yaw


class MicroduckTrackingWalkingEnv(MicroduckGroundAlignedWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Command-Tracking-v5", walking_version="v5",
            command_error_cost_weight=-2., command_error_deadbands=[.01, .01, .05],
            command_error_scales=[.05, .05, .20],
            floor_collision_masks=[1, 1])

    def _build_buffers(self):
        super()._build_buffers()
        self.episode_sums["command_error_cost"] = torch.zeros(self.num_envs, device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        value = -2*command_error_cost(self.base_lin_vel, self.base_ang_vel, self.twist_cmd)*self.dt
        self.rew_buf += value
        self.episode_sums["command_error_cost"] += value
