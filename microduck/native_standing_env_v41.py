"""Focused native MuJoCo standing PPO with complete handoff-state resets."""
from collections import deque
import copy
import gzip
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np
import torch
from tensordict import TensorDict

from experiments.walking.terrain_v23 import TerrainWorld, materialize_terrain
from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
from experiments.walking.self_load import record_self_loads
from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
from microduck.constants import HEAD_JOINT_IDS

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'receipts/walking/20260906-v30-flat-regression'
TEMPLATES=[
    ('flat-forward10',0.,[.1,0,0]),('flat-forward20',0.,[.2,0,0]),
    ('flat-left',0.,[0,0,.6]),('flat-right',0.,[0,0,-.6]),
    ('flat-arc-left',0.,[.12,0,.35]),('flat-arc-right',0.,[.12,0,-.35]),
    ('downhill',3.,[.12,0,0]),('uphill',-3.,[.12,0,0]),
]


def snapshot(world):
    c=world.core
    return dict(data=copy.copy(c.data),damping=c.model.dof_damping.copy(),friction=c.model.dof_frictionloss.copy(),
        last_ts=c.controller.last_ts,previous_torque=c.controller._prev_motor_torque.copy(),
        q_target=c.controller.q_target.copy(),motor_history=copy.deepcopy(world.motor_delay.history),
        sensors=copy.deepcopy(world.sensor_rows),last_action=world.last_action.copy(),
        applied_target=world.applied_target.copy(),steps=world.steps)


def restore(world, state):
    c=world.core
    c.model.dof_damping[:]=state['damping']; c.model.dof_frictionloss[:]=state['friction']
    mujoco.mj_copyData(c.data,c.model,state['data'])
    c.controller.last_ts=state['last_ts']; c.controller._prev_motor_torque=state['previous_torque'].copy()
    c.controller.q_target=state['q_target'].copy()
    world.motor_delay.history=copy.deepcopy(state['motor_history'])
    world.sensor_rows=copy.deepcopy(state['sensors']); world.last_action=state['last_action'].copy()
    world.applied_target=state['applied_target'].copy(); world.steps=state['steps']; world.fell=False


def observation(world):
    c=world.core
    obs=c.observation_vector(world.last_action,np.zeros(3),np.zeros(4),np.zeros(6))
    if world.sensor_ticks and world.sensor_rows:
        old=world.sensor_rows[-1]
        obs[:,:6]=old[:,:6]; obs[:,20:34]=old[:,20:34]
    return obs


def raw_step(world, action):
    expected=observation(world)
    with record_self_loads(world) as loads:
        row=ConsistentSensorWalkingWorld.step_command(world,[0,0,0],action_override=action)
    np.testing.assert_array_equal(world.last_observation,expected)
    if world.last_action.tobytes()!=np.asarray(action,np.float32).tobytes():raise ValueError('altered training action')
    if len(loads)!=4:raise ValueError('missing physics load samples')
    clearance=float(world.core.data.qpos[2]-world.ground.height([world.core.data.qpos[:2]])[0])
    world.fell=clearance<.07 or row['tilt_deg']>70
    row.update(fell=world.fell,base_clearance_m=clearance,internal_load_n=max(s['total_normal_n'] for s in loads))
    return row


def clone_world(template):
    w=copy.copy(template); w.core=copy.copy(template.core)
    w.core.model=copy.copy(template.core.model); w.core.data=mujoco.MjData(w.core.model)
    w.core._validate_model(); w.core.controller=w.core._build_bam_controller(ROOT/'.workspace/bam')
    w.core.observation_vector=w._observation_vector
    w.sensor_data=mujoco.MjData(w.core.model); w.motor_delay=copy.copy(template.motor_delay)
    w.robot_trail=deque(maxlen=400); w.target_trail=deque(maxlen=400)
    assert not np.shares_memory(w.core.model.dof_damping,template.core.model.dof_damping)
    return w


