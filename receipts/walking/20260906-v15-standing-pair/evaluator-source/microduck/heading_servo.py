"""Explicit IMU-to-velocity-command heading servo; never edits motor actions.

This is an upstream controller, not improved raw-policy performance. It needs
the orientation estimate outside the existing 61D actor input. Physical use
requires an independently validated IMU orientation source.
"""
import math
import numpy as np

HEADING_GAIN_PER_S = 2.
MAX_CORRECTION_RAD_S = .25
MAX_POLICY_YAW_RAD_S = .75


def imu_heading(quaternion):
    q = np.asarray(quaternion, float)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q)-1.) > 1e-5:
        raise ValueError("finite unit wxyz IMU quaternion required")
    w, x, y, z = q
    forward_x, forward_y = 1-2*(y*y+z*z), 2*(x*y+w*z)
    if math.hypot(forward_x, forward_y) < .25:
        raise ValueError("IMU heading projection is unreliable")
    return math.atan2(forward_y, forward_x)


class HeadingServo:
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous_wrapped = None
        self.measured = None
        self.reference = None

    def step(self, requested_twist, orientation_wxyz, dt=.02):
        requested = np.asarray(requested_twist, np.float32)
        if requested.shape != (3,) or not np.isfinite(requested).all() or dt != .02:
            raise ValueError("finite twist at the versioned 50-Hz rate required")
        if abs(requested[2]) > MAX_POLICY_YAW_RAD_S:
            raise ValueError("requested yaw outside the controller envelope")
        wrapped = imu_heading(orientation_wxyz)
        if self.previous_wrapped is None:
            self.measured = self.reference = wrapped
        else:
            self.measured += math.atan2(math.sin(wrapped-self.previous_wrapped), math.cos(wrapped-self.previous_wrapped))
        self.previous_wrapped = wrapped
        if not np.any(requested):
            # A stop means no residual turn request; discard the moving target.
            self.reference = self.measured
            return np.zeros(3, np.float32), {"mode": "stopped", "heading_error_rad": 0., "correction_rad_s": 0.}
        error = self.reference-self.measured
        correction = float(np.clip(HEADING_GAIN_PER_S*error, -MAX_CORRECTION_RAD_S, MAX_CORRECTION_RAD_S))
        command = requested.copy()
        command[2] = np.clip(float(requested[2])+correction, -MAX_POLICY_YAW_RAD_S, MAX_POLICY_YAW_RAD_S)
        result = {"mode": "tracking", "heading_error_rad": error,
                  "correction_rad_s": float(command[2]-requested[2]),
                  "measured_unwrapped_heading_rad": self.measured,
                  "reference_heading_rad": self.reference}
        self.reference += float(requested[2])*dt
        return command, result
