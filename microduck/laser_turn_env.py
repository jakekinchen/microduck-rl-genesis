"""Versioned correction for measured turn-in-place stagnation in robust-v1."""
import torch
from .laser_robust_env import MicroduckLaserRobustEnv, ROBUST_CONFIG

TURN_CONFIG = dict(ROBUST_CONFIG, version="laser-turn-v2",
                   correction="gate linear credit on yaw tracking; emphasize actual commanded yaw progress",
                   angular_tracking_weight=12., linear_tracking_weight=3.,
                   pose_weight=.2, action_rate_l2_weight=-.01, yaw_progress_weight=4.)


class MicroduckLaserTurnEnv(MicroduckLaserRobustEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Laser-Dynamic-Turn-v2", robustness=TURN_CONFIG,
                        reward_weights=dict(self.reward_weights))

    def _build_buffers(self):
        super()._build_buffers()
        self.episode_sums["laser_yaw_progress"] = torch.zeros(self.num_envs, device=self.device)

    def _apply_curricula(self):
        super()._apply_curricula()
        self.reward_weights.update(track_angular_velocity=12., track_linear_velocity=3.,
                                   pose=.2, action_rate_l2=-.01)

    def _rew_track_lin(self):
        score = super()._rew_track_lin()
        yaw_error = (self.twist_cmd[:, 2]-self.base_ang_vel[:, 2]).square()
        yaw_gate = .15+.85*torch.exp(-yaw_error/.25)
        return score*torch.where(self.twist_cmd[:, 2].abs()>.35, yaw_gate, torch.ones_like(score))

    def _compute_rewards(self):
        super()._compute_rewards()
        command = self.twist_cmd[:, 2]
        # Velocity measured from the robot, not a difference of moving target bearings.
        progress = (self.base_ang_vel[:, 2]*command.sign()).clamp(-1, 1)
        progress *= (command.abs()>.35)*self._rew_upright()
        value = torch.nan_to_num(4*progress*self.dt, nan=0., posinf=0., neginf=0.)
        self.rew_buf += value
        self.episode_sums["laser_yaw_progress"] += value
