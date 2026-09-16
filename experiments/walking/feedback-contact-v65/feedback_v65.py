"""Read-only solver-force snapshots for the V65 BAM input-age intervention."""
from collections import deque
from dataclasses import dataclass
from types import MappingProxyType
import numpy as np

FORCE_FIELDS = ('qfrc_bias', 'qfrc_constraint', 'qfrc_actuator',
                'efc_id', 'efc_type', 'efc_force')


@dataclass(frozen=True)
class ForceSnapshot:
    step: int
    solver_time: float
    captured_time: float
    fields: object

    @classmethod
    def capture(cls, data, step, solver_time):
        fields = {}
        for name in FORCE_FIELDS:
            value = np.array(getattr(data, name), copy=True)
            if not np.isfinite(value).all():
                raise ValueError('nonfinite solver field: ' + name)
            value.flags.writeable = False
            fields[name] = value
        if data.time < solver_time - 1e-10:
            raise ValueError('future solver timestamp')
        return cls(step, float(solver_time), float(data.time), MappingProxyType(fields))

    def record(self):
        return {'step': self.step, 'solver_time_s': self.solver_time,
                'captured_time_s': self.captured_time,
                **{k: v.tolist() for k, v in self.fields.items()}}


class ForceHistory:
    def __init__(self, subdivisions, initial):
        if subdivisions not in (1, 2, 4) or initial.step != -1:
            raise ValueError('invalid reset snapshot or subdivision')
        self.subdivisions = subdivisions
        self.dt = .005 / subdivisions
        self.history = deque([initial], maxlen=subdivisions + 1)

    def append(self, snapshot):
        if snapshot.step != self.history[-1].step + 1:
            raise ValueError('missing or duplicate force sample')
        if abs(snapshot.solver_time - snapshot.step * self.dt) > 1e-8:
            raise ValueError('solver timestamp does not match interval start')
        if abs(snapshot.captured_time - (snapshot.step + 1) * self.dt) > 1e-8:
            raise ValueError('capture timestamp does not match interval end')
        self.history.append(snapshot)

    def select(self, tick, mode, current_time):
        if mode not in ('native', 'fixed_5ms') or tick < 0:
            raise ValueError('unknown feedback mode or negative tick')
        if abs(current_time - tick * .005) > 1e-8:
            raise ValueError('BAM clock mismatch')
        latest = tick * self.subdivisions - 1
        if self.history[-1].step != latest:
            raise ValueError('missing or future force history')
        wanted = -1 if tick == 0 else (latest if mode == 'native'
                                      else (tick - 1) * self.subdivisions)
        for snapshot in self.history:
            if snapshot.step == wanted:
                age = current_time - snapshot.solver_time
                expected = 0. if tick == 0 else (self.dt if mode == 'native' else .005)
                if abs(age - expected) > 1e-8:
                    raise ValueError('unexpected physical force-input age')
                return snapshot
        raise ValueError('required snapshot evicted or missing')


class ControllerData:
    """Only ctrl writes reach physical data; force reads use the chosen snapshot."""
    def __init__(self, physical, snapshot):
        self._physical = physical
        self._snapshot = snapshot
        self.reads = set()

    def __getattr__(self, name):
        self.reads.add(name)
        if name in FORCE_FIELDS:
            return self._snapshot.fields[name]
        if name in ('time', 'ctrl'):
            return getattr(self._physical, name)
        if name in ('qpos', 'qvel'):
            view = getattr(self._physical, name).view()
            view.flags.writeable = False
            return view
        raise AttributeError('unreviewed BAM data access: ' + name)


def force_inputs(snapshot, dofs, joints, friction_type):
    f = snapshot.fields
    selector = (np.asarray(joints)[:, None] == f['efc_id'][None, :]) & (
        f['efc_type'][None, :] == friction_type)
    friction = np.sum(f['efc_force'][None, :] * selector, axis=1)
    return {'bias_nm': f['qfrc_bias'][dofs].tolist(),
            'constraint_nm': f['qfrc_constraint'][dofs].tolist(),
            'actuator_nm': f['qfrc_actuator'][dofs].tolist(),
            'subtracted_dof_friction_nm': friction.tolist(),
            'external_nm': (-f['qfrc_bias'][dofs] + f['qfrc_constraint'][dofs] - friction).tolist()}


def update_with_snapshot(controller, physical, snapshot, tick):
    before = {name: getattr(physical, name).copy() for name in FORCE_FIELDS}
    qpos, qvel, now = physical.qpos.copy(), physical.qvel.copy(), float(physical.time)
    view = ControllerData(physical, snapshot)
    assert controller.mujoco_data is physical
    controller.mujoco_data = view
    try:
        controller.update()
    finally:
        controller.mujoco_data = physical
    for name, value in before.items():
        np.testing.assert_array_equal(getattr(physical, name), value, err_msg='physical solver field changed: ' + name)
    np.testing.assert_array_equal(physical.qpos, qpos)
    np.testing.assert_array_equal(physical.qvel, qvel)
    assert physical.time == now
    assert view.reads == set(FORCE_FIELDS) | {'qpos', 'qvel', 'ctrl', 'time'}, view.reads
    return {'bam_tick': tick, 'time_s': now, 'snapshot_step': snapshot.step,
            'snapshot_solver_time_s': snapshot.solver_time,
            'snapshot_captured_time_s': snapshot.captured_time,
            'force_input_age_s': now - snapshot.solver_time,
            'physical_solver_fields_unchanged': True, 'fields_read': sorted(view.reads),
            'qpos': qpos.tolist(), 'qvel': qvel.tolist(),
            **force_inputs(snapshot, controller.dof_indexes, controller.joint_indexes, 1),
            'ctrl_nm': physical.ctrl.tolist(),
            'frictionloss_nm': controller.mujoco_model.dof_frictionloss[controller.dof_indexes].tolist(),
            'damping': controller.mujoco_model.dof_damping[controller.dof_indexes].tolist()}
