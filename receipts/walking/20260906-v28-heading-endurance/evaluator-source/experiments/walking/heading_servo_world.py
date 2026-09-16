"""V12 explicitly adds IMU heading feedback before the frozen locomotion actor."""
from collections import deque
import numpy as np
from microduck.heading_servo import HeadingServo
from experiments.walking.collision_world import CompleteContactWalkingWorld


class HeadingServoWalkingWorld(CompleteContactWalkingWorld):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.heading_servo = HeadingServo()
        self.heading_sensor_history = deque(maxlen=2)

    def step_command(self, command, action_override=None):
        if action_override is not None:
            raise ValueError("command-servo evaluation is closed loop, not fixed-action replay")
        sensor = self._sample_current_sensors()
        self.heading_sensor_history.append(sensor.sensor("orientation").data.copy())
        orientation = self.heading_sensor_history[max(0, len(self.heading_sensor_history)-1-self.sensor_ticks)]
        policy_command, control = self.heading_servo.step(command, orientation)
        row = super().step_command(policy_command)
        row["policy_command"] = row["command"]
        row["command"] = np.asarray(command, np.float32).tolist()
        row["heading_control"] = control
        row["heading_source"] = "copied-current IMU orientation with declared sensor FIFO"
        row["controller_variant"] = "imu-heading-command-servo-v12"
        return row
