"""Deterministic moving-target programs and frozen flat-domain test draws."""
import math
import numpy as np

PROGRAMS = ("retarget", "circle", "figure-eight", "manual")
WAYPOINTS = ((0, (.6, 0)), (7, (.6, .55)), (14, (-.15, .45)),
             (22, (-.25, -.35)), (30, (.5, -.25)), (40, (.4, .45)))


def program_target(mode, t, *, rotation=0.):
    visible = True
    if mode == "retarget":
        i = max(i for i, (start, _) in enumerate(WAYPOINTS) if t >= start)
        xy = np.array(WAYPOINTS[i][1], dtype=float)
        visible = not 38 <= t < 40
        label = "Target hidden" if not visible else f"Waypoint {i+1}"
        epoch = i
    elif mode == "circle":
        xy = np.array([.25+.4*math.cos(.2*t), .4*math.sin(.2*t)])
        label, epoch = "Circle", 0
    elif mode == "figure-eight":
        xy = np.array([.25+.4*math.cos(.18*t), .28*math.sin(.36*t)])
        label, epoch = "Figure eight", 0
    else:
        raise ValueError("manual targets must come from user input")
    c, s = math.cos(rotation), math.sin(rotation)
    return np.array([[c, -s], [s, c]])@xy, visible, label, epoch


def domain_draw(seed, randomized=True):
    rng = np.random.default_rng(seed)
    return {
        "seed": int(seed), "randomized": randomized,
        "friction_ratio": float(rng.uniform(.6, 1.4)) if randomized else 1.,
        "trunk_mass_ratio": float(rng.uniform(.9, 1.1)) if randomized else 1.,
        "motor_kp_ratio": float(rng.uniform(.9, 1.1)) if randomized else 1.,
        "trunk_com_shift_m": rng.uniform(-.005, .005, 3).tolist() if randomized else [0., 0., 0.],
        "sensor_delay_steps": int(rng.integers(0, 3)) if randomized else 0,
        "encoder_bias_rad": rng.uniform(-.012, .012, 14).tolist() if randomized else [0.]*14,
        "sensor_noise": bool(randomized),
        "push_at_s": 23.,
        "push_delta_v_m_s": rng.uniform(-.10, .10, 2).tolist() if randomized else [0., 0.],
        "route_rotation_rad": float(rng.uniform(-math.pi, math.pi)) if randomized else 0.,
        "visual_palette": int(rng.integers(0, 3)),
        "ground": "flat; no obstacles",
    }
