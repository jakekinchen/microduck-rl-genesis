import unittest
import numpy as np
from microduck.filtered_heading_servo import FilteredHeadingServo
from microduck.motion_heading_servo_v28 import MotionHeadingServo
from tests.test_persistent_heading_v24 import orientation


class MotionHeadingTests(unittest.TestCase):
    def test_initial_settling_and_first_motion_match_legacy_controller(self):
        old, new = FilteredHeadingServo(), MotionHeadingServo()
        for yaw in np.linspace(0, .2, 50):
            a, _ = old.step([0,0,0], orientation(yaw))
            b, _ = new.step([0,0,0], orientation(yaw))
            np.testing.assert_array_equal(a,b)
            self.assertEqual(old.reference,new.reference)
        self.assertFalse(new.motion_started)
        for yaw in np.linspace(.2, .4, 50):
            a, _ = old.step([0,0,.6], orientation(yaw))
            b, _ = new.step([0,0,.6], orientation(yaw))
            np.testing.assert_array_equal(a,b)
            self.assertEqual(old.reference,new.reference)
        self.assertTrue(new.motion_started)

    def test_later_stops_preserve_course_and_reset_releases_it(self):
        servo=MotionHeadingServo()
        servo.step([0,0,0],orientation(.2))
        servo.step([.1,0,0],orientation(.2))
        reference=servo.reference
        for yaw in np.linspace(.2,.4,20):
            cmd,_=servo.step([0,0,0],orientation(yaw))
            np.testing.assert_array_equal(cmd,[0,0,0])
            self.assertEqual(servo.reference,reference)
        servo.reset()
        servo.step([0,0,0],orientation(1.))
        servo.step([0,0,0],orientation(1.1))
        self.assertAlmostEqual(servo.reference,1.1)
        self.assertFalse(servo.motion_started)
