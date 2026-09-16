"""Versioned timestamp-consistent native sensor observation.

MuJoCo's mj_step advances generalized coordinates but leaves sensor values at
the pre-integration phase. Compute sensor samples on a COPY at the advertised
timestamp; never forward the physical data an extra time or change BAM loads.
"""
import mujoco
import numpy as np
from evaluator.core import projected_gravity
from experiments.walking.world import WalkingWorld


class ConsistentSensorWalkingWorld(WalkingWorld):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_data = mujoco.MjData(self.core.model)
        self.core.observation_vector = self._observation_vector

    def _sample_current_sensors(self):
        mujoco.mj_copyData(self.sensor_data, self.core.model, self.core.data)
        mujoco.mj_forward(self.core.model, self.sensor_data)
        return self.sensor_data

    def _observation_vector(self, last_action, twist, head, body):
        c = self.core
        d = self._sample_current_sensors()
        parts = [d.sensor("imu_ang_vel").data.copy(),
                 projected_gravity(d.sensor("orientation").data.copy()),
                 c.data.qpos[c.qpos_indices]-c.home, c.data.qvel[c.dof_indices],
                 last_action, twist, head, body]
        observation = np.concatenate(parts).astype(np.float32).reshape(1, 61)
        if not np.isfinite(observation).all():
            raise ValueError("nonfinite timestamp-consistent observation")
        return observation

    def step_command(self, command, action_override=None):
        row = super().step_command(command, action_override)
        d = self._sample_current_sensors()
        row["yaw_rate_rad_s"] = float(d.sensor("imu_ang_vel").data[2])
        row["imu_sampling_phase"] = "copied-post-integration-state"
        row["imu_extra_implicit_delay_s"] = 0.
        return row
