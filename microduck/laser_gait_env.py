"""Physical-face gait-v4: learn stepping, not endpoint-only translation.

No robot/model/actuator edits, scripted joints, IK or action post-filter. The
command adapter and reward/termination contract are explicitly new. Start from
the early first-party baseline, not the hip-stop-exploiting laser lineage.
"""
import math
import torch
from .laser_robust_env import MicroduckLaserRobustEnv
from .velocity_env import MicroduckVelocityEnv

GAIT_CONFIG = {
    "version": "laser-gait-v4", "forward_axis": "body +X; mouth and head-camera site direction, NOT legacy camera optical axis",
    "linear_tracking_std_m_s": .08, "angular_tracking_std_rad_s": .5,
    "recent_step_window_s": 1., "qualified_air_s": [.06, .5],
    "qualified_site_clearance_m": .008, "swing_site_target_m": .015,
    "hard_stop_fraction_of_range": .05, "hard_stop_timeout_s": .5,
    "qpos_penalty_starts_at_fraction_of_half_range": .8,
    "qpos_limit_weight": -4., "loaded_foot_slip_weight": -2.,
    "action_rate_l2_weight": -.1, "pose_weight": .5,
    "curriculum": "face-side narrow targets first; moving full-circle by 300 iterations",
    "boundary": "Reward intervention, not a calibrated simulator or physical acceptance",
}


def face_commands_torch(relative, visible):
    distance = relative.norm(dim=-1)
    bearing = torch.atan2(relative[:, 1], relative[:, 0])
    active = visible & (distance > .18)
    vx = (3*(distance-.18)).clamp(0, .25)*bearing.cos().clamp(min=0)*active
    return torch.stack((vx, torch.zeros_like(vx), (2*bearing).clamp(-1, 1)*active), -1)


def joint_boundary_cost(position, lower, upper):
    ratio = ((position-(lower+upper)/2)/((upper-lower)/2)).abs()
    return ((ratio-.8).clamp(min=0)/.2).square().sum(-1)


