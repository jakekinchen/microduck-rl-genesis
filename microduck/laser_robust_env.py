"""Second-stage pursuit curriculum: changing targets and bounded physical DR.

New subclass, not a mutation of the frozen September 4 training task. Targets
are still privileged coordinates; no visual generalization is implied.
"""
import math
import torch
from .laser_env import MicroduckLaserEnv
from .bam_actuator import DelayBuffer

ROBUST_CONFIG = {
    "version": "laser-robust-v1", "ground": "flat",
    "foot_friction_ratio": [.55, 1.45], "trunk_mass_ratio": [.9, 1.1],
    "motor_kp_ratio": [.9, 1.1], "motor_electrical_damping_ratio": [.9, 1.1],
    "motor_friction_ratio": [.8, 1.2], "trunk_com_m": .006, "head_com_m": .004,
    "imu_delay_control_steps": [0, 2], "joint_velocity_delay_control_steps": [1, 2],
    "target_speed_m_s": [.02, .12], "target_resample_s": [2, 6],
    "dropout_s": [.3, 1.2], "push_interval_s": [4, 8], "push_max_delta_v_m_s": .10,
    "push_ramp_iterations": [100, 250], "approach_gain_s_inv": 3.,
    "inherited": "6 degree IMU mounting error, encoder bias, observation noise, armature DR and BAM delays",
}


class MicroduckLaserRobustEnv(MicroduckLaserEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Laser-Dynamic-Robust-v1", robustness=ROBUST_CONFIG,
                        reward_weights=dict(self.reward_weights))

    def _build_buffers(self):
        super()._build_buffers()
        self.hide_until = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.target_turn_rate = torch.zeros(self.num_envs, device=self.device)
        if not self.demo:
            self.obs_delays = {
                k: DelayBuffer((self.num_envs, dim), lo, 2, 64, device=self.device)
                for k, dim, lo in (("base_ang_vel", 3, 0), ("projected_gravity", 3, 0), ("joint_vel", 14, 1))
            }

    def _startup_randomization(self):
        super()._startup_randomization()
        if self.demo:
            return
        n, d = self.num_envs, self.device
        sample = lambda shape, a, b: torch.empty(shape, device=d).uniform_(a, b)
        self.robot.set_friction_ratio(sample((n, 1), .55, 1.45).repeat(1, len(self.foot_link_idx)),
                                      links_idx_local=self.foot_link_idx)
        mass = float(self.robot.links[self.trunk_idx].inertial_mass)
        self.robot.set_mass_shift(mass*(sample((n, 1), .9, 1.1)-1), links_idx_local=[self.trunk_idx])
        self.bam.kp_scale[:] = sample(self.bam.kp_scale.shape, .9, 1.1)
        self.bam.kd_scale[:] = sample(self.bam.kd_scale.shape, .9, 1.1)
        self._cache_link_inertials()

    def _apply_curricula(self):
        super()._apply_curricula()
        self.com_range, self.head_com_range = .006, .004
        self.reward_weights["track_angular_velocity"] = 3.0

    def _resample_twist(self, env_ids):
        n, d = len(env_ids), self.device
        pos, q = self.robot.get_pos(), self.robot.get_quat()
        yaw = torch.atan2(2*(q[:, 0]*q[:, 3]+q[:, 1]*q[:, 2]), 1-2*(q[:, 2]**2+q[:, 3]**2))
        span = math.pi * (.6 + .4*min(self.common_step_counter/(100*24), 1))
        angle = yaw[env_ids] + torch.empty(n, device=d).uniform_(-span, span)
        radius = torch.empty(n, device=d).uniform_(.30, .85)
        radius[torch.rand(n, device=d)<.10] = .12
        self.laser_xy[env_ids] = pos[env_ids, :2] + radius[:, None]*torch.stack((angle.cos(), angle.sin()), -1)
        heading = torch.empty(n, device=d).uniform_(-math.pi, math.pi)
        speed = torch.empty(n, device=d).uniform_(.02, .12)
        speed[torch.rand(n, device=d)<.35] = 0
        self.laser_velocity[env_ids] = speed[:, None]*torch.stack((heading.cos(), heading.sin()), -1)
        self.target_turn_rate[env_ids] = torch.empty(n, device=d).uniform_(-.7, .7)
        self.twist_resample_at[env_ids] = self.episode_length_buf[env_ids] + torch.empty(n, device=d).uniform_(2, 6).div(self.dt).long()
        self.hide_until[env_ids] = self.episode_length_buf[env_ids]
        self.laser_visible[env_ids] = True
        self._update_laser_commands(pos, q)

    def _update_laser_commands(self, pos=None, q=None):
        super()._update_laser_commands(pos, q)
        bearing = torch.atan2(self.laser_relative[:, 1], self.laser_relative[:, 0])
        active = self.laser_visible & (self.laser_distance > .18)
        self.twist_cmd[:, 0] = (3*(self.laser_distance-.18)).clamp(0, .25)*bearing.cos().clamp(min=0)*active

    def _resample_due_commands(self):
        if self.demo:
            self._update_laser_commands()
            return
        angle = self.target_turn_rate*self.dt
        x, y = self.laser_velocity[:, 0].clone(), self.laser_velocity[:, 1].clone()
        self.laser_velocity[:, 0] = angle.cos()*x-angle.sin()*y
        self.laser_velocity[:, 1] = angle.sin()*x+angle.cos()*y
        self.laser_xy += self.laser_velocity*self.dt
        due = (self.episode_length_buf >= self.twist_resample_at).nonzero().flatten()
        if len(due):
            self._resample_twist(due)
        hide = (torch.rand(self.num_envs, device=self.device)<.002).nonzero().flatten()
        self.hide_until[hide] = self.episode_length_buf[hide] + torch.empty(len(hide), device=self.device).uniform_(.3, 1.2).div(self.dt).long()
        self.laser_visible = self.episode_length_buf >= self.hide_until
        self._update_laser_commands()

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        if not self.demo and len(env_ids):
            self.bam.set_friction_scale(env_ids, torch.empty((len(env_ids), 1), device=self.device).uniform_(.8, 1.2))
            self.push_at[env_ids] = torch.empty(len(env_ids), device=self.device).uniform_(4, 8).div(self.dt).long()

    def _maybe_push(self):
        if self.demo:
            return
        due = (self.episode_length_buf >= self.push_at).nonzero().flatten()
        if not len(due):
            return
        strength = .1*min(max((self.common_step_counter/24-100)/150, 0), 1)
        velocity = self.robot.get_vel()[due].clone()
        velocity[:, :2] += torch.empty((len(due), 2), device=self.device).uniform_(-strength, strength)
        self.robot.set_dofs_velocity(velocity, dofs_idx_local=[0, 1, 2], envs_idx=due)
        self.push_at[due] = self.episode_length_buf[due] + torch.empty(len(due), device=self.device).uniform_(4, 8).div(self.dt).long()
