"""V19 reuses the exact V18 paired world except its upstream heading correction."""
from experiments.walking.command_ramp import RampedStandingSwitchWorld
from microduck.filtered_heading_servo import FilteredHeadingServo


class FilteredHeadingWalkingWorld(RampedStandingSwitchWorld):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heading_servo = FilteredHeadingServo()

    def step_command(self, command, action_override=None):
        row = super().step_command(command, action_override)
        row["controller_variant"] = "filtered-heading-command-v19"
        return row
