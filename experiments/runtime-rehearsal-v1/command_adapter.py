"""Retained V30 command preprocessing for a future isolated runtime adapter.

This component owns command shaping and actor selection only. It never opens a
socket or device, steps physics, rewrites a pose, or modifies an actor's output.
It is not a complete replacement for robotd or the BAM body transport.
"""
from collections import deque

import numpy as np

from experiments.walking.command_ramp import CommandRamp
from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
from microduck.constants import DEFAULT_JOINT_POS


class RetainedCommandAdapter:
    def __init__(self, sensor_ticks=1):
        if sensor_ticks not in (0, 1):
            raise ValueError("Retained sensor delay must be zero or one control tick")
        self.sensor_ticks = sensor_ticks
        self.reset()

    def reset(self):
        """Only at the episode boundary, never at a walk/stand transition."""
        self.ramp = CommandRamp()
        self.heading = Float32HeadingHeadroomServo()
        self.orientation_history = deque(maxlen=2)

    def step(self, requested, sampled_orientation_wxyz):
        q = np.asarray(sampled_orientation_wxyz, dtype=np.float64)
        if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q)-1) > 1e-5:
            raise ValueError("A finite unit sampled IMU quaternion is required")
        routed = self.ramp.step(requested)
        # Selection precedes heading correction, exactly as StandingSwitchWalkingWorld.
        mode = "standing" if np.all(routed == 0) else "walking"
        self.orientation_history.append(q.copy())
        delayed = self.orientation_history[max(0, len(self.orientation_history)-1-self.sensor_ticks)]
        policy_command, heading = self.heading.step(routed, delayed)
        return {"actor_mode": mode, "routing_command": routed,
                "policy_command": policy_command, "heading_control": heading}

    @staticmethod
    def motor_reference(action):
        """The unchanged float32 action determines the unfiltered radian target."""
        action = np.asarray(action)
        if action.dtype != np.float32 or action.shape != (14,) or not np.isfinite(action).all():
            raise ValueError("Exactly 14 finite raw float32 actor outputs are required")
        return np.asarray(DEFAULT_JOINT_POS, dtype=np.float64) + action.astype(np.float64)
