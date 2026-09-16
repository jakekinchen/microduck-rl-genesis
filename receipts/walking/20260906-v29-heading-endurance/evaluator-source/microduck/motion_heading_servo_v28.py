"""Establish course at first motion; preserve it through subsequent STOP."""
from .filtered_heading_servo import FilteredHeadingServo
from .persistent_heading_servo_v24 import PersistentHeadingServo


class MotionHeadingServo(PersistentHeadingServo):
    def reset(self):
        super().reset()
        self.motion_started = False

    def step(self, requested_twist, orientation_wxyz, dt=.02):
        if not self.motion_started:
            command, control = FilteredHeadingServo.step(self, requested_twist, orientation_wxyz, dt)
            self.motion_started = control['mode'] != 'stopped'
            control['reference_preserved_through_stop'] = self.motion_started
            return command, control
        return super().step(requested_twist, orientation_wxyz, dt)
