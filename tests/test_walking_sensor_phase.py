"""Sensor timestamp correction must not alter the physical trajectory itself."""
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import mujoco
from experiments.walking.world import WalkingWorld
from experiments.walking.sensor_world import ConsistentSensorWalkingWorld
from evaluator.core import projected_gravity


class SensorPhaseTests(unittest.TestCase):
    def make(self, cls):
        return cls(ROOT/"receipts/walking/20260905-v3-final/policy.onnx", ROOT/".workspace/bam")

    def test_copy_sensor_sample_is_current_and_does_not_touch_physical_data(self):
        world = self.make(ConsistentSensorWalkingWorld)
        try:
            c = world.core
            c.data.qpos[3:7] = [np.cos(.1), np.sin(.1), 0., 0.]
            c.data.qvel[3:6] = [1., 2., 3.]
            fields = ("qpos", "qvel", "ctrl", "qacc", "qacc_warmstart", "qfrc_bias", "qfrc_constraint", "efc_force", "efc_J")
            before = {name: getattr(c.data, name).copy().tobytes() for name in fields}
            friction = c.model.dof_frictionloss.copy().tobytes()
            old_gyro = c.data.sensor("imu_ang_vel").data.copy()
            obs = world._observation_vector(np.zeros(14), np.zeros(3), np.zeros(4), np.zeros(6))
            np.testing.assert_allclose(obs[0, :3], [1., 2., 3.], atol=1e-6)
            np.testing.assert_allclose(obs[0, 3:6], projected_gravity(c.data.qpos[3:7]), atol=1e-6)
            self.assertFalse(np.allclose(old_gyro, obs[0, :3]))
            for name in fields:
                self.assertEqual(before[name], getattr(c.data, name).tobytes(), name)
            self.assertEqual(friction, c.model.dof_frictionloss.tobytes())
        finally:
            world.close()

    def test_identical_override_actions_keep_physics_byte_identical(self):
        old, new = self.make(WalkingWorld), self.make(ConsistentSensorWalkingWorld)
        try:
            rng = np.random.default_rng(76545)
            for _ in range(50):
                action = rng.normal(0., .02, 14).astype(np.float32)
                old.step_command([.12, 0., .5], action_override=action)
                new.step_command([.12, 0., .5], action_override=action)
                self.assertEqual(old.last_action.tobytes(), new.last_action.tobytes())
                for name in ("qpos", "qvel", "ctrl", "qacc", "qfrc_constraint"):
                    self.assertEqual(getattr(old.core.data, name).tobytes(), getattr(new.core.data, name).tobytes(), name)
        finally:
            old.close()
            new.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
