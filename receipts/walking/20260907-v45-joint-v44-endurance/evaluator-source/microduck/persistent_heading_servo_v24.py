"""V24 preserves the commanded course across STOP; motor actions unchanged."""
from .filtered_heading_servo import FilteredHeadingServo


class PersistentHeadingServo(FilteredHeadingServo):
    def step(self, requested_twist, orientation_wxyz, dt=.02):
        previous_reference = self.reference
        command, control = super().step(requested_twist, orientation_wxyz, dt)
        if control["mode"] == "stopped" and previous_reference is not None:
            self.reference = previous_reference
            control.update(heading_error_rad=self.reference-self.measured,
                           measured_unwrapped_heading_rad=self.measured,
                           reference_heading_rad=self.reference)
        control["reference_preserved_through_stop"] = True
        return command, control
