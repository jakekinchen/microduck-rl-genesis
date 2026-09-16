"""Conditional v10 timing-domain correction; not used by the v9 run.

Same uniform delay ranges and exact inherited FIFO. The only change is when
device delays are sampled: at episode reset, then constant within that episode.
"""
import torch
from .bam_actuator import DelayBuffer
from .walking_viability_env import MicroduckViableWalkingEnv


class EpisodeDelayBuffer(DelayBuffer):
    def __init__(self, shape, min_lag, max_lag, device):
        if type(min_lag) is not int or type(max_lag) is not int or not 0 <= min_lag <= max_lag <= 6:
            raise ValueError("integer delay envelope 0..6 required")
        super().__init__(shape, min_lag, max_lag, 0, device)

    def reset(self, env_ids):
        super().reset(env_ids)
        if len(env_ids):
            self._lag[env_ids] = torch.randint(self.min_lag, self.max_lag + 1,
                                              (len(env_ids),), device=self.device)


class MicroduckPersistentTimingWalkingEnv(MicroduckViableWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Episode-Persistent-Timing-v10", walking_version="v10",
                        timing_sampling="independent uniform device delays sampled at each episode reset; held for episode",
                        motor_delay_physics_steps=[0, 6], sensor_delay_control_steps=[0, 1])

    def _build_actuator(self):
        super()._build_actuator()
        self.bam._delay = EpisodeDelayBuffer((self.num_envs, 14), 0, 6, self.device)
        for name, dimension in (("base_ang_vel", 3), ("projected_gravity", 3), ("joint_vel", 14)):
            self.obs_delays[name] = EpisodeDelayBuffer((self.num_envs, dimension), 0, 1, self.device)
