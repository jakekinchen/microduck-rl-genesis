"""Bounded Genesis recreation of the upstream standing-backflip task.

Only the base flat-ground task is carried here.  Pedestal specialists,
reference-state distillation, evaluators, and receipt infrastructure remain in
the source repository and are intentionally outside this Mac pipeline slice.
"""

from __future__ import annotations

import copy
import math

from .velocity_cfg import TRAIN_CFG as VELOCITY_TRAIN_CFG

NUM_STEPS_PER_ENV = 24
EPISODE_LENGTH_S = 4.0
STAND_Z = 0.115
MIN_TAKEOFF_Z = 0.135
STABLE_HOLD_S = 0.5

ASSIST_START_S = 0.30
ASSIST_END_S = 0.40
ASSIST_UPWARD_FORCE_N = 16.0
ASSIST_BACKWARD_TORQUE_NM = 1.40
ASSIST_MIN_ACTION_AUTHORITY = 0.05

SPAWN_STAGES = [
    (0, (0.45, 0.10, 0.25, 0.20)),
    (200 * NUM_STEPS_PER_ENV, (0.60, 0.10, 0.20, 0.10)),
    (400 * NUM_STEPS_PER_ENV, (0.75, 0.10, 0.10, 0.05)),
]

TUCK_OVERRIDES = {
    2: -1.15,
    3: 1.25,
    4: 1.05,
    5: -0.55,
    6: 0.55,
    11: 1.15,
    12: -1.25,
    13: -1.05,
}
CROUCH_OVERRIDES = {
    2: -1.15,
    3: 1.25,
    4: 1.05,
    11: 1.15,
    12: -1.25,
    13: -1.05,
}
LEG_JOINT_IDS = (0, 1, 2, 3, 4, 9, 10, 11, 12, 13)

# These are the base-task weights from microduck-backflip.  Positive reward
# functions are positive; costs are positive with negative weights.
REWARD_WEIGHTS = {
    "backflip_takeoff": 60.0,
    "backflip_launch_velocity": 40.0,
    "backflip_preload": 30.0,
    "backflip_launch_quality": 40.0,
    "backflip_supported_push": 60.0,
    "backflip_feasible_push": 120.0,
    "backflip_rotation": 80.0,
    "backflip_flight_tuck": 8.0,
    "backflip_prepare_landing": 20.0,
    "backflip_landing_approach": 50.0,
    "backflip_landing": 100.0,
    "backflip_landing_upright": 100.0,
    "backflip_landing_height": 75.0,
    "backflip_landing_stillness": 75.0,
    "backflip_landing_foot_support": 50.0,
    "backflip_stability_progress": 200.0,
    "backflip_success": 200.0,
    "backflip_body_contact": -2.0,
    "backflip_assisted_action": -2.0,
    "backflip_late_pitch_rate": -10.0,
    "backflip_wrong_direction": -0.02,
    "backflip_flatness": -0.02,
    "backflip_lateral_velocity": -0.05,
    "body_ang_vel": -0.001,
    "dof_pos_limits": -1.0,
}


def stage_value(stages, step):
    value = stages[0][1]
    for threshold, candidate in stages:
        if step >= threshold:
            value = candidate
    return value


TRAIN_CFG = copy.deepcopy(VELOCITY_TRAIN_CFG)
TRAIN_CFG["algorithm"]["symmetry_cfg"] = None
