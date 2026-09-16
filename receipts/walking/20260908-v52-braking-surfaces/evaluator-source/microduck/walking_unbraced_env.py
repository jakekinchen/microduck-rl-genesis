"""V18: apply the verified V15 internal-load objective to V13 walking."""
import torch
from .walking_persistent_contact_env import MicroduckPersistentCompleteWalkingEnv
from .walking_viability_env import positive_walking_return, posture_viability
from .standing_env import summed_internal_force, standing_load_delta


class MicroduckUnbracedWalkingEnv(MicroduckPersistentCompleteWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Unbraced-v18", walking_version="v18",
                        inherited_behavior="V13 commands/resets/physics/actions; additive V15 internal-load objective on ALL commands",
                        self_load_measurement="valid internal force_a magnitudes after last 5-ms substep; 50-Hz reward, not native normal-force equivalence",
                        self_load_free_n=.5, self_load_gate_scale_n=.5, self_load_cost_per_n=-2.)

    def _build_buffers(self):
        super()._build_buffers()
        self.walking_internal_n = torch.zeros(self.num_envs, device=self.device)
        for name in ("walking_internal_n", "walking_load_cost"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _update_contacts(self):
        super()._update_contacts()
        self.walking_internal_n = summed_internal_force(self.robot.get_contacts(with_entity=self.robot))

    def _compute_rewards(self):
        super()._compute_rewards()
        positive = positive_walking_return(self)
        posture = posture_viability(self.walking_head_absolute_ema, self.projected_gravity)
        delta = standing_load_delta(positive, posture, self.walking_internal_n, self.dt)
        self.rew_buf += delta
        self.episode_sums["walking_load_cost"] += delta
        self.episode_sums["walking_internal_n"] += self.walking_internal_n*self.dt

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        self.walking_internal_n[env_ids] = 0.
