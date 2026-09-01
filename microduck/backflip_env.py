"""Genesis flat-ground standing-backflip task on the proven walking runtime.

This recreates the bounded base task from Lulzx/microduck-backflip: full-body
collisions, reverse-curriculum starts, airborne-only backward rotation, an
annealed virtual spotter, and strict feet-first stable landing semantics.  The
actor contract remains byte-for-byte compatible with walking (61 observations,
14 actions).
"""

from __future__ import annotations

import math

import genesis as gs
import torch
from genesis.utils.geom import transform_by_quat

from . import backflip_cfg as B
from . import velocity_cfg as V
from .constants import MICRODUCK_ALLCOLLISIONS_XML, NUM_ACTIONS
from .velocity_env import MicroduckVelocityEnv, _rand


class MicroduckBackflipEnv(MicroduckVelocityEnv):
    def __init__(self, num_envs: int, show_viewer: bool = False, play: bool = False):
        super().__init__(
            num_envs=num_envs,
            rough=False,
            show_viewer=show_viewer,
            play=play,
            robot_xml=MICRODUCK_ALLCOLLISIONS_XML,
            task_name="Backflip-Flat",
            episode_length_s=B.EPISODE_LENGTH_S,
            max_collision_pairs=120,
        )
        self.cfg.update(
            {
                "task": "Backflip-Flat",
                "reward_weights": dict(B.REWARD_WEIGHTS),
                "source_task": "Lulzx/microduck-backflip:Mjlab-Backflip-Flat-MicroDuck",
                "assist": {
                    "start_s": B.ASSIST_START_S,
                    "end_s": B.ASSIST_END_S,
                    "upward_force_n": B.ASSIST_UPWARD_FORCE_N,
                    "backward_pitch_torque_nm": B.ASSIST_BACKWARD_TORQUE_NM,
                },
            }
        )

    def _build_buffers(self) -> None:
        super()._build_buffers()
        n, d = self.num_envs, self.device
        z = torch.zeros(n, dtype=gs.tc_float, device=d)
        b = torch.zeros(n, dtype=torch.bool, device=d)
        l = torch.zeros(n, dtype=torch.long, device=d)

        self.reward_names = list(B.REWARD_WEIGHTS)
        self.reward_weights = dict(B.REWARD_WEIGHTS)
        self.episode_sums = {name: z.clone() for name in self.reward_names}

        self.flip_angle = z.clone()
        self.flip_max = z.clone()
        self.flip_paid = z.clone()
        self.max_z = z.clone()
        self.paid_z = z.clone()
        self.max_vz = z.clone()
        self.paid_vz = z.clone()
        self.max_preload = z.clone()
        self.paid_preload = z.clone()
        self.max_launch_quality = z.clone()
        self.paid_launch_quality = z.clone()
        self.max_push_quality = z.clone()
        self.paid_push_quality = z.clone()
        self.max_feasible_push = z.clone()
        self.paid_feasible_push = z.clone()
        self.had_support = b.clone()
        self.airborne_latch = b.clone()
        self.flight_ended_latch = b.clone()
        self.landed_latch = b.clone()
        self.stable_latch = b.clone()
        self.stable_steps = l.clone()
        self.max_stable_steps = l.clone()
        self.paid_stable_steps = l.clone()
        self.assist_eligible = b.clone()
        self.assist_initialized = b.clone()
        self.spawn_kind = l.clone()
        self.assist_scale = 1.0
        self._assist_window_episodes = 0
        self._assist_window_successes = 0

    def _resample_twist(self, env_ids) -> None:
        self.twist_cmd[env_ids] = 0.0
        self.is_standing_env[env_ids] = True
        self.twist_resample_at[env_ids] = self.max_episode_length + 1

    def _resample_pose_cmd(self, env_ids, buf, ranges, at_buf, resample_s) -> None:
        del ranges, resample_s
        buf[env_ids] = 0.0
        at_buf[env_ids] = self.max_episode_length + 1

    def _resample_due_commands(self) -> None:
        return

    def _maybe_push(self) -> None:
        return

    def _apply_curricula(self) -> None:
        self.com_range = V.stage_value(V.COM_RANGE_STAGES, self.common_step_counter)
        self.head_com_range = V.stage_value(
            V.HEAD_COM_RANGE_STAGES, self.common_step_counter
        )
        self.reward_weights["backflip_preload"] = (
            30.0 if self.common_step_counter < 200 * 24
            else 15.0 if self.common_step_counter < 350 * 24
            else 5.0
        )

    def _update_contacts(self) -> None:
        super()._update_contacts()
        contacts = self.robot.get_contacts(with_entity=self.ground)
        valid = contacts["valid_mask"]
        link_a, link_b = contacts["link_a"], contacts["link_b"]
        per_link = torch.zeros(
            (self.num_envs, self.robot.n_links), dtype=torch.bool, device=self.device
        )
        for local_id in range(self.robot.n_links):
            global_id = self.robot.link_start + local_id
            per_link[:, local_id] = (
                valid & ((link_a == global_id) | (link_b == global_id))
            ).any(dim=1)
        self.ground_link_contact = per_link
        self.feet_ground_contact = per_link[:, self.foot_link_idx].any(dim=1)
        self.robot_ground_contact = per_link.any(dim=1)
        body_mask = torch.ones(self.robot.n_links, dtype=torch.bool, device=self.device)
        body_mask[self.foot_link_idx] = False
        self.body_ground_contact = per_link[:, body_mask].any(dim=1)

    def _update_backflip_state(self) -> None:
        feet = self.feet_ground_contact
        robot = self.robot_ground_contact
        z = torch.nan_to_num(self.base_pos[:, 2], nan=0.0)
        self.had_support |= feet
        newly_airborne = self.had_support & ~robot & (z >= B.MIN_TAKEOFF_Z)
        self.airborne_latch |= newly_airborne
        recontact = self.airborne_latch & robot & ~self.flight_ended_latch
        airborne_now = self.airborne_latch & ~robot & ~self.flight_ended_latch

        omega_back = -torch.nan_to_num(self.base_ang_vel[:, 1], nan=0.0)
        w, x, y, zz = self.base_quat.unbind(-1)
        lateral_axis_z = (2.0 * (y * zz + w * x)).abs()
        flat = torch.clamp((0.866 - lateral_axis_z) / (0.866 - 0.5), 0.0, 1.0)
        flat = flat * flat * (3.0 - 2.0 * flat)
        self.flip_angle += omega_back * self.dt * airborne_now.float() * flat
        self.flip_max = torch.maximum(self.flip_max, self.flip_angle)
        self.max_z = torch.where(
            self.flight_ended_latch, self.max_z, torch.maximum(self.max_z, z)
        )

        upright = self._upright()
        landed = (
            self.airborne_latch
            & recontact
            & feet
            & (self.flip_max >= math.radians(320.0))
            & (upright >= math.cos(math.radians(35.0)))
            & (z >= 0.085)
        )
        self.landed_latch |= landed
        self.flight_ended_latch |= recontact

        stable_now = (
            self.landed_latch
            & (self.flip_max >= 2.0 * math.pi)
            & feet
            & (upright > math.cos(math.radians(20.0)))
            & (z >= 0.095)
            & (self.base_ang_vel.norm(dim=1) < 2.0)
        )
        self.stable_steps = torch.where(
            stable_now, self.stable_steps + 1, torch.zeros_like(self.stable_steps)
        )
        self.max_stable_steps = torch.maximum(self.max_stable_steps, self.stable_steps)
        self.stable_latch |= self.stable_steps >= math.ceil(B.STABLE_HOLD_S / self.dt)

    def _update_task_observation(self) -> None:
        self.twist_cmd.zero_()
        self.head_cmd.zero_()
        self.body_cmd.zero_()
        x = self.episode_length_buf.to(gs.tc_float) * self.dt / 0.30
        self.body_cmd[:, 0] = x.pow(3) / (1.0 + x.pow(3))
        self.body_cmd[:, 1] = float(self.assist_scale)

    def _apply_assist(self, phase_s: torch.Tensor) -> None:
        active = (
            self.assist_eligible
            & ~self.flight_ended_latch
            & (phase_s >= B.ASSIST_START_S)
            & (phase_s < B.ASSIST_END_S)
        )
        amplitude = active.to(gs.tc_float) * float(self.assist_scale)
        wrench = torch.zeros((self.num_envs, 6), dtype=gs.tc_float, device=self.device)
        wrench[:, 2] = amplitude * B.ASSIST_UPWARD_FORCE_N
        torque_b = torch.zeros((self.num_envs, 3), dtype=gs.tc_float, device=self.device)
        torque_b[:, 1] = -amplitude * B.ASSIST_BACKWARD_TORQUE_NM
        wrench[:, 3:6] = transform_by_quat(torque_b, self.robot.get_quat())
        self.robot.control_dofs_force(wrench, list(range(6)))

    def step(self, actions: torch.Tensor):
        # Episode summaries are one-shot.  Keeping the reset dictionary alive
        # would make rsl_rl repeat the same completed episode every step.
        self.extras.pop("episode", None)
        self.last_actions.copy_(self.actions)
        self.actions = torch.clip(actions, -100.0, 100.0)
        constrained = self.assist_eligible & ~self.flight_ended_latch
        authority = torch.ones(self.num_envs, device=self.device)
        authority[constrained] = 1.0 - float(self.assist_scale) * (
            1.0 - B.ASSIST_MIN_ACTION_AUTHORITY
        )
        target = self.default_dof_pos + self.actions * authority.unsqueeze(1)

        phase0 = self.episode_length_buf.to(gs.tc_float) * self.dt
        for substep in range(self.decimation):
            self._apply_assist(phase0 + substep * self.sim_dt)
            tau = self.bam.compute(target)
            self.robot.control_dofs_force(tau, self.motors_dof_idx)
            self.scene.step()

        self.episode_length_buf += 1
        self.common_step_counter += 1
        self._refresh_state()
        self._update_contacts()
        self._update_backflip_state()
        self._apply_curricula()
        self._update_task_observation()
        self._compute_rewards()
        self._check_termination()

        env_ids = self.reset_buf.nonzero(as_tuple=False).flatten()
        if len(env_ids) > 0:
            self.reset_idx(env_ids)
            self._refresh_state()
        obs = self._compute_observations()
        self.extras["time_outs"] = self.time_out_buf
        return obs, self.rew_buf, self.reset_buf, self.extras

    def _progress_gate(self, lo, hi):
        t = torch.clamp((self.flip_max - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    def _upright(self):
        q = self.base_quat
        return 1.0 - 2.0 * (q[:, 1].square() + q[:, 2].square())

    def _standing_score(self, height_std=0.025, upright_std=0.30, pose_std=0.40):
        height = torch.exp(-((self.base_pos[:, 2] - B.STAND_Z) / height_std).square())
        tilt = 1.0 - self._upright()
        upright = torch.exp(-(tilt / upright_std).square())
        idx = torch.tensor(B.LEG_JOINT_IDS, dtype=torch.long, device=self.device)
        pose_err = (self.dof_pos[:, idx] - self.default_dof_pos[idx]).square().mean(1)
        pose = torch.exp(-pose_err / (pose_std * pose_std))
        return height * upright * pose

    def _frontier(self, maximum, paid, normalizer=1.0, cap=None):
        delta = torch.clamp(maximum - paid, min=0.0)
        if cap is not None:
            delta = torch.clamp(delta, max=cap)
        paid.copy_(torch.maximum(paid, maximum))
        return delta / (self.dt * max(normalizer, 1e-6))

    def _autonomy(self):
        return 1.0 - min(max(float(self.assist_scale), 0.0), 1.0)

    def _preload_score(self):
        terms = []
        for idx, target in B.CROUCH_OVERRIDES.items():
            home = self.default_dof_pos[idx]
            terms.append(torch.clamp((self.dof_pos[:, idx] - home) / (target - home), 0.0, 1.0))
        return torch.stack(terms, dim=1).mean(1)

    def _compute_rewards(self) -> None:
        self.rew_buf.zero_()
        feet = self.feet_ground_contact
        airborne = self.airborne_latch & ~self.flight_ended_latch
        vz = torch.clamp(
            torch.nan_to_num(self.robot.get_vel()[:, 2], nan=0.0), min=0.0
        )
        omega = torch.clamp(-torch.nan_to_num(self.base_ang_vel[:, 1], nan=0.0), min=0.0)
        autonomy = self._autonomy()

        self.max_preload = torch.maximum(
            self.max_preload, self._preload_score() * (~self.airborne_latch).float()
        )
        quality = torch.minimum((vz / 1.2).clamp(max=1.0), (omega / 10.0).clamp(max=1.0))
        self.max_launch_quality = torch.maximum(
            self.max_launch_quality, quality * airborne.float()
        )
        push_eligible = feet & ~self.airborne_latch & (self.max_preload >= 0.55)
        self.max_push_quality = torch.maximum(
            self.max_push_quality, quality * push_eligible.float()
        )
        feasible = ((vz - 0.6) / 0.9).clamp(0.0, 1.0) * ((omega - 4.0) / 8.0).clamp(0.0, 1.0)
        self.max_feasible_push = torch.maximum(
            self.max_feasible_push, feasible * push_eligible.float()
        )
        self.max_vz = torch.maximum(self.max_vz, vz * airborne.float())

        completed = self.flip_max >= 2.0 * math.pi
        landed_complete = self.landed_latch & completed
        upright = torch.clamp(self._upright(), 0.0, 1.0)
        gate_late = self._progress_gate(math.radians(270.0), math.radians(340.0))
        tuck_idx = torch.tensor(list(B.TUCK_OVERRIDES), dtype=torch.long, device=self.device)
        tuck_target = torch.tensor(list(B.TUCK_OVERRIDES.values()), device=self.device)
        tuck = torch.exp(-(
            self.dof_pos[:, tuck_idx] - tuck_target
        ).square().mean(1) / (0.35 * 0.35))
        tuck *= self._progress_gate(math.radians(20.0), math.radians(50.0))
        tuck *= 1.0 - self._progress_gate(math.radians(250.0), math.radians(300.0))
        tuck *= airborne.float()

        required = math.ceil(B.STABLE_HOLD_S / self.dt)
        stable_delta = torch.clamp(
            torch.clamp(self.max_stable_steps, max=required)
            - torch.clamp(self.paid_stable_steps, max=required),
            min=0,
        )
        self.paid_stable_steps = torch.maximum(
            self.paid_stable_steps, torch.clamp(self.max_stable_steps, max=required)
        )
        landing_score = self._standing_score()
        terms = {
            "backflip_takeoff": self._frontier(self.max_z.clamp(max=0.30), self.paid_z, 0.30 - B.STAND_Z) * autonomy,
            "backflip_launch_velocity": self._frontier(self.max_vz.clamp(max=1.5), self.paid_vz, 1.5) * autonomy,
            "backflip_preload": self._frontier(self.max_preload, self.paid_preload) * autonomy,
            "backflip_launch_quality": self._frontier(self.max_launch_quality, self.paid_launch_quality) * autonomy,
            "backflip_supported_push": self._frontier(self.max_push_quality, self.paid_push_quality) * autonomy,
            "backflip_feasible_push": self._frontier(self.max_feasible_push, self.paid_feasible_push) * autonomy,
            "backflip_rotation": self._frontier(self.flip_max.clamp(max=2 * math.pi), self.flip_paid, 2 * math.pi, 18.0 * self.dt),
            "backflip_flight_tuck": tuck,
            "backflip_prepare_landing": upright * self._progress_gate(math.radians(250.0), math.radians(340.0)),
            "backflip_landing_approach": self._standing_score(0.12, 0.50, 0.55) * gate_late,
            "backflip_landing": landing_score * landed_complete.float(),
            "backflip_landing_upright": upright * landed_complete.float(),
            "backflip_landing_height": ((self.base_pos[:, 2] - 0.06) / (B.STAND_Z - 0.06)).clamp(0.0, 1.0) * landed_complete.float(),
            "backflip_landing_stillness": torch.exp(-self.base_ang_vel.square().sum(1) / 16.0) * landed_complete.float(),
            "backflip_landing_foot_support": feet.float() * landed_complete.float(),
            "backflip_stability_progress": stable_delta.float() / (required * self.dt),
            "backflip_success": self.stable_latch.float(),
            "backflip_body_contact": (self.airborne_latch & self.body_ground_contact & ~feet).float(),
            "backflip_assisted_action": self.actions.square().mean(1) * self.assist_eligible.float() * float(self.assist_scale),
            "backflip_late_pitch_rate": (omega / 15.0).square() * self._progress_gate(math.radians(300.0), 2 * math.pi) * airborne.float(),
            "backflip_wrong_direction": torch.clamp(self.base_ang_vel[:, 1], min=0.0).square(),
            "backflip_flatness": (2.0 * (self.base_quat[:, 2] * self.base_quat[:, 3] + self.base_quat[:, 0] * self.base_quat[:, 1])).square(),
            "backflip_lateral_velocity": self.base_lin_vel[:, 1].square(),
            "body_ang_vel": self.base_ang_vel[:, [0, 2]].square().sum(1),
            "dof_pos_limits": self._rew_dof_pos_limits(),
        }
        for name, value in terms.items():
            weighted = torch.nan_to_num(
                value * self.reward_weights[name] * self.dt,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )
            self.rew_buf += weighted
            self.episode_sums[name] += weighted

    def _check_termination(self) -> None:
        self.time_out_buf = self.episode_length_buf >= self.max_episode_length
        nan_state = self.scene.rigid_solver.get_error_envs_mask()
        nan_state |= ~torch.isfinite(self.base_pos).all(dim=1)
        nan_state |= ~torch.isfinite(self.dof_pos).all(dim=1)
        out = self.base_pos[:, :2].norm(dim=1) > 1.0
        self.reset_buf = self.time_out_buf | nan_state | out
        self._term_stats = {
            "time_out": self.time_out_buf.float().mean(),
            "nan_state": nan_state.float().mean(),
            "out_of_bounds": out.float().mean(),
        }

    def _maybe_decay_assist(self, env_ids) -> None:
        completed = self.assist_initialized[env_ids] & self.assist_eligible[env_ids]
        if completed.any():
            ids = env_ids[completed]
            self._assist_window_episodes += int(ids.numel())
            self._assist_window_successes += int(self.stable_latch[ids].sum().item())
        if self._assist_window_episodes >= 256:
            rate = self._assist_window_successes / self._assist_window_episodes
            if rate >= 0.60:
                self.assist_scale = max(0.0, self.assist_scale - 0.05)
            self._assist_window_episodes = 0
            self._assist_window_successes = 0

    def reset_idx(self, env_ids) -> None:
        if len(env_ids) == 0:
            return
        self._maybe_decay_assist(env_ids)
        super().reset_idx(env_ids)
        n, d = len(env_ids), self.device

        standing_p, crouch_p, mid_p, recovery_p = B.stage_value(
            B.SPAWN_STAGES, self.common_step_counter
        )
        total = standing_p + crouch_p + mid_p + recovery_p
        sample = torch.rand(n, device=d)
        is_mid = sample < mid_p / total
        is_recovery = (~is_mid) & (sample < (mid_p + recovery_p) / total)
        is_crouch = (~is_mid) & (~is_recovery) & (
            sample < (mid_p + recovery_p + crouch_p) / total
        )
        self.spawn_kind[env_ids] = torch.where(
            is_mid, 2, torch.where(is_recovery, 3, torch.where(is_crouch, 1, 0))
        )

        yaw = _rand(-math.pi, math.pi, (n,), d)
        angle = _rand(math.radians(160.0), math.radians(330.0), (n,), d)
        pitch = _rand(-math.radians(4.0), math.radians(4.0), (n,), d)
        pitch = torch.where(is_mid, -angle, pitch)
        pitch = torch.where(is_recovery, _rand(-math.radians(15.0), math.radians(15.0), (n,), d), pitch)
        pitch = torch.where(is_crouch, _rand(0.0, math.radians(10.0), (n,), d), pitch)
        roll = _rand(-math.radians(4.0), math.radians(4.0), (n,), d)
        roll = torch.where(is_recovery, _rand(-math.radians(15.0), math.radians(15.0), (n,), d), roll)
        cy, sy = torch.cos(yaw / 2), torch.sin(yaw / 2)
        cp, sp = torch.cos(pitch / 2), torch.sin(pitch / 2)
        cr, sr = torch.cos(roll / 2), torch.sin(roll / 2)
        quat = torch.stack(
            [
                cr * cp * cy + sr * sp * sy,
                sr * cp * cy - cr * sp * sy,
                cr * sp * cy + sr * cp * sy,
                cr * cp * sy - sr * sp * cy,
            ],
            dim=1,
        )
        stand_z = _rand(0.11, 0.12, (n,), d)
        mid_z = _rand(0.16, 0.28, (n,), d)
        crouch_z = _rand(0.06, 0.085, (n,), d)
        recovery_z = _rand(0.105, 0.12, (n,), d)
        z = torch.where(is_mid, mid_z, torch.where(is_recovery, recovery_z, torch.where(is_crouch, crouch_z, stand_z)))
        pos = torch.zeros((n, 3), dtype=gs.tc_float, device=d)
        pos[:, 2] = z
        self.robot.set_pos(pos, envs_idx=env_ids)
        self.robot.set_quat(quat, envs_idx=env_ids)

        joints = self.default_dof_pos.unsqueeze(0).repeat(n, 1)
        for idx, target in B.TUCK_OVERRIDES.items():
            factor = _rand(0.5, 1.0, (n,), d)
            joints[:, idx] = torch.where(
                is_mid, joints[:, idx] + factor * (target - joints[:, idx]), joints[:, idx]
            )
        for idx, target in B.CROUCH_OVERRIDES.items():
            factor = _rand(0.55, 1.0, (n,), d)
            joints[:, idx] = torch.where(
                is_crouch, joints[:, idx] + factor * (target - joints[:, idx]), joints[:, idx]
            )
        shaped = is_mid | is_crouch | is_recovery
        joints += torch.randn_like(joints) * 0.05 * shaped.unsqueeze(1)
        self.robot.set_dofs_position(joints, self.motors_dof_idx, envs_idx=env_ids)

        root_vel = torch.zeros((n, 6), dtype=gs.tc_float, device=d)
        omega = _rand(10.0, 18.0, (n,), d)
        root_vel[:, 4] = torch.where(is_mid, -omega, root_vel[:, 4])
        remaining = torch.clamp(2 * math.pi - angle, min=0.0)
        flight_time = torch.clamp(remaining / omega + _rand(0.03, 0.10, (n,), d), min=0.05)
        ballistic_vz = (B.STAND_Z - z + 0.5 * 9.81 * flight_time.square()) / flight_time
        root_vel[:, 2] = torch.where(is_mid, ballistic_vz, root_vel[:, 2])
        recovery_vel = _rand(-0.20, 0.20, (n, 2), d)
        root_vel[:, :2] = torch.where(is_recovery.unsqueeze(1), recovery_vel, root_vel[:, :2])
        recovery_ang = _rand(-1.50, 1.50, (n, 3), d)
        root_vel[:, 3:6] = torch.where(is_recovery.unsqueeze(1), recovery_ang, root_vel[:, 3:6])
        self.robot.set_dofs_velocity(root_vel, list(range(6)), envs_idx=env_ids)

        progress = torch.where(is_mid, angle, torch.where(is_recovery, torch.full_like(angle, 2 * math.pi), torch.zeros_like(angle)))
        for buf in (self.flip_angle, self.flip_max, self.flip_paid):
            buf[env_ids] = progress
        self.max_z[env_ids] = z
        self.paid_z[env_ids] = z
        for maximum, paid in (
            (self.max_vz, self.paid_vz),
            (self.max_launch_quality, self.paid_launch_quality),
            (self.max_push_quality, self.paid_push_quality),
            (self.max_feasible_push, self.paid_feasible_push),
            (self.max_preload, self.paid_preload),
        ):
            maximum[env_ids] = 0.0
            paid[env_ids] = 0.0
        supplied = is_mid | is_recovery
        supplied_ids = env_ids[supplied]
        if len(supplied_ids) > 0:
            supplied_vz = torch.clamp(root_vel[supplied, 2], min=0.0)
            self.max_vz[supplied_ids] = supplied_vz
            self.paid_vz[supplied_ids] = supplied_vz
            for maximum, paid in (
                (self.max_launch_quality, self.paid_launch_quality),
                (self.max_push_quality, self.paid_push_quality),
                (self.max_feasible_push, self.paid_feasible_push),
            ):
                maximum[supplied_ids] = 1.0
                paid[supplied_ids] = 1.0
        shaped_ids = env_ids[shaped]
        if len(shaped_ids) > 0:
            self.max_preload[shaped_ids] = 1.0
            self.paid_preload[shaped_ids] = 1.0
        self.had_support[env_ids] = True
        self.airborne_latch[env_ids] = is_mid | is_recovery
        self.flight_ended_latch[env_ids] = is_recovery
        self.landed_latch[env_ids] = is_recovery
        self.stable_latch[env_ids] = False
        self.stable_steps[env_ids] = 0
        self.max_stable_steps[env_ids] = 0
        self.paid_stable_steps[env_ids] = 0
        self.assist_eligible[env_ids] = ~(is_mid | is_recovery)
        self.assist_initialized[env_ids] = True
        self.twist_cmd[env_ids] = 0.0
        self.head_cmd[env_ids] = 0.0
        self.body_cmd[env_ids] = 0.0
        self._update_task_observation()
