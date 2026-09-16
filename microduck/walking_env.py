"""Walking v1: command-only, dense sole-lift feedback and explicit timing envelope.

Keeps the frozen rigid model, BAM law and 61D/14D interface. No phase clock,
scripted action, external force, joint clipping or assisted starting gait.
"""
import math
import numpy as np
import torch
import mujoco
from scipy.spatial import ConvexHull
from genesis.utils.geom import transform_by_quat
from .velocity_env import MicroduckVelocityEnv
from .bam_actuator import DelayBuffer
from .laser_gait_env import joint_boundary_cost


def sole_vertices(robot_xml):
    """Collision-mesh hull vertices in the ankle BODY frame, not foot SITE height."""
    model = mujoco.MjModel.from_xml_path(robot_xml)
    feet=[]
    for side in ("left","right"):
        geom=model.geom(f"{side}_foot_collision").id
        mesh=model.geom_dataid[geom]
        start,count=model.mesh_vertadr[mesh],model.mesh_vertnum[mesh]
        vertices=model.mesh_vert[start:start+count].copy()
        vertices=vertices[ConvexHull(vertices).vertices]
        rotation=np.zeros(9)
        mujoco.mju_quat2Mat(rotation,model.geom_quat[geom])
        feet.append(vertices@rotation.reshape(3,3).T+model.geom_pos[geom])
    count=max(len(v) for v in feet)
    return np.stack([np.concatenate((v,np.repeat(v[:1],count-len(v),axis=0))) for v in feet])


def lift_score(sole_height,air_time,contact):
    valid=(~contact)&(air_time>=.02)&(air_time<=.30)&contact.flip(-1)
    return (torch.exp(-((sole_height-.018)/.014).square())*valid).sum(-1)


