"""V15 standing specialization: same complete model/timing, zero commands only."""
import torch
from .walking_persistent_contact_env import MicroduckPersistentCompleteWalkingEnv
from .walking_viability_env import positive_walking_return, posture_viability


def summed_internal_force(contacts):
    force = torch.linalg.vector_norm(contacts["force_a"], dim=-1)
    mask = contacts["valid_mask"]
    if force.shape != mask.shape or force.ndim != 2:
        raise ValueError("batched internal contact forces and mask required")
    return torch.where(mask, force, torch.zeros_like(force)).sum(-1)


def standing_load_delta(positive, posture_gate, force_n, dt):
    excess = (force_n-.5).clamp_min(0.)
    viable = torch.exp(-(excess/.5).square())
    # Parent R = posture_gate*positive + negative. Gate ONLY that surviving
    # positive part, never erase or scale inherited effort/posture penalties.
    return -(1-viable)*posture_gate*positive - 2.*excess*dt


class MicroduckStandingEnv(MicroduckPersistentCompleteWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Standing-Unbraced-v15", walking_version="standing-v15",
                        command_domain="exactly zero velocity/head/body commands",
                        self_load_measurement="sum of valid internal force_a vector magnitudes after last 5-ms substep, 50-Hz reward; not native normal-force equivalence",
                        self_load_free_n=.5, self_load_gate_scale_n=.5, self_load_cost_per_n=-2.,
                        inherited_behavior="v13 complete physics/persistent delays and v9 posture objective; standing specialization only")

    def _build_buffers(self):
        super()._build_buffers()
        self.standing_internal_n = torch.zeros(self.num_envs, device=self.device)
        for name in ("standing_internal_n", "standing_load_cost"):
            self.episode_sums[name] = torch.zeros(self.num_envs, device=self.device)

    def _resample_twist(self, env_ids):
        self.twist_cmd[env_ids] = 0.
        self.is_standing_env[env_ids] = True
        self.twist_resample_at[env_ids] = self.episode_length_buf[env_ids]+250

    def _update_contacts(self):
        super()._update_contacts()
        self.standing_internal_n = summed_internal_force(self.robot.get_contacts(with_entity=self.robot))

    def _compute_rewards(self):
        super()._compute_rewards()
        positive = positive_walking_return(self)
        gate = posture_viability(self.walking_head_absolute_ema, self.projected_gravity)
        delta = standing_load_delta(positive, gate, self.standing_internal_n, self.dt)
        self.rew_buf += delta
        self.episode_sums["standing_load_cost"] += delta
        self.episode_sums["standing_internal_n"] += self.standing_internal_n*self.dt

    def reset_idx(self, env_ids):
        super().reset_idx(env_ids)
        self.standing_internal_n[env_ids] = 0.
