import math
import unittest
import numpy as np
from microduck.heading_servo import HeadingServo, imu_heading


def quat(yaw):
    return [math.cos(yaw/2), 0, 0, math.sin(yaw/2)]


class HeadingServoTests(unittest.TestCase):
    def test_correcting_sign_and_bounds(self):
        servo = HeadingServo()
        servo.step([.12, 0, 0], quat(0))
        command, state = servo.step([.12, 0, 0], quat(.3))
        self.assertAlmostEqual(float(command[2]), -.25)
        self.assertAlmostEqual(float(command[0]), .12)
        self.assertLess(state['heading_error_rad'], 0)

    def test_perfect_turn_preserves_feedforward(self):
        servo = HeadingServo()
        for i in range(900):
            command, state = servo.step([0, 0, .5], quat(i*.02*.5))
            self.assertAlmostEqual(float(command[2]), .5, places=6)
            self.assertAlmostEqual(state['heading_error_rad'], 0., places=6)

    def test_wrap_is_continuous(self):
        servo = HeadingServo()
        servo.step([.1, 0, .5], quat(math.pi-.005))
        command, state = servo.step([.1, 0, .5], quat(-math.pi+.005))
        self.assertAlmostEqual(state['heading_error_rad'], 0., places=6)
        self.assertAlmostEqual(float(command[2]), .5)

    def test_stop_is_exact_zero_and_resets_reference(self):
        servo = HeadingServo()
        servo.step([.12, 0, .5], quat(0))
        for _ in range(50):
            command, state = servo.step([0, 0, 0], quat(.3))
            np.testing.assert_array_equal(command, np.zeros(3, np.float32))
        command, state = servo.step([.12, 0, 0], quat(.3))
        self.assertEqual(state['heading_error_rad'], 0.)

    def test_total_policy_command_is_bounded(self):
        servo = HeadingServo()
        servo.step([.12, 0, .6], quat(0))
        command, _ = servo.step([.12, 0, .6], quat(-1))
        self.assertEqual(float(command[2]), .75)

    def test_invalid_orientation_and_commands_refused(self):
        for q in ([0]*4, [float('nan')]*4, [1, 0, 0], quat(0)*2,
                  [math.sqrt(.5), 0, math.sqrt(.5), 0]):
            with self.assertRaises(ValueError):
                imu_heading(q)
        for command in ([0, 0, float('nan')], [0, 0, 1], [0, 0]):
            with self.assertRaises(ValueError):
                HeadingServo().step(command, quat(0))
        with self.assertRaises(ValueError):
            HeadingServo().step([.1, 0, 0], quat(0), dt=.01)

    def test_reset_discards_old_reference(self):
        servo = HeadingServo()
        servo.step([.1, 0, 0], quat(0))
        servo.reset()
        command, state = servo.step([.1, 0, 0], quat(2))
        self.assertEqual(state['heading_error_rad'], 0.)


if __name__ == '__main__':
    unittest.main()
