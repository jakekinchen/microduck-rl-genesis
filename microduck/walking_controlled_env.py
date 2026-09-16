"""Walking v2: controlled steps, all-substep effort feedback and practiced stops.

Versioned reward-only correction. The actuator return value and physics loop
are unchanged; torque recording observes all four existing BAM calls.
"""
import torch
from .walking_env import MicroduckWalkingEnv


def landing_quality(air_time):
    return torch.exp(-((air_time-.16)/.06).square())


def effort_cost(torque, limit):
    """[physics substep, environment, joint] -> per-environment cost."""
    ratio=torque.abs()/limit
    return ((ratio-.7).clamp_min(0)/.3).square().sum(-1).mean(0)


class TorqueRecorder:
    def __init__(self, compute):
        self.compute=compute
        self.samples=[]

    def __call__(self, target):
        torque=self.compute(target)
        self.samples.append(torque.detach().clone())
        return torque  # exact same tensor; no actuator or action modification


class MicroduckControlledWalkingEnv(MicroduckWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Controlled-v2",walking_version="v2",
                        landing_event_reward="0.6 * exp(-((air_s-0.16)/0.06)^2)",
                        near_limit_torque_weight=-4.,stop_speed_weight=-3.,
                        command_mix={"forward":.4,"turn":.25,"arc":.1,"stop":.25},
                        reward_weights=dict(self.reward_weights))

    def _build_buffers(self):
        super()._build_buffers()
        self.landing_air=torch.zeros_like(self.feet_air_time)
        for name in ("motor_effort", "stop_motion", "motor_saturation_fraction", "landing_air_sum"):
            self.episode_sums[name]=torch.zeros(self.num_envs,device=self.device)

    def _build_actuator(self):
        super()._build_actuator()
        self.torque_recorder=TorqueRecorder(self.bam.compute)
        self.bam.compute=self.torque_recorder

    def step(self, actions):
        self.torque_recorder.samples.clear()
        return super().step(actions)

    def _update_contacts(self):
        self.landing_air=self.feet_air_time.clone()
        super()._update_contacts()

    def _apply_curricula(self):
        super()._apply_curricula()
        self.reward_weights["action_rate_l2"]=-.25

    def _resample_twist(self, env_ids):
        n=len(env_ids)
        choice=torch.rand(n,device=self.device)
        command=torch.zeros((n,3),device=self.device)
        forward=choice<.4
        turn=(choice>=.4)&(choice<.65)
        arc=(choice>=.65)&(choice<.75)
        command[:,0]=torch.empty(n,device=self.device).uniform_(.08,.22)*(forward|arc)
        sign=torch.where(torch.rand(n,device=self.device)<.5,-1.,1.)
        command[:,2]=torch.empty(n,device=self.device).uniform_(.35,.75)*sign*(turn|arc)
        self.twist_cmd[env_ids]=command
        self.is_standing_env[env_ids]=choice>=.75
        self.twist_resample_at[env_ids]=self.episode_length_buf[env_ids]+torch.randint(150,301,(n,),device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        active=self._command_active()
        upright=self._rew_upright()
        # Replace the v1 flat event reward; do not reward a rapid tapping rate.
        correction=.6*(self.valid_landing.float()*(landing_quality(self.landing_air)-1)).sum(-1)*active*upright
        self.rew_buf+=correction
        self.episode_sums["valid_landing"]+=correction
        if len(self.torque_recorder.samples)!=self.decimation:
            raise RuntimeError("missing physics-substep motor effort")
        torque=torch.stack(self.torque_recorder.samples)
        limit=self.bam.kt*self.bam.max_current
        stop_cost=(self.base_lin_vel[:,:2].norm(dim=-1)/.05).clamp_max(2)
        stop_cost+=(self.base_ang_vel[:,2].abs()/.2).clamp_max(2)
        terms={"motor_effort":-4*effort_cost(torque,limit)*self.dt,
               "stop_motion":-3*stop_cost*(1-active)*self.dt}
        for name,value in terms.items():
            self.rew_buf+=value
            self.episode_sums[name]+=value
        self.episode_sums["motor_saturation_fraction"]+=(torque.abs()>=.98*limit).float().mean((0,2))*self.dt
        self.episode_sums["landing_air_sum"]+=(self.landing_air*self.valid_landing).sum(-1)

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        self.landing_air[env_ids]=0
