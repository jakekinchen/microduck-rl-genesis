"""Two separate, opt-in command candidates; unchanged RGB detector/motor actors."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys
import numpy as np


def marker_edge_margin(detection, camera):
    if not detection.valid or detection.centroid_uv is None or detection.area_px <= 0:
        return None
    u, v = detection.centroid_uv
    if not np.isfinite([u, v, detection.area_px]).all():
        return None
    radius = math.sqrt(detection.area_px / math.pi)
    # The same known circular marker assumption as the retained RGB detector.
    return float(min(u - radius, camera.width - 1 - u - radius,
                     v - radius, camera.height - 1 - v - radius))


def edge_limited_twist(command, detection, camera, margin_px=20.):
    value = np.asarray(command)
    if value.dtype != np.float32 or value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError("finite float32 twist required")
    if not math.isfinite(margin_px) or margin_px <= 0:
        raise ValueError("positive edge margin required")
    margin = marker_edge_margin(detection, camera)
    if margin is None:
        return np.zeros(3, np.float32)
    result = value.copy()
    result[0] *= np.clip(margin / margin_px, 0., 1.)
    return result


class ReacquisitionYaw:
    """Slew only the high-level nonzero yaw request. Fault zero is immediate."""
    def __init__(self, rate_rad_s2=1.5, max_control_gap_s=.04):
        if not all(math.isfinite(x) and x > 0 for x in (rate_rad_s2, max_control_gap_s)):
            raise ValueError("finite positive yaw rate/gap required")
        self.rate, self.max_gap = rate_rad_s2, max_control_gap_s
        self.last_s, self.yaw = None, 0.

    def apply(self, command, now_s):
        value = np.asarray(command)
        if value.dtype != np.float32 or value.shape != (3,) or not np.isfinite(value).all():
            raise ValueError("finite float32 twist required")
        if not math.isfinite(now_s) or (self.last_s is not None and now_s < self.last_s):
            self.last_s, self.yaw = None, 0.
            return np.zeros(3, np.float32)
        dt = 0. if self.last_s is None else now_s - self.last_s
        self.last_s = now_s
        if not np.any(value) or dt > self.max_gap:
            self.yaw = 0.
            return np.zeros(3, np.float32)
        result = value.copy()
        self.yaw += float(np.clip(float(value[2]) - self.yaw, -self.rate * dt, self.rate * dt))
        result[2] = self.yaw
        return result


def retained_perception():
    """Load the existing hyphenated experiment directory without modifying it."""
    name = "_microduck_retained_visual_perception"
    if name not in sys.modules:
        path = Path(__file__).resolve().parents[1] / "experiments/visual-follow-v1/perception.py"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError("retained perception source unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    return sys.modules[name]


def make_follower(arm="control", camera=None):
    """Expose one active command intervention per arm. No default promotion."""
    if arm not in ("control", "edge_speed", "reacquisition_yaw"):
        raise ValueError("unknown visual comparison arm")
    legacy = retained_perception()
    camera = legacy.Camera() if camera is None else camera

    class Candidate(legacy.Follower):
        def __init__(self):
            super().__init__()
            self.yaw_slew = ReacquisitionYaw()

        def command(self, now_s):
            value = super().command(now_s)
            if arm == "edge_speed":
                return edge_limited_twist(value, self.latest, camera)
            if arm == "reacquisition_yaw":
                return self.yaw_slew.apply(value, now_s)
            return value

    return Candidate()
