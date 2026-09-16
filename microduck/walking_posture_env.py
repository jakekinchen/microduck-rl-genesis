"""Walking v3: retain controlled steps, price every head-command error."""
import torch
from .walking_controlled_env import MicroduckControlledWalkingEnv


def head_command_cost(error):
    # Linear beyond a small deadband: one badly displaced joint cannot hide in
    # an average of three correct joints or in a saturated Gaussian tail.
    return (error.abs()-.20).clamp_min(0).sum(-1)


class MicroduckPostureWalkingEnv(MicroduckControlledWalkingEnv):
    def __init__(self,num_envs,**kwargs):
        super().__init__(num_envs,**kwargs)
        self.cfg.update(task="Walking-Controlled-Posture-v3",walking_version="v3",
            head_command_cost_weight=-6.,head_command_deadband_rad=.20,
            domain="nominal rigid model; timing plus inherited BAM battery/drop variation")

    def _build_buffers(self):
        super()._build_buffers()
        self.episode_sums["head_command_cost"]=torch.zeros(self.num_envs,device=self.device)
        self.episode_sums["worst_head_command_error_rad"]=torch.zeros(self.num_envs,device=self.device)

    def _compute_rewards(self):
        super()._compute_rewards()
        error=self._head_pose_error()
        value=-6*head_command_cost(error)*self.dt
        self.rew_buf+=value
        self.episode_sums["head_command_cost"]+=value
        self.episode_sums["worst_head_command_error_rad"]+=error.abs().amax(-1)*self.dt
