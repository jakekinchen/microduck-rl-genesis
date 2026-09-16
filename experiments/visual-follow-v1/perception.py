"""Pixel-only marker perception and bounded velocity commands.

No simulator imports or access to target/root poses. This is an artificial,
known-size red-marker detector, not general object recognition or obstacle
avoidance. Fail-stop means an upstream zero command, not instant physical rest.
"""
from dataclasses import dataclass
import math

import numpy as np

DETECTOR_REVISION = "visual-marker-low-light-v2"

@dataclass(frozen=True)
class Camera:
    width: int = 320
    height: int = 240
    vertical_fov_deg: float = 45.0
    marker_radius_m: float = .035

    def __post_init__(self):
        if self.width < 32 or self.height < 32:
            raise ValueError("invalid image dimensions")
        if not 10 <= self.vertical_fov_deg <= 120 or not 0 < self.marker_radius_m < .1:
            raise ValueError("invalid camera intrinsics or known marker size")

    @property
    def focal_px(self):
        return self.height / (2 * math.tan(math.radians(self.vertical_fov_deg) / 2))


@dataclass(frozen=True)
class Detection:
    valid: bool
    reason: str
    bearing_rad: float | None = None
    range_m: float | None = None
    area_px: int = 0
    centroid_uv: tuple | None = None
    component_count: int = 0


def detect(rgb, camera=Camera()):
    """Choose a single compact red component; uncertain images are rejected."""
    rgb = np.asarray(rgb)
    if rgb.dtype != np.uint8 or rgb.shape != (camera.height, camera.width, 3):
        return Detection(False, "malformed_frame")
    values = rgb.astype(np.float32)
    red, green, blue = values.transpose(2, 0, 1)
    # V1's 100/255 brightness assumption rejected the actual, visible marker
    # (R=31..45 in its frozen smoke). V2 retains chromatic separation and
    # introduces explicit absolute/chromatic noise floors for low-light RGB.
    mask = ((red >= 20) & (red-np.maximum(green, blue) >= 12)
            & (red >= 1.7 * green) & (red >= 1.7 * blue))
    # Flood only foreground. This keeps the dependency boundary NumPy-only.
    pending = set(map(tuple, np.argwhere(mask)))
    components = []
    while pending:
        seed = pending.pop()
        stack, pixels = [seed], [seed]
        while stack:
            y, x = stack.pop()
            for point in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                if point in pending:
                    pending.remove(point)
                    pixels.append(point)
                    stack.append(point)
        if len(pixels) >= 9:
            components.append(np.asarray(pixels))
    components.sort(key=len, reverse=True)
    if not components:
        return Detection(False, "no_target")
    p = components[0]
    if len(components) > 1 and len(components[1]) >= .25 * len(p):
        return Detection(False, "ambiguous_targets", component_count=len(components))
    low, high = p.min(0), p.max(0)
    box = high - low + 1
    fill = len(p) / float(np.prod(box))
    if (low <= 1).any() or high[0] >= camera.height-2 or high[1] >= camera.width-2:
        return Detection(False, "clipped_target")
    if max(box) / min(box) > 1.35 or not .62 <= fill <= .88:
        return Detection(False, "noncircular_or_occluded_target")
    if len(p) > camera.width * camera.height * .10:
        return Detection(False, "oversized_target")
    v, u = p.mean(0)
    bearing = math.atan((camera.width / 2 - .5 - u) / camera.focal_px)
    vertical = math.atan((camera.height / 2 - .5 - v) / camera.focal_px)
    radius_px = math.sqrt(len(p) / math.pi)
    # Known-radius angular extent estimate; no target-position or depth buffer.
    distance = camera.marker_radius_m * math.sqrt(1 + (camera.focal_px/radius_px)**2)
    if not .25 <= distance <= 1.8 or abs(vertical) > math.radians(20):
        return Detection(False, "out_of_envelope")
    return Detection(True, "detected", bearing, distance, len(p), (float(u), float(v)), len(components))


class Follower:
    """50 Hz command adapter; two new frames reacquire after any perception loss."""
    max_age_s = .12

    def __init__(self):
        self.latest = Detection(False, "startup")
        self.capture_s = None
        self.sequence = -1
        self.valid_frames = 0
        self.last_now = -math.inf
        self.reason = "startup"

    def ingest(self, detection, capture_s, sequence, now_s):
        if (not isinstance(sequence, int) or not math.isfinite(capture_s)
                or not math.isfinite(now_s) or capture_s > now_s + 1e-9):
            self.latest = Detection(False, "invalid_timestamp")
            self.valid_frames = 0
            return
        if sequence <= self.sequence or (self.capture_s is not None and capture_s <= self.capture_s):
            # Replayed/out-of-order frames do not refresh the freshness timer.
            return
        self.sequence, self.capture_s = sequence, capture_s
        self.latest = detection
        self.valid_frames = self.valid_frames + 1 if detection.valid else 0

    def command(self, now_s):
        command = np.zeros(3, np.float32)
        if not math.isfinite(now_s) or now_s < self.last_now:
            self.reason, self.valid_frames = "invalid_clock", 0
            return command
        self.last_now = now_s
        if self.capture_s is None or now_s - self.capture_s > self.max_age_s + 1e-9:
            self.reason, self.valid_frames = "stale_frame", 0
            return command
        if not self.latest.valid:
            self.reason = self.latest.reason
            return command
        if self.valid_frames < 2:
            self.reason = "reacquiring"
            return command
        bearing, distance = self.latest.bearing_rad, self.latest.range_m
        if (bearing is None or distance is None or not np.isfinite([bearing, distance]).all()
                or not .25 <= distance <= 1.8):
            self.reason, self.valid_frames = "invalid_detection", 0
            return command
        if abs(bearing) > .5:
            self.reason = "bearing_out_of_envelope"
            return command
        if distance <= .60:
            self.reason = "following_distance_reached"
            return command
        command[0] = min(.12, .35 * (distance-.55)) * max(0, math.cos(bearing))
        command[2] = np.clip(1.6 * bearing, -.65, .65)
        self.reason = "following"
        return command
