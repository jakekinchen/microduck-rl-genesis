"""V56: identical V55 weight-3 dynamics/curriculum, standing face-posture cost."""
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
# Twenty-four fixed, balanced template/timing cells; actual application is audited.
from microduck.native_sequence_env_v46 import BUCKETS as OLD_BUCKETS, request_at as old_request
TIMINGS=[(4,1),(0,0),(6,1)]
BUCKETS=[(f'{name}-yaw{yaw}',angle,offset,motor,sensor,yaw)
         for name,angle,offset,motor,sensor in OLD_BUCKETS for yaw in [0.,.12]]


# (window controls, move end controls, windows per episode)
LAYOUTS = [(300, 150, 3), (600, 400, 3), (900, 650, 10)]


def request_at(step, bucket, episode, level):
    width, stop, _ = LAYOUTS[level]
    window, tick = divmod(step, width)
    if not 50 <= tick < stop:
        return np.zeros(3, np.float32)
    return old_request(window*900+50, bucket//2, episode)


def next_level(level, recent, controls):
    cap = 2 if controls >= 18000 else 1 if controls >= 6000 else 0
    return level+1 if level < cap and len(recent) == 8 and sum(recent) >= 6 else level


def downhill_yaw_cost(actual, requested, weight=3.):
    """Absolute error cannot cancel alternating left/right yaw excursions."""
    return weight*abs(actual-requested)/.20


def standing_face_cost(face_pitch_deg, standing, weight):
    """Train the final face metric only during exact-zero-command standing."""
    return weight*(max(abs(face_pitch_deg)-25.,0.)/5.)**2 if standing else 0.


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


def make_templates(output):
    templates = []
    for name, angle, _, motor, sensor, yaw in BUCKETS:
        terrain = {'kind': 'slope', 'axis': 'y', 'degrees': angle} if angle else {'kind': 'flat'}
        scene = materialize_terrain(output/'models'/name, terrain)
        world = TerrainWorld(BASE/'policy.onnx', ROOT/'.workspace/bam', standing_policy=BASE/'standing/policy.onnx',
            model_directory=ROOT/'experiments/walking/models/contact-v11', terrain_scene=scene,
            domain={'mass_inertia_scale': 1., 'sliding_friction_scale': 1.},
            motor_ticks=motor, sensor_ticks=sensor, yaw=yaw, seed=26090954)
        reset_controllers(world)
        templates.append((world, snapshot(world)))
    return templates


class NativeSequenceEnv:
    device = 'cpu'
    num_actions = 14
    num_obs = 61
    max_episode_length = 9000
    max_episode_length_s = 180.

    def __init__(self, num_envs, seed, output, face_weight=0.):
        if face_weight not in (0., 2.): raise ValueError("frozen face weights only")
        self.yaw_weight = 3.
        self.face_weight = face_weight
        self.num_envs, self.output = num_envs, output
        self.cfg = dict(task='Native-Standing-Posture-v56', backend='native-mujoco',
            actor_observations=61, critic_observations=61, action_filter=False,
            episodes='18/36/180 s outcome-gated curriculum; HOME only on fall or full episode timeout',
            physical_calibration=False, domain_randomization='balanced flat and +/-3 degree slopes only',
            timings=TIMINGS, standing_actor_frozen=False, flat_retention_label_actor_visible=False, yaw_cost="3 * abs(actual yaw rate - requested yaw rate) / .20 on downhill walking", face_cost=f"{face_weight} * (max(abs(face pitch degrees)-25,0)/5)^2 on exact-zero-command standing")
        self.templates = make_templates(output)
        self.worlds = [clone_world(self.templates[i%24][0]) for i in range(num_envs)]
        self.adapters = [AssignedAction() for _ in self.worlds]
        self.episode_length_buf = torch.zeros(num_envs, dtype=torch.long)
        self.episodes = np.full(num_envs, -1, np.int64)
        self.reset_counts = np.zeros(24, np.int64)
        self.falls = np.zeros(24, np.int64)
        self.completed = np.zeros(24, np.int64)
        self.phase_counts = np.zeros((24, 5), np.int64)
        self.switches = np.zeros((24, 2), np.int64)
        self.last_stand = [True]*num_envs
        self.steps = 0
        self.levels = np.zeros(num_envs, np.int64)
        self.recent = [deque(maxlen=8) for _ in self.worlds]
        self.curriculum_completions = np.zeros((24,3), np.int64)
        self.curriculum_falls = np.zeros((24,3), np.int64)
        self.level_control_counts = np.zeros((24,3), np.int64)
        self.episode_stream = gzip.open(output/'episodes.jsonl.gz', 'wt', compresslevel=1)
        self.min_obs = np.full((24, 61), np.inf)
        self.max_obs = np.full((24, 61), -np.inf)
        self.observation_digest = hashlib.sha256()
        self.action_digest = hashlib.sha256()
        self.yaw_error_sum = np.zeros(24)
        self.yaw_cost_steps = np.zeros(24, np.int64)
        self.obs_file = gzip.open(output/'all-observations-float32.bin.gz', 'wb', compresslevel=1)
        self.action_file = gzip.open(output/'all-actions-float32.bin.gz', 'wb', compresslevel=1)
        self.reward_file = gzip.open(output/'all-reward-components-float32.bin.gz', 'wb', compresslevel=1)
        self.transitions = gzip.open(output/'handoff-histories.jsonl.gz', 'wt', compresslevel=1)
        for i in range(num_envs):
            self.reset_one(i)

    def reset_one(self, i):
        level = next_level(int(self.levels[i]), self.recent[i], self.steps)
        if level != self.levels[i]:
            self.recent[i].clear()
            self.levels[i] = level
        w = self.worlds[i]
        restore(w, self.templates[i%24][1])
        reset_controllers(w)
        adapter = self.adapters[i]
        w.walking_policy = w.standing_policy = adapter
        self.episode_length_buf[i] = 0
        self.episodes[i] += 1
        self.reset_counts[i%24] += 1
        self.last_stand[i] = True

    def get_observations(self):
        obs = np.concatenate([preview(w, request_at(int(self.episode_length_buf[i]), i%24, int(self.episodes[i]), int(self.levels[i])))
                              for i, w in enumerate(self.worlds)])
        if obs.shape != (self.num_envs, 61) or not np.isfinite(obs).all():
            raise ValueError('invalid sequence observations')
        return TensorDict({'policy': torch.from_numpy(obs),
            'flat_retention': torch.tensor([[BUCKETS[i%24][1]==0] for i in range(self.num_envs)])}, [self.num_envs])

    def step(self, actions):
        actions = actions.detach().cpu().numpy().astype(np.float32)
        if actions.shape != (self.num_envs, 14) or not np.isfinite(actions).all():
            raise ValueError('invalid sequence actions')
        obs = self.get_observations()['policy'].numpy()
        self.obs_file.write(obs.tobytes()); self.observation_digest.update(obs.tobytes())
        self.action_file.write(actions.tobytes()); self.action_digest.update(actions.tobytes())
        rewards = np.zeros(self.num_envs, np.float32)
        reward_components = np.zeros((self.num_envs,8), np.float32)
        dones, timeouts = np.zeros(self.num_envs, bool), np.zeros(self.num_envs, bool)
        for i, (w, action) in enumerate(zip(self.worlds, actions)):
            bucket, step = i%24, int(self.episode_length_buf[i])
            level = int(self.levels[i])
            requested = request_at(step, bucket, int(self.episodes[i]), level)
            stand = bool(np.all(obs[i, 48:51] == 0))
            width, move_end, windows = LAYOUTS[level]
            tick = step%width
            phase = 0 if step < 50 else 1 if 50 <= tick < move_end else 2 if not stand else 3
            self.level_control_counts[bucket, level] += 1
            if 50 <= tick < 100 and step >= width:
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
                    episode_step=step, curriculum_level=level, direction='walk-to-stand' if stand else 'stand-to-walk',
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
            base_reward = .02*(tracking-cost)-8*row['fell']
            yaw_cost = 0.
            if BUCKETS[bucket][1] > 0 and not stand:
                error = abs(row['yaw_rate_rad_s']-requested[2])
                yaw_cost = downhill_yaw_cost(row['yaw_rate_rad_s'], requested[2], self.yaw_weight)
                cost += yaw_cost
                self.yaw_error_sum[bucket] += error
                self.yaw_cost_steps[bucket] += 1
            face_pitch = float(np.degrees(np.arcsin(np.clip(abs(row['face_world'][2]),0.,1.))))
            face_cost = standing_face_cost(face_pitch, stand, self.face_weight)
            cost += face_cost
            rewards[i] = .02*(tracking-cost)-8*row['fell']
            reward_components[i] = [row['yaw_rate_rad_s'],requested[2],yaw_cost,base_reward,rewards[i],stand,face_pitch,face_cost]
            self.falls[bucket] += int(row['fell'])
            self.episode_length_buf[i] += 1
            timeouts[i] = self.episode_length_buf[i] >= width*windows
            self.completed[bucket] += int(timeouts[i] and not row['fell'])
            dones[i] = timeouts[i] or row['fell']
            if dones[i]:
                success = bool(timeouts[i] and not row['fell'])
                self.recent[i].append(success)
                self.curriculum_completions[bucket, level] += int(success)
                self.curriculum_falls[bucket, level] += int(row['fell'])
                self.episode_stream.write(json.dumps(dict(env=i, bucket=bucket,
                    episode=int(self.episodes[i]), level=level, controls=int(self.episode_length_buf[i]),
                    global_control=self.steps, completed=success, fell=bool(row['fell'])))+'\n')
                self.reset_one(i)
        self.reward_file.write(reward_components.tobytes())
        self.steps += 1
        if self.steps%240 == 0:
            from experiments.walking.recipe_v54 import storage_ready
            storage_ready()
            (self.output/'coverage-progress.json').write_text(json.dumps(self.coverage(), indent=2)+'\n')
        return self.get_observations(), torch.from_numpy(rewards), torch.from_numpy(dones), {'time_outs': torch.from_numpy(timeouts)}

    def coverage(self):
        return dict(materialized_timing_cells=[dict(motor_ticks=w.motor_ticks,sensor_ticks=w.sensor_ticks,terrain=w.materialized_terrain,domain=w.materialized_domain) for w,_ in self.templates],control_steps=self.steps, transitions=self.steps*self.num_envs, buckets=[b[0] for b in BUCKETS],
            reset_counts=self.reset_counts.tolist(), falls=self.falls.tolist(), complete_episodes=self.completed.tolist(), curriculum_completions=self.curriculum_completions.tolist(), curriculum_falls=self.curriculum_falls.tolist(), curriculum_control_counts=self.level_control_counts.tolist(), final_levels=self.levels.tolist(), downhill_yaw_error_sum=self.yaw_error_sum.tolist(), downhill_yaw_cost_steps=self.yaw_cost_steps.tolist(),
            phases=['initial-stand', 'move', 'brake', 'settled-command', 'restart'], phase_counts=self.phase_counts.tolist(),
            switches_walk_to_stand_and_reverse=self.switches.tolist(), observation_min=self.min_obs.tolist(),
            observation_max=self.max_obs.tolist(), observation_raw_sha256=self.observation_digest.hexdigest(),
            action_raw_sha256=self.action_digest.hexdigest(), stored_shape=[self.steps, self.num_envs],
            stored_dtype='little-endian float32; step then environment then 61 observation / 14 action elements',
            snapshot_boundary='All actor inputs/actions and switch histories retained; switch JSON is not a complete MjData replay state.')

    def close(self):
        self.episode_stream.close()
        self.obs_file.close(); self.action_file.close(); self.reward_file.close(); self.transitions.close()
        for w in self.worlds: w.close()
        for w, _ in self.templates: w.close()
