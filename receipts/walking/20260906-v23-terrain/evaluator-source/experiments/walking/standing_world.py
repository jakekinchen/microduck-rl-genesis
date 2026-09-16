"""V14 command-only actor switch; selected actions are never blended/filtered."""
import numpy as np
from evaluator.core import OnnxPolicy
from experiments.walking.heading_servo_world import HeadingServoWalkingWorld


def standing_command(command):
    value = np.asarray(command, np.float32)
    if value.shape != (3,) or not np.isfinite(value).all():
        raise ValueError("finite three-axis user command required")
    return bool(np.all(value == 0))


class StandingSwitchWalkingWorld(HeadingServoWalkingWorld):
    def __init__(self, *args, standing_policy, **kwargs):
        super().__init__(*args, **kwargs)
        self.walking_policy = self.core.policy
        self.standing_policy = OnnxPolicy(standing_policy, self.core.config["inference"])

    def step_command(self, command, action_override=None):
        stand = standing_command(command)
        self.core.policy = self.standing_policy if stand else self.walking_policy
        row = super().step_command(command, action_override)
        row["actor_mode"] = "standing" if stand else "walking"
        row["controller_variant"] = "command-only-stand-switch-v14"
        return row
