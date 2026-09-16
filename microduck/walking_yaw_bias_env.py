"""Reward-only low-frequency yaw-error component on balanced v8.

The EMA is privileged reward state. It never enters the deployed observation,
command, policy action, actuator or simulator. Normal gait wobble remains
subject to the unchanged instantaneous tracking and motor gates.
"""
import math
import torch
from .walking_balance_env import MicroduckBalancedWalkingEnv

YAW_BIAS_TAU_S = 1.
YAW_BIAS_DEADBAND_RAD_S = .005
YAW_BIAS_SCALE_RAD_S = .05
YAW_BIAS_WEIGHT = -2.


def update_yaw_bias(previous, error, dt):
    alpha = -math.expm1(-dt / YAW_BIAS_TAU_S)
    return previous + alpha * (error - previous)


def yaw_bias_cost(bias):
    return (bias.abs() - YAW_BIAS_DEADBAND_RAD_S).clamp_min(0.) / YAW_BIAS_SCALE_RAD_S


class MicroduckYawBiasWalkingEnv(MicroduckBalancedWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Low-Frequency-Yaw-Component", walking_version="v9-component",
                        yaw_bias_tau_s=YAW_BIAS_TAU_S,
                        yaw_bias_deadband_rad_s=YAW_BIAS_DEADBAND_RAD_S,
                        yaw_bias_scale_rad_s=YAW_BIAS_SCALE_RAD_S,
                        yaw_bias_weight=YAW_BIAS_WEIGHT,
                        yaw_bias_scope="reward only; current body gyro error; all commands")

    def _build_buffers(self):
        super()._build_buffers()
        self.walking_yaw_bias_ema = torch.zeros(self.num_envs, device=self.device)
        for name in ("yaw_bias_cost", "absolute_yaw_bias_rad_s"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        # reset_idx's parent clears the episode counter; do not modify its
        # physical state, random population or delay-history initialization.
        previous = torch.where(self.episode_length_buf <= 1,
                               torch.zeros_like(self.walking_yaw_bias_ema),
                               self.walking_yaw_bias_ema)
        error = self.base_ang_vel[:, 2] - self.twist_cmd[:, 2]
        self.walking_yaw_bias_ema = update_yaw_bias(previous, error, self.dt)
        value = YAW_BIAS_WEIGHT * yaw_bias_cost(self.walking_yaw_bias_ema) * self.dt
        self.rew_buf += value
        self.episode_sums["yaw_bias_cost"] += value
        self.episode_sums["absolute_yaw_bias_rad_s"] += self.walking_yaw_bias_ema.abs() * self.dt
