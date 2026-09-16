"""V29: bounded heading-correction headroom above the requested yaw envelope."""
import math
import numpy as np
from .motion_heading_servo_v28 import MotionHeadingServo
from .heading_servo import HEADING_GAIN_PER_S, MAX_CORRECTION_RAD_S
from .filtered_heading_servo import CORRECTION_TAU_S

POLICY_YAW_LIMIT_RAD_S = .8


class HeadingHeadroomServo(MotionHeadingServo):
    def step(self, requested_twist, orientation_wxyz, dt=.02):
        previous_filtered = self.filtered_correction
        command, control = super().step(requested_twist, orientation_wxyz, dt)
        if control['mode'] != 'stopped':
            requested_yaw = float(np.asarray(requested_twist,np.float32)[2])
            raw = float(np.clip(HEADING_GAIN_PER_S*control['heading_error_rad'],
                                -MAX_CORRECTION_RAD_S,MAX_CORRECTION_RAD_S))
            raw = float(np.clip(requested_yaw+raw,-POLICY_YAW_LIMIT_RAD_S,POLICY_YAW_LIMIT_RAD_S))-requested_yaw
            alpha = -math.expm1(-dt/CORRECTION_TAU_S)
            self.filtered_correction = previous_filtered+alpha*(raw-previous_filtered)
            command[2] = np.clip(requested_yaw+self.filtered_correction,
                                 -POLICY_YAW_LIMIT_RAD_S,POLICY_YAW_LIMIT_RAD_S)
            control.update(raw_correction_rad_s=raw,filtered_correction_rad_s=self.filtered_correction,
                           correction_rad_s=float(command[2]-requested_yaw))
        control['policy_yaw_limit_rad_s'] = POLICY_YAW_LIMIT_RAD_S
        return command, control
