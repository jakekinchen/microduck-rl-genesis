"""Pure laser-following geometry, perception, and reward primitives (v1).

The steering layer outputs ordinary velocity commands; only the locomotion
policy outputs joint actions. Ground-truth targets are NOT camera detections.
"""
from __future__ import annotations

import numpy as np

STOP_RADIUS_M = 0.18
MAX_FORWARD_M_S = 0.25
MAX_YAW_RAD_S = 1.0


def target_command(relative_xy, visible=True):
    """Body-yaw-frame target -> canonical vx, vy, wz; fail closed on loss."""
    xy = np.asarray(relative_xy, dtype=float)
    if xy.shape != (2,) or not np.isfinite(xy).all() or not visible:
        return np.zeros(3, dtype=np.float32)
    distance = np.linalg.norm(xy)
    if distance <= STOP_RADIUS_M:
        return np.zeros(3, dtype=np.float32)
    bearing = np.arctan2(xy[1], xy[0])
    return np.array([
        min(1.5 * (distance - STOP_RADIUS_M), MAX_FORWARD_M_S)
        * max(float(np.cos(bearing)), 0.0),
        0.0, np.clip(2.0 * bearing, -MAX_YAW_RAD_S, MAX_YAW_RAD_S),
    ], dtype=np.float32)


def world_to_body_xy(target, robot_xy, quaternion_wxyz):
    w, x, y, z = quaternion_wxyz
    yaw = np.arctan2(2 * (w*z + x*y), 1 - 2 * (y*y + z*z))
    delta = np.asarray(target) - np.asarray(robot_xy)
    return np.array([np.cos(yaw)*delta[0] + np.sin(yaw)*delta[1],
                     -np.sin(yaw)*delta[0] + np.cos(yaw)*delta[1]])


def detect_red_spot(rgb, *, min_pixels=2, max_pixels=150):
    """Conservative RGB connected-component detector; ambiguous scenes -> None.

    Returns pixel coordinates only, never an invented metric distance. A
    calibrated camera/ground-plane transform is required before real control.
    """
    from scipy.ndimage import label
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("expected HxWx3 uint8 RGB")
    r, g, b = np.moveaxis(rgb.astype(np.int16), -1, 0)
    mask = (r >= 180) & (r - g >= 70) & (r - b >= 70)
    components, count = label(mask)
    candidates = []
    for index in range(1, count + 1):
        yy, xx = np.nonzero(components == index)
        if min_pixels <= len(xx) <= max_pixels:
            # Reject long red edges/lines; do not choose the biggest red object.
            aspect = (xx.max() - xx.min() + 1) / (yy.max() - yy.min() + 1)
            if 0.4 <= aspect <= 2.5:
                candidates.append((float(xx.mean()), float(yy.mean())))
    return candidates[0] if len(candidates) == 1 else None
