"""Genesis laser-goal locomotion curriculum, preserving the 61D/14D interface.

Privileged simulated spot geometry drives a NON-learned command generator.
PPO learns all fourteen joint actions with BAM physics, without IK or action
assistance. This is not an end-to-end visual policy or a hardware controller.
"""
from __future__ import annotations

import math
import torch
from .velocity_env import MicroduckVelocityEnv
from .laser_task import STOP_RADIUS_M, MAX_FORWARD_M_S, MAX_YAW_RAD_S


class MicroduckLaserEnv(MicroduckVelocityEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, task_name="Laser-Follow-Oracle-v1", **kwargs)
        self.cfg.update(target_source="simulated-ground-truth", reward_version="laser-v1",
                        reward_weights=dict(self.reward_weights),
                        stop_radius_m=STOP_RADIUS_M,
                        laser_reward_weights={"robot_progress": 4.0, "settled_stop": 1.0,
                                              "fall_event": -5.0})

    def _build_buffers(self):
        super()._build_buffers()
        self.laser_xy = torch.zeros((self.num_envs, 2), device=self.device)
        self.laser_velocity = torch.zeros_like(self.laser_xy)
        self.laser_visible = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        self.laser_relative = torch.zeros_like(self.laser_xy)
        self.laser_distance = torch.ones(self.num_envs, device=self.device)
        for name in ("laser_progress", "laser_stop", "laser_fall"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _resample_twist(self, env_ids):
        n = len(env_ids)
        pos, q = self.robot.get_pos(), self.robot.get_quat()
        yaw = torch.atan2(2*(q[:, 0]*q[:, 3] + q[:, 1]*q[:, 2]),
                          1-2*(q[:, 2]**2 + q[:, 3]**2))
        span = math.radians(45 if self.common_step_counter < 300*24 else 110)
        angle = yaw[env_ids] + torch.empty(n, device=self.device).uniform_(-span, span)
        distance = torch.empty(n, device=self.device).uniform_(0.3, 0.9)
        self.laser_xy[env_ids] = pos[env_ids, :2] + distance[:, None] * torch.stack(
            (torch.cos(angle), torch.sin(angle)), dim=-1)
        self.laser_visible[env_ids] = torch.rand(n, device=self.device) >= 0.1
        self.laser_velocity[env_ids] = 0
        if self.common_step_counter >= 400*24:
            self.laser_velocity[env_ids] = torch.empty((n, 2), device=self.device).uniform_(-0.04, 0.04)
        self.twist_resample_at[env_ids] = self.episode_length_buf[env_ids] + int(5/self.dt)
        self._update_laser_commands(pos, q)

    def _resample_pose_cmd(self, env_ids, buf, ranges, at_buf, resample_s):
        buf[env_ids] = 0
        at_buf[env_ids] = self.episode_length_buf[env_ids] + int(5/self.dt)

    def _update_laser_commands(self, pos=None, q=None):
        pos = self.base_pos if pos is None else pos
        q = self.base_quat if q is None else q
        yaw = torch.atan2(2*(q[:, 0]*q[:, 3] + q[:, 1]*q[:, 2]),
                          1-2*(q[:, 2]**2 + q[:, 3]**2))
        delta = self.laser_xy - pos[:, :2]
        self.laser_relative = torch.stack((torch.cos(yaw)*delta[:, 0] + torch.sin(yaw)*delta[:, 1],
                                          -torch.sin(yaw)*delta[:, 0] + torch.cos(yaw)*delta[:, 1]), dim=-1)
        self.laser_distance = self.laser_relative.norm(dim=-1)
        bearing = torch.atan2(self.laser_relative[:, 1], self.laser_relative[:, 0])
        active = self.laser_visible & (self.laser_distance > STOP_RADIUS_M)
        self.twist_cmd[:, 0] = (1.5*(self.laser_distance-STOP_RADIUS_M)).clamp(0, MAX_FORWARD_M_S) * torch.cos(bearing).clamp(min=0) * active
        self.twist_cmd[:, 1] = 0
        self.twist_cmd[:, 2] = (2*bearing).clamp(-MAX_YAW_RAD_S, MAX_YAW_RAD_S) * active
        self.is_standing_env = ~active
        self.head_cmd.zero_()
        self.body_cmd.zero_()

    def _resample_due_commands(self):
        if not self.demo:
            self.laser_xy += self.laser_velocity * self.dt
            due = (self.episode_length_buf >= self.twist_resample_at).nonzero().flatten()
            if len(due):
                self._resample_twist(due)
        self._update_laser_commands()

    def _apply_curricula(self):
        super()._apply_curricula()
        self.reward_weights.update(track_linear_velocity=5.0, track_angular_velocity=2.0,
                                   upright=3.0, pose=0.5, head_pose_bias=0.0)

    def _maybe_push(self):
        # First learn target pursuit; retain startup/episode DR and BAM delays.
        # External perturbation robustness is a separate, unclaimed stage.
        return

    def _compute_rewards(self):
        super()._compute_rewards()
        direction = self.laser_relative / self.laser_distance.clamp(min=1e-6)[:, None]
        # Robot velocity only: a moving/teleported target cannot earn progress.
        # World velocity rotated by yaw, consistent with the ground-plane goal.
        q = self.base_quat
        yaw = torch.atan2(2*(q[:, 0]*q[:, 3]+q[:, 1]*q[:, 2]), 1-2*(q[:, 2]**2+q[:, 3]**2))
        v = self.robot.get_vel()
        vxy = torch.stack((torch.cos(yaw)*v[:, 0]+torch.sin(yaw)*v[:, 1],
                           -torch.sin(yaw)*v[:, 0]+torch.cos(yaw)*v[:, 1]), dim=-1)
        active = self.laser_visible & (self.laser_distance > STOP_RADIUS_M)
        upright = self._rew_upright()
        progress = ((vxy*direction).sum(-1)/MAX_FORWARD_M_S).clamp(-1, 1) * active * upright
        stop = (~active) * torch.exp(-vxy.square().sum(-1)/0.01) * upright
        fall = (self.projected_gravity[:, 2] > -math.cos(math.radians(70))) | (self.base_pos[:, 2] < 0.07)
        for name, value in {"laser_progress": 4*progress*self.dt,
                            "laser_stop": stop*self.dt, "laser_fall": -5*fall.float()}.items():
            self.rew_buf += torch.nan_to_num(value, nan=0, posinf=0, neginf=0)
            self.episode_sums[name] += value

    def _check_termination(self):
        super()._check_termination()
        if not self.demo:
            self.reset_buf |= self.base_pos[:, 2] < 0.07

    def _compute_observations(self):
        self._update_laser_commands()
        return super()._compute_observations()
