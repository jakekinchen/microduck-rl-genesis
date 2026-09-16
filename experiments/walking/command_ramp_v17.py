"""V17 diagnostic: one-second full-yaw rise, unchanged translational ramp."""
from experiments.walking.command_ramp import RampedStandingSwitchWorld


class GentleYawStandingSwitchWorld(RampedStandingSwitchWorld):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_ramp.rate_per_s[2] = .75

    def step_command(self, command, action_override=None):
        row = super().step_command(command, action_override)
        row["controller_variant"] = "command-ramp-v17-diagnostic"
        return row
