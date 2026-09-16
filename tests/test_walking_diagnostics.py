"""Copied-state and scheduled-command diagnostics must expose their limits."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from microduck.constants import DEFAULT_JOINT_POS
from scripts.audit_walking_body_clearance import BodyClearance
from scripts.probe_walking_genesis import command_at, response_metrics


class WalkingDiagnosticTests(unittest.TestCase):
    def test_command_boundaries_are_exact_and_stop_has_no_delay(self):
        suite = {"move_start_s": 1., "stop_start_s": 13.}
        case = {"command": [.12, 0., .4]}
        self.assertEqual(command_at(.98, case, suite), [0., 0., 0.])
        self.assertEqual(command_at(1., case, suite), case["command"])
        self.assertEqual(command_at(12.98, case, suite), case["command"])
        self.assertEqual(command_at(13., case, suite), [0., 0., 0.])

    def test_full_body_clearance_detects_penetration_omitted_by_walk_contacts(self):
        probe = BodyClearance()
        q = np.asarray([0., 0., .125, 1., 0., 0., 0.]+list(DEFAULT_JOINT_POS))
        clear = np.asarray(probe.sample(q))
        self.assertGreater(float(clear.min()), 0.)
        q[2] -= .2
        lowered = np.asarray(probe.sample(q))
        np.testing.assert_allclose(lowered, clear-.2, atol=1e-10)
        self.assertLess(float(lowered.min()), -.001)
        q[12] = np.nan
        with self.assertRaises(ValueError):
            probe.sample(q)

    def test_incomplete_stop_is_missing_not_zero(self):
        row = {"time_s": 2., "command": [.12, 0., 0.], "body_velocity_m_s": [.12, 0., 0.],
               "yaw_rate_rad_s": .3, "speed_m_s": .12, "sole_clearance_m": [.01, 0.],
               "genesis_foot_load_z_n": [0., 7.]}
        result = response_metrics([row])
        self.assertIsNone(result["stop_max_speed_m_s"])
        self.assertAlmostEqual(result["mean_abs_yaw_error_rad_s"], .3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
