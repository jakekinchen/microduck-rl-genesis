"""V16 diagnostic: slew commanded motion, never servo actions or physics."""
import numpy as np
from experiments.walking.standing_world import StandingSwitchWalkingWorld


class CommandRamp:
    def __init__(self):
        self.value = np.zeros(3, np.float64)
        self.rate_per_s = np.array([.75, .75, 2.5], np.float64)

    def step(self, command):
        target = np.asarray(command, np.float32)
        if target.shape != (3,) or not np.isfinite(target).all():
            raise ValueError("finite three-axis requested command required")
        target = target.astype(np.float64)
        delta = target-self.value
        limit = self.rate_per_s*.02
        self.value = np.where(np.abs(delta) <= limit, target, self.value+np.sign(delta)*limit)
        return self.value.astype(np.float32)


class RampedStandingSwitchWorld(StandingSwitchWalkingWorld):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_ramp = CommandRamp()

    def step_command(self, command, action_override=None):
        routed = self.command_ramp.step(command)
        row = super().step_command(routed, action_override)
        row["routing_command"] = row["command"]
        row["command"] = np.asarray(command, np.float32).tolist()
        row["command_ramp_rate_per_s"] = self.command_ramp.rate_per_s.tolist()
        row["controller_variant"] = "command-ramp-v16-diagnostic"
        return row
