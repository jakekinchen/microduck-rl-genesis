from pathlib import Path
import tempfile
import unittest
import numpy as np
from experiments.walking.collision_model import ASSETS, materialize
from experiments.walking.self_contact import SelfContactProbe, evaluate_self_contact

# Actual v9 FINAL nominal forward08 at 0.90 s; raw CAD triangle witness is
# retained in 20260905-v9-raw-cad-intersections-r2. No inferred joint poses.
WITNESS = [0.006800916572056543, 0.008902965678510202, 0.08081032724961865,
           0.9600238875242566, -0.02856732846442395, 0.041796877484785756, 0.27530176926373134,
           -0.2942459382173295, -0.10530092005727545, 0.24826334040427556, 1.2188363328836054,
           0.8775132809663936, 0.19740046830992464, 0.4941746743442645, 0.05051990078218306,
           0.06759209745201591, 0.23065618566768253, 0.13912449078291617, 0.06198916551686256,
           -1.1949935502949829, -1.1720004746739199]


class SelfContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from microduck.constants import DEFAULT_JOINT_POS
        cls.temporary = tempfile.TemporaryDirectory(prefix='duck-self-contact-')
        _, scene = materialize(cls.temporary.name)
        cls.probe = SelfContactProbe(scene)
        cls.home = np.r_[0., 0., .125, 1., 0., 0., 0., DEFAULT_JOINT_POS].tolist()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_real_battery_witness_rejected(self):
        result = evaluate_self_contact([{"time_s": .02, "qpos": WITNESS}], self.probe, 1)
        self.assertFalse(result['passed'])
        self.assertIn('self_penetration_over_1mm', result['failures'])
        self.assertGreater(result['maximum_self_penetration_m'], .001)

    def test_home_geometry_clear_not_standing_dynamics_proof(self):
        self.assertTrue(evaluate_self_contact([{'time_s': .02, 'qpos': self.home}], self.probe, 1)['passed'])

    def test_missing_and_nonfinite_fail_closed(self):
        for q in (None, [0]*20, [float('nan')]*21, [0]*21):
            self.assertFalse(evaluate_self_contact([{'time_s': .02, 'qpos': q}], self.probe, 1)['passed'])

    def test_incomplete_or_wrong_time_fail_closed(self):
        self.assertFalse(evaluate_self_contact([], self.probe)['passed'])
        self.assertFalse(evaluate_self_contact([{'time_s': .03, 'qpos': self.home}], self.probe, 1)['passed'])

    def test_reduced_model_cannot_certify_coverage(self):
        with self.assertRaises(ValueError):
            SelfContactProbe(ASSETS/'scene_walk.xml')


if __name__ == '__main__':
    unittest.main()