class MicroduckLaserGaitEnv(MicroduckLaserRobustEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Laser-Physical-Face-Gait-v4", gait=GAIT_CONFIG,
                        reward_version="gait-v4", reward_weights=dict(self.reward_weights))

    def _build_buffers(self):
        super()._build_buffers()
        mid = (self.soft_limit_lo+self.soft_limit_hi)/2
        half = (self.soft_limit_hi-self.soft_limit_lo)/1.8
        self.gait_limit_lo, self.gait_limit_hi = mid-half, mid+half
        self.last_step_tick = torch.full((self.num_envs, 2), -10000, dtype=torch.long, device=self.device)
        self.valid_landing = torch.zeros((self.num_envs, 2), dtype=torch.bool, device=self.device)
        self.hard_stop_ticks = torch.zeros(self.num_envs, dtype=torch.long, device=self.device)
        self.episode_sums["gait_landing"] = torch.zeros(self.num_envs, device=self.device)

    def _update_laser_commands(self, pos=None, q=None):
        # Parent computes canonical body-frame geometry. Replace only commands.
        super()._update_laser_commands(pos, q)
        self.twist_cmd[:] = face_commands_torch(self.laser_relative, self.laser_visible)

    def _resample_twist(self, env_ids):
        super()._resample_twist(env_ids)
        pos, q = self.robot.get_pos(), self.robot.get_quat()
        yaw = torch.atan2(2*(q[:,0]*q[:,3]+q[:,1]*q[:,2]), 1-2*(q[:,2]**2+q[:,3]**2))
        # A moving target is introduced only after initial positive-vx stepping.
        progress = min(self.common_step_counter/(300*24), 1.)
        span = .25 + (math.pi-.25)*progress
        angle = yaw[env_ids]+torch.empty(len(env_ids), device=self.device).uniform_(-span, span)
        radius = torch.empty(len(env_ids), device=self.device).uniform_(.4, .85)
        radius[torch.rand(len(env_ids), device=self.device)<.12] = .12
        self.laser_xy[env_ids] = pos[env_ids,:2]+radius[:,None]*torch.stack((angle.cos(),angle.sin()), -1)
        self.laser_velocity[env_ids] *= progress
        self._update_laser_commands(pos, q)

    def _apply_curricula(self):
        super()._apply_curricula()
        self.reward_weights.update(track_linear_velocity=5., track_angular_velocity=3.,
                                   upright=3., pose=.5, action_rate_l2=-.1,
                                   dof_pos_limits=-4., foot_slip=-2., head_pose_tracking=1.)

    def _update_contacts(self):
        previous_air = self.feet_air_time.clone()
        super()._update_contacts()
        self.valid_landing = self.first_contact & (previous_air>=.06) & (previous_air<=.5) & (self._peak_at_landing>=.008)
        tick = self.episode_length_buf[:,None]
        self.last_step_tick = torch.where(self.valid_landing, tick, self.last_step_tick)
        margin = torch.minimum(self.dof_pos-self.gait_limit_lo, self.gait_limit_hi-self.dof_pos)/(self.gait_limit_hi-self.gait_limit_lo)
        parked = (margin<.05).any(-1)
        self.hard_stop_ticks = torch.where(parked, self.hard_stop_ticks+1, torch.zeros_like(self.hard_stop_ticks))

    def _gait_credit(self):
        age = (self.episode_length_buf[:,None]-self.last_step_tick)*self.dt
        recent = (age<1.).all(-1)
        # Nonzero exploration signal, but standing/dragging cannot earn the
        # full locomotion score. No phase clock or gait action enters the actor.
        return .15+.85*recent.float()

    def _rew_track_lin(self):
        err = (self.twist_cmd[:,:2]-self.base_lin_vel[:,:2]).square().sum(-1)+self.base_lin_vel[:,2].square()
        score = torch.exp(-err/.08**2)
        return score*torch.where(self._command_active().bool(), self._gait_credit(), torch.ones_like(score))

    def _rew_track_ang(self):
        err = (self.twist_cmd[:,2]-self.base_ang_vel[:,2]).square()+self.base_ang_vel[:,:2].square().sum(-1)
        return torch.exp(-err/.5**2)

    def _rew_dof_pos_limits(self):
        # Mechanical position, not reference target: BAM needs target overshoot
        # under load. Penalize actual hard-stop use rather than clipping actions.
        return joint_boundary_cost(self.dof_pos, self.gait_limit_lo, self.gait_limit_hi)

    def _rew_foot_swing_height(self, active):
        return (((self._peak_at_landing/.015)-1).square()*self.first_contact.float()).sum(-1)*active

    def _compute_rewards(self):
        MicroduckVelocityEnv._compute_rewards(self)
        active = self.laser_visible & (self.laser_distance>.18)
        facing = (self.laser_relative[:,0]/self.laser_distance.clamp(min=1e-6)).clamp(0,1)
        forward = (self.base_lin_vel[:,0]/.25).clamp(-1,1)
        upright = self._rew_upright()
        progress = forward*facing*active*upright*self._gait_credit()
        stop = (~active)*torch.exp(-self.base_lin_vel[:,:2].square().sum(-1)/.01)*upright
        fall = (self.projected_gravity[:,2]>-math.cos(math.radians(70))) | (self.base_pos[:,2]<.07)
        landing = self.valid_landing.float().sum(-1)*active*upright
        for name, value in {"laser_progress":4*progress*self.dt, "laser_stop":stop*self.dt,
                            "laser_fall":-5*fall.float(), "gait_landing":4*landing*self.dt}.items():
            self.rew_buf += torch.nan_to_num(value, nan=0., posinf=0., neginf=0.)
            self.episode_sums[name] += value

    def _check_termination(self):
        super()._check_termination()
        if not self.demo:
            self.reset_buf |= self.hard_stop_ticks>round(.5/self.dt)

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        self.last_step_tick[env_ids] = -10000
        self.valid_landing[env_ids] = False
        self.hard_stop_ticks[env_ids] = 0
