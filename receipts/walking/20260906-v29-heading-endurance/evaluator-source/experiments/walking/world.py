"""Versioned timing-aware native world; direct policy output, no motion assistance."""
from collections import deque
import math
import mujoco
import numpy as np
from experiments.laser.face_world import FaceFirstLaserWorld
from evaluator.core import projected_gravity
from microduck.laser_dynamics import domain_draw


class TargetDelay:
    """FIFO in PHYSICS ticks. Values are held, never interpolated or filtered."""
    def __init__(self,initial,ticks):
        if not isinstance(ticks,int) or not 0<=ticks<=6:raise ValueError("invalid motor lag")
        self.history=deque([np.array(initial,copy=True) for _ in range(ticks)])

    def step(self,target):
        self.history.append(np.array(target,copy=True))
        return self.history.popleft()


class WalkingWorld(FaceFirstLaserWorld):
    def __init__(self,policy,bam_repo,*,motor_ticks=4,sensor_ticks=1,yaw=0.,seed=76521,render=False):
        if sensor_ticks not in (0,1):raise ValueError("invalid sensor lag")
        super().__init__(policy,bam_repo,domain_draw(seed,False),render=render)
        self.core.reset([0,0,.125],[math.cos(yaw/2),0,0,math.sin(yaw/2)])
        self.motor_delay=TargetDelay(self.core.home,motor_ticks)
        self.motor_ticks,self.sensor_ticks=motor_ticks,sensor_ticks
        self.sensor_rows=deque(maxlen=2)
        self.applied_target=self.core.home.copy()

    def step_command(self,command,action_override=None):
        if self.fell:raise RuntimeError("fall is terminal; no automatic reset")
        command=np.asarray(command,np.float32)
        if command.shape!=(3,) or not np.isfinite(command).all():raise ValueError("invalid command")
        c=self.core
        obs=c.observation_vector(self.last_action,command,np.zeros(4),np.zeros(6))
        self.sensor_rows.append(obs.copy())
        delayed=self.sensor_rows[max(0,len(self.sensor_rows)-1-self.sensor_ticks)]
        obs[:,:6]=delayed[:,:6];obs[:,20:34]=delayed[:,20:34]
        self.last_observation=obs.copy()
        action,latency=c.policy.infer(obs)
        if action_override is not None:action=np.asarray(action_override,dtype=np.float32).reshape(1,14)
        if action.shape!=(1,14) or not np.isfinite(action).all():raise ValueError("invalid action")
        self.last_action=action[0].copy()
        reference=c.home+self.last_action.astype(np.float64)
        torques=[]
        for _ in range(4):
            self.applied_target=self.motor_delay.step(reference)
            for j,name in enumerate(c.joint_names):c.controller.set_q_target(name,float(self.applied_target[j]))
            c.controller.update();torques.append(c.data.ctrl.copy());mujoco.mj_step(c.model,c.data)
        if not np.isfinite(np.r_[c.data.qpos,c.data.qvel,c.data.ctrl]).all():raise ValueError("nonfinite simulation")
        tilt=float(np.degrees(np.arccos(np.clip(-projected_gravity(c.data.qpos[3:7])[2],-1,1))))
        self.fell=bool(c.data.qpos[2]<.07 or tilt>70)
        self.steps+=1
        rotation=np.zeros(9);mujoco.mju_quat2Mat(rotation,c.data.qpos[3:7])
        self.robot_trail.append(c.data.qpos[:3].copy())
        self.latest={"time_s":self.steps*.02,"robot_xyz_m":c.data.qpos[:3].tolist(),
                     "speed_m_s":float(np.linalg.norm(c.data.qvel[:2])),"tilt_deg":tilt,"fell":self.fell,
                     "command":command.tolist(),"action_rad":self.last_action.tolist(),"latency_ms":latency,
                     "body_velocity_m_s":(rotation.reshape(3,3).T@c.data.qvel[:3]).tolist(),
                     "yaw_rate_rad_s":float(c.data.sensor("imu_ang_vel").data[2]),
                     "applied_servo_target_rad":self.applied_target.tolist(),
                     "motor_torque_physics_nm":np.asarray(torques).tolist(),
                     "minimum_actual_joint_margin_rad":float(np.minimum(c.data.qpos[c.qpos_indices]-c.model.jnt_range[c.joint_ids,0],c.model.jnt_range[c.joint_ids,1]-c.data.qpos[c.qpos_indices]).min()),
                     "motor_delay_physics_ticks":self.motor_ticks,"sensor_delay_control_ticks":self.sensor_ticks}
        return self.latest

    def walking_frame(self):
        return self.frame([0,0],False,view="inspection")
