import unittest
import numpy as np
from microduck.heading_headroom_v29 import HeadingHeadroomServo
from microduck.motion_heading_servo_v28 import MotionHeadingServo
from tests.test_persistent_heading_v24 import orientation


class HeadroomTests(unittest.TestCase):
    def test_unsaturated_feedback_and_stop_match_v28(self):
        a,b=MotionHeadingServo(),HeadingHeadroomServo()
        for command,yaw in [([0,0,0],.2),([.1,0,0],.2),([.1,0,0],.19),([0,0,0],.25)]:
            x,_=a.step(command,orientation(yaw));y,_=b.step(command,orientation(yaw))
            np.testing.assert_array_equal(x,y)
            self.assertEqual(a.reference,b.reference)

    def test_correction_has_bounded_headroom_and_zero_stop(self):
        s=HeadingHeadroomServo();s.step([0,0,0],orientation(0))
        for _ in range(100):cmd,_=s.step([0,0,.738],orientation(0))
        self.assertGreater(cmd[2],.75)
        self.assertLessEqual(float(cmd[2]),.80000002)
        reference=s.reference
        cmd,_=s.step([0,0,0],orientation(.1))
        np.testing.assert_array_equal(cmd,[0,0,0]);self.assertEqual(reference,s.reference)
        with self.assertRaises(ValueError):s.step([0,0,.81],orientation(.1))
