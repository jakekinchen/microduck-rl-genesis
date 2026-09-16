"""Physical-face v4 steering; preserve canonical +X velocity semantics.

The mouth and head-camera SITE face +X at HOME. The legacy MuJoCo CAMERA
looks inward (-X) and is not a valid proxy for physical facing direction.
The discarded v3 opposite-axis implementation is retained in quarantine.
"""
import numpy as np
from .laser_task import STOP_RADIUS_M, MAX_FORWARD_M_S, MAX_YAW_RAD_S
from .laser_steering import approach_command


def face_first_command(relative_xy, visible=True):
    return approach_command(relative_xy, visible, 3.)
