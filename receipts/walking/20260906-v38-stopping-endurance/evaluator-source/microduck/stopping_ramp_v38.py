"""V38 slow translational STOP command deceleration; direct motor actions stay."""
import numpy as np
from experiments.walking.command_ramp import CommandRamp


class StoppingRamp(CommandRamp):
    def step(self, command):
        target=np.asarray(command,np.float32)
        if target.shape!=(3,) or not np.isfinite(target).all():
            raise ValueError('finite three-axis requested command required')
        target=target.astype(np.float64)
        rates=self.rate_per_s.copy()
        # STOP is the exact zero user command. Acceleration, moving commands
        # and angular deceleration retain the baseline arithmetic and limits.
        if np.all(target==0):rates[:2]=.25
        delta=target-self.value
        limit=rates*.02
        self.value=np.where(np.abs(delta)<=limit,target,self.value+np.sign(delta)*limit)
        return self.value.astype(np.float32)