class MicroduckWalkingEnv(MicroduckVelocityEnv):
    def __init__(self,num_envs,**kwargs):
        super().__init__(num_envs,task_name="Walking-Sole-Timing-v1",**kwargs)
        self.cfg.update(walking_version="v1",motor_delay_physics_steps=[0,6],
                        sensor_delay_control_steps=[0,1],domain="nominal rigid model; timing variation only",
                        reward_weights=dict(self.reward_weights),landing_event_reward=.6)

    def _build_buffers(self):
        super()._build_buffers()
        self._sole_vertices=torch.tensor(sole_vertices(self.robot_xml),device=self.device,dtype=self.actions.dtype)
        self.sole_height=torch.zeros((self.num_envs,2),device=self.device)
        self.peak_sole=torch.zeros_like(self.sole_height)
        self.valid_landing=torch.zeros_like(self.sole_height,dtype=torch.bool)
        self.hard_stop_ticks=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.actual_lo,self.actual_hi=self.robot.get_dofs_limit(self.motors_dof_idx)
        self.actual_lo=self.actual_lo.flatten()[:14]
        self.actual_hi=self.actual_hi.flatten()[:14]
        self.episode_sums["sole_lift"]=torch.zeros(self.num_envs,device=self.device)
        self.episode_sums["valid_landing"]=torch.zeros(self.num_envs,device=self.device)
        self.episode_sums["fall_event"]=torch.zeros(self.num_envs,device=self.device)
        self.episode_sums["flight_cost"]=torch.zeros(self.num_envs,device=self.device)
        self.episode_sums["qualified_landing_rate"]=torch.zeros(self.num_envs,device=self.device)

    def _build_actuator(self):
        super()._build_actuator()
        self.bam._delay=DelayBuffer((self.num_envs,14),0,6,64,self.device)
        self.obs_delays["joint_vel"]=DelayBuffer((self.num_envs,14),0,1,64,self.device)

    def _startup_randomization(self):
        # Nominal foundation: no mass/COM/friction/IMU or encoder perturbation.
        was_demo=self.demo
        self.demo=True
        try: super()._startup_randomization()
        finally: self.demo=was_demo

    def _refresh_state(self):
        super()._refresh_state()
        if not hasattr(self,"_sole_vertices"): return
        count=self._sole_vertices.shape[1]
        q=self._links_quat[:,self.foot_link_idx,None,:].expand(-1,-1,count,-1)
        points=transform_by_quat(self._sole_vertices[None].expand(self.num_envs,-1,-1,-1),q)
        points+=self._links_pos[:,self.foot_link_idx,None,:]
        self.sole_height=points[...,2].amin(-1)

    def _update_contacts(self):
        prior_air=self.feet_air_time.clone()
        prior_contact=self.last_contacts.clone()
        super()._update_contacts()
        self.contact=self.foot_contact_force[...,2]>1.
        self.first_contact=self.contact&~prior_contact
        self.last_contacts=self.contact.clone()
        self.peak_sole=torch.where(~self.contact,torch.maximum(self.peak_sole,self.sole_height),self.peak_sole)
        self.valid_landing=self.first_contact&(prior_air>=.06)&(prior_air<=.35)&(self.peak_sole>=.005)
        self.peak_sole=torch.where(self.first_contact,torch.zeros_like(self.peak_sole),self.peak_sole)
        self.feet_air_time=torch.where(self.contact,torch.zeros_like(prior_air),prior_air+self.dt)
        margin=torch.minimum(self.dof_pos-self.actual_lo,self.actual_hi-self.dof_pos)/(self.actual_hi-self.actual_lo)
        self.hard_stop_ticks=torch.where((margin<.05).any(-1),self.hard_stop_ticks+1,torch.zeros_like(self.hard_stop_ticks))

    def _resample_twist(self,env_ids):
        n=len(env_ids)
        choice=torch.rand(n,device=self.device)
        command=torch.zeros((n,3),device=self.device)
        forward=choice<.55
        turn=(choice>=.55)&(choice<.85)
        arc=(choice>=.85)&(choice<.95)
        command[:,0]=torch.empty(n,device=self.device).uniform_(.08,.22)*(forward|arc)
        sign=torch.where(torch.rand(n,device=self.device)<.5,-1.,1.)
        command[:,2]=torch.empty(n,device=self.device).uniform_(.35,.75)*sign*(turn|arc)
        self.twist_cmd[env_ids]=command
        self.is_standing_env[env_ids]=choice>=.95
        self.twist_resample_at[env_ids]=self.episode_length_buf[env_ids]+torch.randint(150,301,(n,),device=self.device)

    def _resample_pose_cmd(self,env_ids,buf,ranges,at_buf,resample_s):
        buf[env_ids]=0
        at_buf[env_ids]=self.episode_length_buf[env_ids]+250

    def _maybe_push(self): pass

    def _apply_curricula(self):
        super()._apply_curricula()
        self.reward_weights.update(track_linear_velocity=6.,track_angular_velocity=5.,upright=2.,
                                   pose=.3,action_rate_l2=-.12,dof_pos_limits=-4.,
                                   foot_slip=-2.,air_time=2.,foot_clearance=-2.,
                                   foot_swing_height=0.,head_pose_tracking=2.,head_pose_bias=0.)

    def _rew_track_lin(self):
        err=(self.twist_cmd[:,:2]-self.base_lin_vel[:,:2]).square().sum(-1)
        return torch.exp(-err/.12**2)

    def _rew_track_ang(self):
        return torch.exp(-(self.twist_cmd[:,2]-self.base_ang_vel[:,2]).square()/.35**2)

    def _rew_dof_pos_limits(self):
        return joint_boundary_cost(self.dof_pos,self.actual_lo,self.actual_hi)

    def _rew_foot_clearance(self,active):
        return ((self.sole_height-.018).abs()*self.foot_vel[...,:2].norm(dim=-1)).sum(-1)*active

    def _compute_observations(self):
        was_demo=self.demo
        self.demo=True  # delay buffers remain active; no additive observation noise
        try: return super()._compute_observations()
        finally: self.demo=was_demo

    def _compute_rewards(self):
        super()._compute_rewards()
        active=self._command_active()
        upright=self._rew_upright()
        fell=(self.base_pos[:,2]<.07)|(self.projected_gravity[:,2]>-math.cos(math.radians(55)))
        terms={"sole_lift":4*lift_score(self.sole_height,self.feet_air_time,self.contact)*active*upright*self.dt,
               "valid_landing":.6*self.valid_landing.float().sum(-1)*active*upright,
               "flight_cost":-2*(~self.contact).all(-1)*self.dt,
               "fall_event":-8*fell.float()}
        for name,value in terms.items():
            self.rew_buf+=value
            self.episode_sums[name]+=value
        self.episode_sums["qualified_landing_rate"]+=self.valid_landing.float().sum(-1)

    def _check_termination(self):
        super()._check_termination()
        if not self.demo:
            self.reset_buf|=(self.base_pos[:,2]<.07)|(self.projected_gravity[:,2]>-math.cos(math.radians(55)))|(self.hard_stop_ticks>25)

    def reset_idx(self,env_ids):
        was_demo=self.demo
        self.demo=True  # disable episode physical DR without changing reset population
        try: super().reset_idx(env_ids)
        finally: self.demo=was_demo
        self.peak_sole[env_ids]=0
        self.valid_landing[env_ids]=False
        self.hard_stop_ticks[env_ids]=0
