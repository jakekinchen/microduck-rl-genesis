import math
import unittest
import numpy as np
from microduck.persistent_heading_servo_v24 import PersistentHeadingServo


def orientation(yaw):
    return [math.cos(yaw/2), 0., 0., math.sin(yaw/2)]


class HeadingPersistenceTests(unittest.TestCase):
    def test_stop_remains_zero_and_restart_recovers_original_course(self):
        servo = PersistentHeadingServo()
        servo.step([.1, 0, 0], orientation(0))
        for yaw in np.linspace(0, .15, 50):
            command, report = servo.step([0, 0, 0], orientation(yaw))
            np.testing.assert_array_equal(command, [0, 0, 0])
        self.assertAlmostEqual(servo.reference, 0.)
        command, report = servo.step([.1, 0, 0], orientation(.15))
        self.assertLess(command[2], 0.)
        self.assertAlmostEqual(report['heading_error_rad'], -.15)

    def test_unwrap_and_explicit_new_session_reset(self):
        servo = PersistentHeadingServo()
        servo.step([.1, 0, .5], orientation(math.pi-.01))
        servo.step([0, 0, 0], orientation(-math.pi+.01))
        self.assertAlmostEqual(servo.reference, math.pi)
        self.assertAlmostEqual(servo.measured, math.pi+.01)
        servo.reset()
        servo.step([0, 0, 0], orientation(1.))
        self.assertAlmostEqual(servo.reference, 1.)
