"""In-memory native-world snapshots for short counterfactuals, not NPZ pose replay."""
from __future__ import annotations

import copy
import hashlib
import numbers
from dataclasses import dataclass
import numpy as np

MUTABLE_MODEL = ("dof_damping", "dof_frictionloss")
WORLD_FIELDS = ("motor_delay", "sensor_rows", "last_action", "applied_target", "steps",
                "fell", "command_ramp", "heading_servo", "heading_sensor_history")
OPTIONAL_FIELDS = ("latest", "last_observation", "robot_trail", "target_trail")


def model_fingerprint(model):
    """All exposed numeric compiled arrays, names and numeric solver options.

    Damping/friction are captured separately because BAM updates them at runtime.
    This intentionally refuses cross-model restore; change the timestep AFTER
    restoring the same model, and record that as the diagnostic intervention.
    """
    h = hashlib.sha256()
    for name in sorted(dir(model)):
        if name.startswith("_") or name in MUTABLE_MODEL:
            continue
        value = getattr(model, name)
        if isinstance(value, np.ndarray):
            h.update(name.encode()); h.update(value.dtype.str.encode())
            h.update(repr(value.shape).encode()); h.update(value.tobytes())
        elif isinstance(value, (bytes, str, numbers.Number)):
            h.update((name + repr(value)).encode())
    for name in sorted(dir(model.opt)):
        value = getattr(model.opt, name)
        if isinstance(value, np.ndarray):
            h.update(name.encode()); h.update(value.tobytes())
        elif isinstance(value, numbers.Number):
            h.update((name + repr(value)).encode())
    return h.hexdigest()


@dataclass
class WorldCheckpoint:
    """Use capture/restore on the same source-bound TerrainWorld implementation.

    Whole MjData retains warm starts AND derived solver fields used by BAM.
    Complete Python controller attributes preserve hidden controller histories.
    No extra mj_forward is inserted into physical state during restoration.
    Native clone parity is a mandatory experiment gate, not implied by this type.
    """
    fingerprint: str
    data: object
    sensor_data: object
    model_values: dict
    controller: dict
    world_values: dict
    source_model: object
    source_data: object

    @classmethod
    def capture(cls, world):
        core = world.core
        for name in WORLD_FIELDS:
            if not hasattr(world, name):
                raise ValueError("unsupported world: missing " + name)
        values = {name: copy.deepcopy(getattr(world, name))
                  for name in WORLD_FIELDS + OPTIONAL_FIELDS if hasattr(world, name)}
        memo = {id(core.model): core.model, id(core.data): core.data}
        return cls(model_fingerprint(core.model), copy.copy(core.data),
                   copy.copy(world.sensor_data),
                   {name: getattr(core.model, name).copy() for name in MUTABLE_MODEL},
                   copy.deepcopy(vars(core.controller), memo), values, core.model, core.data)

    def restore(self, world, *, copy_data=None):
        if copy_data is None:
            import mujoco
            copy_data = mujoco.mj_copyData
        core = world.core
        if model_fingerprint(core.model) != self.fingerprint:
            raise ValueError("compiled model/options mismatch")
        for name, value in self.model_values.items():
            getattr(core.model, name)[:] = value
        copy_data(core.data, core.model, self.data)
        copy_data(world.sensor_data, core.model, self.sensor_data)
        memo = {id(self.source_model): core.model, id(self.source_data): core.data}
        controller = copy.deepcopy(self.controller, memo)
        vars(core.controller).clear()
        vars(core.controller).update(controller)
        for name, value in self.world_values.items():
            setattr(world, name, copy.deepcopy(value))
