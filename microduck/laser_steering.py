"""Versioned deployment-only steering refinement; policy weights stay frozen.

The original 1.5/s distance gain produced a ~25 cm stand-off in visible tests.
The 3/s variant supplies a stronger *ordinary velocity command* near the goal,
under the same 0.25 m/s cap. It changes neither action outputs nor thresholds.
"""
import numpy as np
from .laser_task import target_command, STOP_RADIUS_M, MAX_FORWARD_M_S


def approach_command(relative_xy, visible=True, gain=1.5):
    if gain not in (1.5, 3.0):
        raise ValueError("unversioned approach gain")
    command = target_command(relative_xy, visible)
    if gain == 1.5 or not visible:
        return command
    xy = np.asarray(relative_xy, dtype=float)
    if xy.shape != (2,) or not np.isfinite(xy).all():
        return command
    distance = np.linalg.norm(xy)
    if distance > STOP_RADIUS_M:
        command[0] = min(gain*(distance-STOP_RADIUS_M), MAX_FORWARD_M_S) * max(float(xy[0]/distance), 0.)
    return command
