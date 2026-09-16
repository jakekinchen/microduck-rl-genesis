"""Additive planar-heading fidelity; never rewrites the frozen motor battery.

Yaw-rate MAE allows a small persistent error to accumulate into a large wrong
heading. Measure the actual trunk heading against the requested planar turn.
"""
import math
import numpy as np

THRESHOLDS = {"endpoint_heading_error_deg": 15., "maximum_heading_error_deg": 20.}


def heading_metrics(rows):
    selected = [r for r in rows if 2. - 1e-9 <= r["time_s"] <= 13. + 1e-9]
    if len(selected) != 551:
        raise ValueError("complete 50-Hz 2..13-second heading window required")
    t = np.asarray([r["time_s"] for r in selected], float)
    q = np.asarray([r["qpos"] for r in selected], float)
    command = np.asarray([r["command"] for r in selected], float)
    if (q.shape != (551, 21) or command.shape != (551, 3)
            or not np.isfinite(np.r_[t, q.ravel(), command.ravel()]).all()
            or not np.allclose(np.diff(t), .02, rtol=0., atol=1e-8)):
        raise ValueError("invalid time, pose or command evidence")
    quat = q[:, 3:7]
    if not np.allclose(np.linalg.norm(quat, axis=1), 1., atol=1e-5, rtol=0.):
        raise ValueError("non-unit body quaternion")
    w, x, y, z = quat.T
    forward_x = 1. - 2. * (y*y + z*z)
    forward_y = 2. * (x*y + w*z)
    if np.any(np.hypot(forward_x, forward_y) < .25):
        raise ValueError("body forward has no reliable horizontal heading")
    measured = np.unwrap(np.arctan2(forward_y, forward_x))
    measured -= measured[0]
    requested = np.r_[0., np.cumsum(command[:-1, 2] * np.diff(t))]
    error = measured - requested
    return {"endpoint_heading_error_deg": float(abs(np.rad2deg(error[-1]))),
            "maximum_heading_error_deg": float(np.rad2deg(np.abs(error).max())),
            "signed_endpoint_heading_error_deg": float(np.rad2deg(error[-1])),
            "measured_heading_change_deg": float(np.rad2deg(measured[-1])),
            "requested_heading_change_deg": float(np.rad2deg(requested[-1]))}


def evaluate_heading(rows):
    try:
        metrics = heading_metrics(rows)
        failures = [key for key, limit in THRESHOLDS.items() if metrics[key] > limit]
    except (KeyError, ValueError, TypeError, IndexError):
        metrics, failures = {}, ["missing_or_invalid_heading_evidence"]
    return {"passed": not failures, "metrics": metrics, "thresholds": dict(THRESHOLDS),
            "failures": failures, "boundary": "Additive exposed-development planar-heading fidelity, not physical yaw calibration. Preserve old motor scores separately."}
