"""Input-history correctness and isolation; no robot simulation or training."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feedback_v65 import ForceSnapshot, ForceHistory, ControllerData, force_inputs


def data(time=0.):
    return SimpleNamespace(time=time, qpos=np.array([3., 4.]), qvel=np.array([5., 6.]),
        ctrl=np.zeros(2), qfrc_bias=np.array([1., 2.]), qfrc_constraint=np.array([10., 20.]),
        qfrc_actuator=np.array([.1, .2]), efc_id=np.array([2, 2, 3]),
        efc_type=np.array([1, 6, 1]), efc_force=np.array([3., 99., 4.]))


class FeedbackTests(unittest.TestCase):
    def test_snapshots_are_independent_readonly_and_variable_constraint_size(self):
        d = data(); s = ForceSnapshot.capture(d, -1, 0.)
        d.efc_force[:] = 100
        np.testing.assert_array_equal(s.fields['efc_force'], [3., 99., 4.])
        with self.assertRaises(ValueError): s.fields['efc_force'][0] = 9
        with self.assertRaises(TypeError): s.fields['efc_force'] = np.zeros(1)
        d.efc_force = np.zeros(0); d.efc_id = d.efc_type = np.zeros(0, dtype=int)
        self.assertEqual(len(ForceSnapshot.capture(d, 0, 0.).fields['efc_force']), 0)

    def test_fixed_age_selects_first_solver_of_previous_tick(self):
        for n in (1, 2, 4):
            d = data(); h = ForceHistory(n, ForceSnapshot.capture(d, -1, 0.))
            self.assertEqual(h.select(0, 'fixed_5ms', 0.).step, -1)
            for i in range(3*n):
                d.time = (i+1)*.005/n
                h.append(ForceSnapshot.capture(d, i, i*.005/n))
                if (i+1) % n == 0:
                    tick = (i+1)//n
                    self.assertEqual(h.select(tick, 'native', d.time).step, i)
                    self.assertEqual(h.select(tick, 'fixed_5ms', d.time).step, (tick-1)*n)

    def test_missing_stale_future_and_wrong_clock_rejected(self):
        d = data(); h = ForceHistory(4, ForceSnapshot.capture(d, -1, 0.))
        with self.assertRaises(ValueError): h.select(1, 'fixed_5ms', .005)
        with self.assertRaises(ValueError): h.select(0, 'native', .001)
        with self.assertRaises(ValueError): h.select(0, 'unknown', 0.)
        d.time = .0025
        with self.assertRaises(ValueError): h.append(ForceSnapshot.capture(d, 1, .00125))
        with self.assertRaises(ValueError): ForceSnapshot.capture(d, 1, .003)

    def test_friction_subtraction_uses_joint_and_constraint_type(self):
        s = ForceSnapshot.capture(data(), -1, 0.)
        v = force_inputs(s, [0, 1], [2, 3], 1)
        self.assertEqual(v['subtracted_dof_friction_nm'], [3., 4.])
        self.assertEqual(v['external_nm'], [6., 14.])

    def test_proxy_preserves_physical_force_and_state_arrays(self):
        d = data(); s = ForceSnapshot.capture(d, -1, 0.); p = ControllerData(d, s)
        p.ctrl[:] = [7., 8.]
        np.testing.assert_array_equal(d.ctrl, [7., 8.])
        with self.assertRaises(ValueError): p.qpos[0] = 0
        with self.assertRaises(ValueError): p.qfrc_constraint[0] = 0
        self.assertEqual(d.qfrc_constraint[0], 10.)
        with self.assertRaises(AttributeError): _ = p.qacc

    def test_nonfinite_forces_rejected(self):
        d = data(); d.qfrc_bias[0] = np.nan
        with self.assertRaises(ValueError): ForceSnapshot.capture(d, -1, 0.)


if __name__ == '__main__': unittest.main()
