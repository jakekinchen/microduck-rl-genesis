import unittest
from microduck.braking_v52 import BrakeController
class BrakePhaseTests(unittest.TestCase):
    def test_exact_125_controls_and_retrigger(self):
        b=BrakeController(None)
        for _ in range(100):b.prepare([0,0,0]);self.assertFalse(b.active)
        for _ in range(2):
            b.prepare([.1,0,0]);self.assertFalse(b.active)
            for i in range(126):b.prepare([0,0,0]);self.assertEqual(b.active,i<125)
    def test_restart_cancels_transient(self):
        b=BrakeController(None);b.prepare([.1,0,0]);b.prepare([0,0,0]);self.assertTrue(b.active)
        b.prepare([0,0,.3]);self.assertFalse(b.active)
if __name__=='__main__':unittest.main()
