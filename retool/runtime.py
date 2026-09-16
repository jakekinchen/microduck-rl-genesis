"""Simulation-only lockstep bridge into the retained native world.

This is the body-side compatibility seam, NOT a patched robotd, socket server,
or hardware interface. Rust scheduler/observation parity still needs rehearsal.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Token:
    epoch: str
    step: int

    def __post_init__(self):
        if not isinstance(self.epoch, str) or not self.epoch or type(self.step) is not int or self.step < 0:
            raise ValueError("nonempty epoch and nonnegative integer step required")


def _raw(value, shape, label):
    a = np.asarray(value)
    if a.dtype != np.float32 or a.shape != shape or not np.isfinite(a).all():
        raise ValueError(f"{label}: finite raw float32 {shape} required")
    return a.copy()


class _AssignedAction:
    def __init__(self, observation, action):
        self.observation, self.action, self.calls = observation, action, 0

    def infer(self, observation):
        actual = _raw(observation, (1, 61), "observation")
        if self.calls or actual.tobytes() != self.observation.tobytes():
            raise ValueError("inference count or actor observation mismatch")
        self.calls += 1
        return self.action.reshape(1, 14).copy(), 0.


class LockstepBody:
    def __init__(self, world, epoch, *, preview=None, load_observer=None):
        if preview is None:
            from microduck.native_yaw_env_v55 import preview
        if load_observer is None:
            from experiments.walking.self_load import record_self_loads
            load_observer = record_self_loads
        Token(epoch, 0)
        self.world, self.epoch, self.step = world, epoch, 0
        self.preview, self.load_observer = preview, load_observer
        self.pending, self.poisoned = None, False
        if not math.isclose(float(world.core.model.opt.timestep), .005, rel_tol=0, abs_tol=1e-12):
            raise ValueError("retained bridge requires 200-Hz physics")

    def _check(self, token):
        if self.poisoned or token != Token(self.epoch, self.step):
            raise ValueError("stale token, wrong epoch, or terminal bridge")
        if self.world.fell:
            raise ValueError("fallen world cannot resume")

    def prepare(self, token: Token, requested):
        self._check(token)
        command = _raw(requested, (3,), "requested twist")
        if self.pending is not None:
            if command.tobytes() != self.pending[0].tobytes():
                raise ValueError("different command for pending step")
            return self.pending[1].copy()
        observation = _raw(self.preview(self.world, command), (1, 61), "preview")
        self.pending = (command, observation)
        return observation.copy()

    def advance(self, token: Token, action):
        self._check(token)
        if self.pending is None:
            raise ValueError("prepare must precede advance")
        action = _raw(action, (14,), "actor action")
        world, (command, observation) = self.world, self.pending
        assigned = _AssignedAction(observation, action)
        old = (world.walking_policy, world.standing_policy)
        start_time, start_steps = float(world.core.data.time), int(world.steps)
        world.walking_policy = world.standing_policy = assigned
        try:
            with self.load_observer(world) as loads:
                row = world.step_command(command)
            if assigned.calls != 1 or world.last_action.tobytes() != action.tobytes():
                raise ValueError("altered actor action or missing inference")
            if len(loads) != 4 or not np.isfinite([s["total_normal_n"] for s in loads]).all():
                raise ValueError("four finite physics-rate load samples required")
            if (world.steps != start_steps + 1 or
                    not math.isclose(float(world.core.data.time) - start_time, .02, rel_tol=0, abs_tol=1e-9)):
                raise ValueError("control clock mismatch or hidden reset")
            if (np.asarray(row["motor_torque_physics_nm"]).shape != (4, 14)
                    or not np.isfinite(row["motor_torque_physics_nm"]).all()):
                raise ValueError("four BAM torque updates required")
            result = dict(epoch=self.epoch, step=self.step, row=row,
                          observation=observation.copy(), action=action.copy(), loads=list(loads),
                          proof_class="runtime_component", physical_acceptance=False)
        except BaseException:
            # Physics may already have advanced; never retry a half-completed step.
            self.poisoned = True
            raise
        finally:
            world.walking_policy, world.standing_policy = old
        self.step += 1
        self.pending = None
        return result
