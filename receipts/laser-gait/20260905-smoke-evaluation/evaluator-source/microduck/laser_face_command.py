"""Face-first v3 steering; preserve the canonical body-frame velocity ABI.

The locked HOME head's optical/beak-forward direction is body -X. Turning
changes body yaw normally, but forward approach therefore requests negative
canonical vx. Do not rotate the mesh/camera or reinterpret policy actions.
"""
import numpy as np
from .laser_task import STOP_RADIUS_M, MAX_FORWARD_M_S, MAX_YAW_RAD_S


def face_first_command(relative_xy, visible=True):
    xy = np.asarray(relative_xy, dtype=float)
    if xy.shape != (2,) or not np.isfinite(xy).all() or not visible:
        return np.zeros(3, np.float32)
    distance = np.linalg.norm(xy)
    if distance <= STOP_RADIUS_M:
        return np.zeros(3, np.float32)
    bearing = np.arctan2(-xy[1], -xy[0])
    return np.array([-min(3*(distance-STOP_RADIUS_M), MAX_FORWARD_M_S)*max(float(np.cos(bearing)), 0),
                     0., np.clip(2*bearing, -MAX_YAW_RAD_S, MAX_YAW_RAD_S)], dtype=np.float32)
