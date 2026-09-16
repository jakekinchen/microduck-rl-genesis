"""Native standing correction from HOME and complete pre-brake states."""
from collections import deque
import copy
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from microduck.native_standing_env_v42 import clone_world, snapshot, restore
from experiments.walking.terrain_v23 import TerrainWorld, materialize_terrain
from experiments.walking.self_load import record_self_loads
from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
from microduck.constants import HEAD_JOINT_IDS

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'receipts/walking/20260906-v30-flat-regression'
# Twenty-four balanced terrain/timing/yaw cells; actual application is audited.
from microduck.native_sequence_env_v46 import BUCKETS as OLD_BUCKETS, request_at as old_request
from experiments.walking.handoff_inspection_v47 import restore_state
TIMINGS=[(4,1),(0,0),(6,1)]
BUCKETS=[(f'{name}-yaw{yaw}',angle,offset,motor,sensor,yaw)
         for name,angle,offset,motor,sensor in OLD_BUCKETS for yaw in [0.,.12]]


def request_at(step,bucket,episode):
    return old_request(step,bucket//2,episode)


def joint_margin_cost(q,limits):
    fraction=np.minimum(q-limits[:,0],limits[:,1]-q)/(limits[:,1]-limits[:,0])
    return 10*float(np.square(np.maximum(.07-fraction,0)/.05).sum())


def preview(world, requested):
    """Predict the next input without advancing the physical or controller state."""
    routed = copy.deepcopy(world.command_ramp).step(requested)
    history = copy.deepcopy(world.heading_sensor_history)
    history.append(world._sample_current_sensors().sensor('orientation').data.copy())
    orientation = history[max(0, len(history)-1-world.sensor_ticks)]
    command, _ = copy.deepcopy(world.heading_servo).step(routed, orientation)
    obs = world.core.observation_vector(world.last_action, command, np.zeros(4), np.zeros(6))
    if world.sensor_ticks and world.sensor_rows:
        obs[:, :6] = world.sensor_rows[-1][:, :6]
        obs[:, 20:34] = world.sensor_rows[-1][:, 20:34]
    if bool(np.all(routed == 0)) != bool(np.all(obs[0, 48:51] == 0)):
        raise ValueError('raw observation and deployment actor routing disagree')
    return obs


class AssignedAction:
    """Insert the sampled action at the actual policy call, with exact ABI checks."""
    def infer(self, obs):
        if obs.tobytes() != self.expected.tobytes():
            raise ValueError('training input differs from actual deployed observation')
        self.calls += 1
        return self.action.reshape(1, 14), 0.


def reset_controllers(world):
    from experiments.walking.command_ramp import CommandRamp
    world.command_ramp = CommandRamp()
    world.heading_servo = Float32HeadingHeadroomServo()
    world.heading_sensor_history = deque(maxlen=2)


def full_state(world):
    state=snapshot(world)
    state.update(command_ramp=copy.deepcopy(world.command_ramp),
        heading_servo=copy.deepcopy(world.heading_servo),
        heading_sensor_history=copy.deepcopy(world.heading_sensor_history),fell=world.fell)
    return state


def make_templates(output):
    templates = []
    for bucket,(name, angle, _, motor, sensor, yaw) in enumerate(BUCKETS):
        terrain = {'kind': 'slope', 'axis': 'y', 'degrees': angle} if angle else {'kind': 'flat'}
        scene = materialize_terrain(output/'models'/name, terrain)
        world = TerrainWorld(BASE/'policy.onnx', ROOT/'.workspace/bam', standing_policy=BASE/'standing/policy.onnx',
            model_directory=ROOT/'experiments/walking/models/contact-v11', terrain_scene=scene,
            domain={'mass_inertia_scale': 1., 'sliding_friction_scale': 1.},
            motor_ticks=motor, sensor_ticks=sensor, yaw=yaw, seed=26090848)
        reset_controllers(world)
        home=full_state(world)
        prefix=[]
        for step in range(650):
            row=world.step_command(request_at(step,bucket,0))
            prefix.append(world.last_action.copy())
            if row['fell']:raise ValueError('original pre-brake prefix fell: '+name)
        prebrake=full_state(world)
        np.save(output/'models'/name/'prefix-actions-float32.npy',np.asarray(prefix,np.float32))
        templates.append((world,home,prebrake))
    return templates


class NativeSequenceEnv:
    device = 'cpu'
    num_actions = 14
    num_obs = 61
    max_episode_length = 2700
    max_episode_length_s = 54.

    def __init__(self, num_envs, seed, output):
        self.num_envs, self.output = num_envs, output
        self.cfg = dict(task='Native-Retained-Stander-v48', backend='native-mujoco',
            actor_observations=61, critic_observations=61, action_filter=False,
            episodes='HOME or complete pre-brake (13 s); continuous to 54 s or fall; no reset at handoffs',
            physical_calibration=False, domain_randomization='balanced flat and +/-3 degree slopes, three timings, two yaw starts; no broad randomization',
            timings=TIMINGS, walking_actor_frozen=True, flat_retention_label_actor_visible=False)
        self.templates = make_templates(output)
        self.worlds = [clone_world(self.templates[i%24][0]) for i in range(num_envs)]
        self.adapters = [AssignedAction() for _ in self.worlds]
        self.episode_length_buf = torch.zeros(num_envs, dtype=torch.long)
        self.episodes = np.full(num_envs, -1, np.int64)
        self.reset_counts = np.zeros((24,2), np.int64)
        self.reset_kind = np.zeros(num_envs, np.int64)
        self.completed_from_origin = np.zeros((24,2), np.int64)
        self.falls = np.zeros(24, np.int64)
        self.completed = np.zeros(24, np.int64)
        self.phase_counts = np.zeros((24, 5), np.int64)
        self.switches = np.zeros((24, 2), np.int64)
        self.last_stand = [True]*num_envs
        self.steps = 0
        self.min_obs = np.full((24, 61), np.inf)
        self.max_obs = np.full((24, 61), -np.inf)
        self.observation_digest = hashlib.sha256()
        self.action_digest = hashlib.sha256()
        self.obs_file = gzip.open(output/'all-observations-float32.bin.gz', 'wb', compresslevel=1)
        self.action_file = gzip.open(output/'all-actions-float32.bin.gz', 'wb', compresslevel=1)
        self.transitions = gzip.open(output/'handoff-histories.jsonl.gz', 'wt', compresslevel=1)
        for i in range(num_envs):
            self.reset_one(i)

    def reset_one(self, i):
        w = self.worlds[i]
        kind=(i//24+i+int(self.episodes[i])+1)%2
        restore_state(w,self.templates[i%24][1+kind])
        self.reset_kind[i]=kind
        adapter = self.adapters[i]
        w.walking_policy = w.standing_policy = adapter
        self.episode_length_buf[i] = 650 if kind else 0
        self.episodes[i] += 1
        self.reset_counts[i%24,kind] += 1
        self.last_stand[i] = not bool(kind)

    def get_observations(self):
        obs = np.concatenate([preview(w, request_at(int(self.episode_length_buf[i]), i%24, int(self.episodes[i])))
                              for i, w in enumerate(self.worlds)])
        if obs.shape != (self.num_envs, 61) or not np.isfinite(obs).all():
            raise ValueError('invalid sequence observations')
        return TensorDict({'policy': torch.from_numpy(obs),
            'flat_retention':torch.tensor([[BUCKETS[i%24][1]==0] for i in range(self.num_envs)])}, [self.num_envs])

    def step(self, actions):
        actions = actions.detach().cpu().numpy().astype(np.float32)
        if actions.shape != (self.num_envs, 14) or not np.isfinite(actions).all():
            raise ValueError('invalid sequence actions')
        obs = self.get_observations()['policy'].numpy()
        self.obs_file.write(obs.tobytes()); self.observation_digest.update(obs.tobytes())
        self.action_file.write(actions.tobytes()); self.action_digest.update(actions.tobytes())
        rewards = np.zeros(self.num_envs, np.float32)
        dones, timeouts = np.zeros(self.num_envs, bool), np.zeros(self.num_envs, bool)
        for i, (w, action) in enumerate(zip(self.worlds, actions)):
            bucket, step = i%24, int(self.episode_length_buf[i])
            requested = request_at(step, bucket, int(self.episodes[i]))
            stand = bool(np.all(obs[i, 48:51] == 0))
            tick = step%900
            phase = 0 if step < 50 else 1 if 50 <= tick < 650 else 2 if not stand else 3
            if 50 <= tick < 100 and step >= 900:
                phase = 4
            self.phase_counts[bucket, phase] += 1
            self.min_obs[bucket] = np.minimum(self.min_obs[bucket], obs[i])
            self.max_obs[bucket] = np.maximum(self.max_obs[bucket], obs[i])
            c = w.core
            if stand != self.last_stand[i]:
                direction = 0 if stand else 1
                self.switches[bucket, direction] += 1
                # Every actual switch includes endogenous actuator and sensing
                # histories, not just HOME samples or an assumed coverage recipe.
                history = dict(global_step=self.steps, env=i, bucket=bucket, episode=int(self.episodes[i]),
                    episode_step=step, reset_kind=int(self.reset_kind[i]), direction='walk-to-stand' if stand else 'stand-to-walk',
                    observation=obs[i].tolist(), qpos=c.data.qpos.tolist(), qvel=c.data.qvel.tolist(),
                    motor_fifo=np.asarray(w.motor_delay.history).tolist(),
                    previous_torque=c.controller._prev_motor_torque.tolist(), q_target=c.controller.q_target.tolist(),
                    sensors=np.asarray(w.sensor_rows).tolist(), last_action=w.last_action.tolist(),
                    damping=c.model.dof_damping.tolist(), friction=c.model.dof_frictionloss.tolist())
                self.transitions.write(json.dumps(history)+'\n')
            self.last_stand[i] = stand
            previous = w.last_action.copy()
            adapter = self.adapters[i]
            adapter.expected, adapter.action, adapter.calls = obs[i:i+1], action, 0
            with record_self_loads(w) as loads:
                row = w.step_command(requested)
            if adapter.calls != 1 or len(loads) != 4 or w.last_action.tobytes() != action.tobytes():
                raise ValueError('missing physics telemetry or altered action')
            target = obs[i, 48:51]
            velocity = np.asarray(row['body_velocity_m_s'])[:2]
            head = c.data.qpos[c.qpos_indices[list(HEAD_JOINT_IDS)]]-c.home[list(HEAD_JOINT_IDS)]
            tracking = 3*np.exp(-np.square((velocity-target[:2])/.08).sum())
            tracking += np.exp(-((row['yaw_rate_rad_s']-target[2])/.30)**2)
            posture = 4*(max(0., row['tilt_deg']-10.)/5.)**2
            posture += 2*float(np.mean((np.maximum(np.abs(head)-.2, 0.)/.15)**2))
            internal = max(s['total_normal_n'] for s in loads)
            stop_cost = 2*((row['speed_m_s']/.05)**2+(row['yaw_rate_rad_s']/.30)**2) if stand else 0.
            torque = np.asarray(row['motor_torque_physics_nm'])
            effort = 2*float((abs(torque) >= .98*.6405236195572268).mean())
            cost = posture+stop_cost+2*max(0., internal-.5)+joint_margin_cost(c.data.qpos[c.qpos_indices],c.model.jnt_range[c.joint_ids])
            cost += effort+.1*float(np.square(action-previous).sum())
            rewards[i] = .02*(tracking-cost)-8*row['fell']
            self.falls[bucket] += int(row['fell'])
            self.episode_length_buf[i] += 1
            timeouts[i] = self.episode_length_buf[i] >= self.max_episode_length
            self.completed[bucket] += int(timeouts[i] and not row['fell'])
            self.completed_from_origin[bucket,self.reset_kind[i]] += int(timeouts[i] and not row['fell'])
            dones[i] = timeouts[i] or row['fell']
            if dones[i]:
                self.reset_one(i)
        self.steps += 1
        if self.steps%240 == 0:
            (self.output/'coverage-progress.json').write_text(json.dumps(self.coverage(), indent=2)+'\n')
        return self.get_observations(), torch.from_numpy(rewards), torch.from_numpy(dones), {'time_outs': torch.from_numpy(timeouts)}

    def coverage(self):
        return dict(materialized_timing_cells=[dict(motor_ticks=w.motor_ticks,sensor_ticks=w.sensor_ticks,terrain=w.materialized_terrain,domain=w.materialized_domain) for w,_,_ in self.templates],control_steps=self.steps, transitions=self.steps*self.num_envs, buckets=[b[0] for b in BUCKETS],
            reset_counts=self.reset_counts.tolist(), falls=self.falls.tolist(), completed_to_sequence_end=self.completed.tolist(),completed_from_home_or_prebrake=self.completed_from_origin.tolist(),
            phases=['initial-stand', 'move', 'brake', 'settled-command', 'restart'], phase_counts=self.phase_counts.tolist(),
            switches_walk_to_stand_and_reverse=self.switches.tolist(), observation_min=self.min_obs.tolist(),
            observation_max=self.max_obs.tolist(), observation_raw_sha256=self.observation_digest.hexdigest(),
            action_raw_sha256=self.action_digest.hexdigest(), stored_shape=[self.steps, self.num_envs],
            stored_dtype='little-endian float32; step then environment then 61 observation / 14 action elements',
            snapshot_boundary='All actor inputs/actions and switch histories retained; switch JSON is not a complete MjData replay state.')

    def close(self):
        self.obs_file.close(); self.action_file.close(); self.transitions.close()
        for w in self.worlds: w.close()
        for w, _, _ in self.templates: w.close()
