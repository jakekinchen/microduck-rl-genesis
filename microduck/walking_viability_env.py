"""Walking v9: posture conditions positive return; steering bias stays costly.

All v8 physical, action, observation, command and termination paths are inherited.
This changes objective composition, not the robot to make a video look better.
"""
import math
import torch
from .walking_yaw_bias_env import MicroduckYawBiasWalkingEnv, update_yaw_bias
from .walking_balance_env import trunk_lean_radians
from .walking_env import lift_score
from .walking_controlled_env import landing_quality

HEAD_MEAN_FREE_RAD = .20
HEAD_MEAN_SCALE_RAD = .20
TRUNK_FREE_RAD = math.radians(10.)
TRUNK_SCALE_RAD = math.radians(5.)
POSITIVE_RATE_METHODS = {
    "track_linear_velocity": "_rew_track_lin",
    "track_angular_velocity": "_rew_track_ang",
    "upright": "_rew_upright",
    "pose": "_rew_pose",
    "head_pose_tracking": "_rew_head_pose_tracking",
}


def posture_viability(head_mean_absolute_error, projected_gravity):
    head = ((head_mean_absolute_error.amax(-1) - HEAD_MEAN_FREE_RAD)
            .clamp_min(0.) / HEAD_MEAN_SCALE_RAD)
    trunk = ((trunk_lean_radians(projected_gravity) - TRUNK_FREE_RAD)
             .clamp_min(0.) / TRUNK_SCALE_RAD)
    return torch.exp(-head.square() - trunk.square())


def positive_walking_return(env):
    """Exactly the positive v8 reward terms, before any v9 gate.

    Refuse an unhandled positive parent term instead of silently under-gating.
    No term here mutates state; the air event is the shaped v2 landing reward.
    """
    allowed = set(POSITIVE_RATE_METHODS) | {"air_time"}
    unexpected = {k for k, v in env.reward_weights.items() if v > 0 and k not in allowed}
    if unexpected:
        raise ValueError(f"unhandled positive parent rewards: {unexpected}")
    result = torch.zeros_like(env.rew_buf)
    for name, method in POSITIVE_RATE_METHODS.items():
        result += max(env.reward_weights[name], 0.) * getattr(env, method)() * env.dt
    active = env._command_active()
    upright = env._rew_upright()
    result += max(env.reward_weights["air_time"], 0.) * env._rew_air_time(active) * env.dt
    result += 4 * lift_score(env.sole_height, env.feet_air_time, env.contact) * active * upright * env.dt
    result += .6 * (env.valid_landing.float() * landing_quality(env.landing_air)).sum(-1) * active * upright
    return result


class MicroduckViableWalkingEnv(MicroduckYawBiasWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Posture-Conditioned-Return-v9", walking_version="v9",
                        positive_reward_gate="exp(-head_mean_excess^2 - trunk_excess^2)",
                        head_mean_tau_s=1., head_mean_free_rad=HEAD_MEAN_FREE_RAD,
                        head_mean_scale_rad=HEAD_MEAN_SCALE_RAD,
                        gate_trunk_free_rad=TRUNK_FREE_RAD, gate_trunk_scale_rad=TRUNK_SCALE_RAD,
                        negative_rewards="all inherited penalties plus low-frequency yaw cost remain ungated")

    def _build_buffers(self):
        super()._build_buffers()
        self.walking_head_absolute_ema = torch.zeros((self.num_envs, 4), device=self.device)
        for name in ("posture_gate_cost", "posture_viability", "ungated_positive_return"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        previous = torch.where((self.episode_length_buf <= 1)[:, None],
                               torch.zeros_like(self.walking_head_absolute_ema),
                               self.walking_head_absolute_ema)
        self.walking_head_absolute_ema = update_yaw_bias(previous, self._head_pose_error().abs(), self.dt)
        viability = posture_viability(self.walking_head_absolute_ema, self.projected_gravity)
        positive = positive_walking_return(self)
        value = -(1 - viability) * positive
        self.rew_buf += value
        self.episode_sums["posture_gate_cost"] += value
        self.episode_sums["posture_viability"] += viability * self.dt
        self.episode_sums["ungated_positive_return"] += positive
