"""V19: low-pass only the outer heading correction, never motor actions."""
import math
import numpy as np
from .heading_servo import HeadingServo, MAX_POLICY_YAW_RAD_S

CORRECTION_TAU_S = .12


class FilteredHeadingServo(HeadingServo):
    def reset(self):
        super().reset()
        self.filtered_correction = 0.

    def step(self, requested_twist, orientation_wxyz, dt=.02):
        command, control = super().step(requested_twist, orientation_wxyz, dt)
        raw = control["correction_rad_s"]
        if control["mode"] == "stopped":
            self.filtered_correction = 0.
        else:
            alpha = -math.expm1(-dt/CORRECTION_TAU_S)
            self.filtered_correction += alpha*(raw-self.filtered_correction)
            requested_yaw = float(np.asarray(requested_twist, np.float32)[2])
            command[2] = np.clip(requested_yaw+self.filtered_correction,
                                 -MAX_POLICY_YAW_RAD_S, MAX_POLICY_YAW_RAD_S)
            control["correction_rad_s"] = float(command[2]-requested_yaw)
        control.update(raw_correction_rad_s=raw, filtered_correction_rad_s=self.filtered_correction,
                       correction_tau_s=CORRECTION_TAU_S)
        return command, control