def build_templates(output):
    templates=[]; reports=[]
    for name,angle,command in TEMPLATES:
        terrain={'kind':'slope','axis':'y','degrees':angle} if angle else {'kind':'flat'}
        scene=materialize_terrain(output/'models'/name,terrain)
        w=TerrainWorld(BASE/'policy.onnx',ROOT/'.workspace/bam',standing_policy=BASE/'standing/policy.onnx',
            model_directory=ROOT/'experiments/walking/models/contact-v11',terrain_scene=scene,
            domain={'mass_inertia_scale':1.,'sliding_friction_scale':1.},motor_ticks=6,sensor_ticks=1,yaw=0.,seed=26090641)
        w.heading_servo=Float32HeadingHeadroomServo()
        home=snapshot(w); actions=[]; handoff=None
        with gzip.open(output/f'{name}-prefix.jsonl.gz','wt') as stream:
            for i in range(750):
                requested=command if 50<=i<650 else [0,0,0]
                if i>=650 and np.all(copy.deepcopy(w.command_ramp).step(requested)==0):
                    handoff=snapshot(w); break
                row=w.step_command(requested)
                actions.append(w.last_action.copy())
                stream.write(json.dumps(dict(time_s=row['time_s'],qpos=w.core.data.qpos.tolist(),qvel=w.core.data.qvel.tolist(),
                    action=w.last_action.tolist(),actor_mode=row['actor_mode'],fell=row['fell']))+'\n')
                if w.fell:break
        actions=np.asarray(actions,np.float32)
        report=dict(id=name,terrain=terrain,command=command,steps=len(actions),handoff_available=handoff is not None,
            action_bytes_sha256=hashlib.sha256(actions.tobytes()).hexdigest())
        np.save(output/f'{name}-actions.npy',actions)
        if name=='downhill':
            recorded=np.load(ROOT/'receipts/walking/20260906-v30-heading-endurance/downhill-3deg-start-1--window-1-actions-float32.npy')
            np.testing.assert_array_equal(actions,recorded[:len(actions)])
            report['v30_prefix_action_bytes_identical']=True
        if handoff is not None:
            # Continuing identical full states must reproduce after a reset,
            # including BAM load-dependent friction and every sensor/FIFO state.
            restore(w,handoff)
            actor_action=w.standing_policy.infer(observation(w))[0][0]
            raw_step(w,actor_action);first=(w.core.data.qpos.copy(),w.core.data.qvel.copy(),w.core.data.ctrl.copy())
            restore(w,handoff);raw_step(w,actor_action)
            for a,b in zip(first,(w.core.data.qpos,w.core.data.qvel,w.core.data.ctrl)):np.testing.assert_array_equal(a,b)
            report['exact_reset_continuation']=True
            templates.append((w,home,handoff))
            for kind,state in [('home',home),('handoff',handoff)]:
                np.savez_compressed(output/f'{name}-{kind}.npz',qpos=state['data'].qpos,qvel=state['data'].qvel,
                    qacc_warmstart=state['data'].qacc_warmstart,ctrl=state['data'].ctrl,
                    friction=state['friction'],damping=state['damping'],motor_fifo=np.asarray(state['motor_history']),
                    previous_torque=state['previous_torque'],last_action=state['last_action'])
        else:w.close()
        reports.append(report)
    (output/'templates.json').write_text(json.dumps(reports,indent=2)+'\n')
    if len(templates)<6 or any(not r['handoff_available'] for r in reports if r['id'] in ('uphill','downhill')):
        raise ValueError('required native handoff coverage missing')
    return templates,reports


class NativeStandingEnv:
    device='cpu'
    num_actions=14
    num_obs=61
    max_episode_length=150
    max_episode_length_s=3.

    def __init__(self,num_envs,seed,output):
        self.num_envs=num_envs;self.rng=np.random.default_rng(seed)
        self.cfg=dict(task='Native-Standing-Transitions-v41',backend='native-mujoco',actor_observations=61,
            action_filter=False,initial_state_mixture='half HOME, half full handoff; fixed balanced template assignments',
            physical_calibration=False,domain_randomization='initial state/terrain choice only')
        self.templates,self.template_reports=build_templates(output)
        self.worlds=[clone_world(self.templates[i%len(self.templates)][0]) for i in range(num_envs)]
        self.episode_length_buf=torch.zeros(num_envs,dtype=torch.long)
        self.reset_counts=np.zeros((len(self.templates),2),dtype=np.int64)
        self.contact_ticks=np.zeros(len(self.templates),dtype=np.int64)
        self.fall_counts=np.zeros(len(self.templates),dtype=np.int64)
        self.steps=0
        for i in range(num_envs):self.reset_one(i)

    def reset_one(self,i):
        template=i%len(self.templates);kind=int(self.rng.integers(2))
        restore(self.worlds[i],self.templates[template][1+kind])
        self.episode_length_buf[i]=0;self.reset_counts[template,kind]+=1

    def get_observations(self):
        obs=np.concatenate([observation(w) for w in self.worlds])
        if obs.shape!=(self.num_envs,61) or not np.isfinite(obs).all():raise ValueError('invalid native actor observations')
        return TensorDict({'policy':torch.from_numpy(obs)},[self.num_envs])

    def step(self,actions):
        actions=actions.detach().cpu().numpy().astype(np.float32)
        if actions.shape!=(self.num_envs,14) or not np.isfinite(actions).all():raise ValueError('invalid native actor action')
        rewards=np.zeros(self.num_envs,np.float32);dones=np.zeros(self.num_envs,bool);timeouts=np.zeros(self.num_envs,bool)
        self.episode_length_buf+=1
        for i,(w,action) in enumerate(zip(self.worlds,actions)):
            previous=w.last_action.copy();row=raw_step(w,action);c=w.core
            head=c.data.qpos[c.qpos_indices[list(HEAD_JOINT_IDS)]]-c.home[list(HEAD_JOINT_IDS)]
            tracking=np.exp(-(row['speed_m_s']/.05)**2-(row['tilt_deg']/10.)**2-float(np.mean((head/.2)**2)))
            margin=row['minimum_actual_joint_margin_rad'];internal=row['internal_load_n']
            rewards[i]=.02*(4*tracking-2*max(0.,internal-.5)-10*(margin<.04)-.1*float(np.square(action-previous).sum()))-8*row['fell']
            template=i%len(self.templates)
            self.contact_ticks[template]+=sum(1 for cn in c.data.contact if c.model.geom_bodyid[int(cn.geom1)]==0 or c.model.geom_bodyid[int(cn.geom2)]==0)
            self.fall_counts[template]+=int(row['fell'])
            timeouts[i]=self.episode_length_buf[i]>=self.max_episode_length
            dones[i]=timeouts[i] or row['fell']
            if dones[i]:self.reset_one(i)
        self.steps+=1
        return self.get_observations(),torch.from_numpy(rewards),torch.from_numpy(dones),{'time_outs':torch.from_numpy(timeouts)}

    def coverage(self):
        return dict(reset_counts_home_handoff=self.reset_counts.tolist(),ground_contact_samples=self.contact_ticks.tolist(),
            falls=self.fall_counts.tolist(),control_steps=self.steps,templates=self.template_reports)

    def close(self):
        for w in self.worlds:w.close()
        for w,_,_ in self.templates:w.close()
