"""New opt-in V54-style PPO with diagnostics and explicit retention ablations.

The frozen V54/V55 implementation is not changed. No candidate is promoted here.
"""
import json
from pathlib import Path
import numpy as np
import torch
from tensordict import TensorDict
from microduck.recipe_actor_v54 import RecipePPO, balanced_indices
from retool.learning import actor_gradient_diagnostics, balanced_replay_indices, PHASES


class ReviewPPO(RecipePPO):
    def __init__(self, *args, diagnostics_path, diagnostics_every=25,
                 online_retention_coef=1., replay_retention_coef=1.,
                 replay_sampling="mode", replay_seed=260916,
                 replay_phases=PHASES, **kwargs):
        if type(diagnostics_every) is not int or diagnostics_every <= 0:
            raise ValueError("positive diagnostic cadence required")
        if replay_sampling not in ("mode", "transition"):
            raise ValueError("unknown replay sampler")
        if not np.isfinite([online_retention_coef, replay_retention_coef]).all() or min(online_retention_coef, replay_retention_coef) < 0:
            raise ValueError("nonnegative finite retention weights required")
        super().__init__(*args, **kwargs)
        self.diag_path = Path(diagnostics_path)
        # A newly allocated run directory must already exist; never overwrite evidence.
        with self.diag_path.open("x"):
            pass
        self.diag_every, self.update_index = diagnostics_every, 0
        self.online_coef, self.replay_coef = online_retention_coef, replay_retention_coef
        self.replay_sampling, self.replay_phases = replay_sampling, tuple(replay_phases)
        self.replay_rng = np.random.default_rng(replay_seed)

    def update(self):
        if (self.rnd or self.symmetry or self.is_multi_gpu or self.actor.is_recurrent
                or self.schedule != "fixed" or self.entropy_coef != 0):
            raise ValueError("review lane supports fixed, nonrecurrent, zero-entropy PPO only")
        sums = dict(value=0., surrogate=0., online_retention=0., rehearsal_retention=0.,
                    approx_kl=0., clip_fraction=0.)
        count = 0
        for batch in self.storage.mini_batch_generator(self.num_mini_batches, self.num_learning_epochs):
            if batch.masks is not None:
                raise ValueError("unexpected recurrent masks")
            self.actor(batch.observations, stochastic_output=True)
            log_prob = self.actor.get_output_log_prob(batch.actions)
            values = self.critic(batch.observations)
            log_ratio = log_prob - batch.old_actions_log_prob.squeeze(-1)
            ratio = torch.exp(log_ratio)
            advantage = batch.advantages.squeeze(-1)
            per_row = torch.maximum(-advantage * ratio,
                                    -advantage * ratio.clamp(1-self.clip_param, 1+self.clip_param))
            surrogate = per_row.mean()
            if self.use_clipped_value_loss:
                clipped = batch.values + (values-batch.values).clamp(-self.clip_param, self.clip_param)
                value_loss = torch.maximum((values-batch.returns).square(),
                                          (clipped-batch.returns).square()).mean()
            else:
                value_loss = (values-batch.returns).square().mean()
            with torch.no_grad():
                target = self.teacher(batch.observations)
            current = self.actor(batch.observations)
            distance = ((current-target)/.03).square().mean(-1)
            retain = batch.observations["flat_retention"].squeeze(-1).bool()
            online_loss = (distance*retain).sum()/retain.sum().clamp_min(1)
            if self.replay_sampling == "transition":
                if not hasattr(self, "replay_labels") or len(self.replay_labels) != len(self.replay_obs):
                    raise ValueError("source-bound row-aligned replay_labels required")
                chosen = balanced_replay_indices(self.replay_labels, self.replay_rng,
                                                phases=self.replay_phases, total_count=512)
                indices = torch.as_tensor(chosen, device=self.replay_obs.device)
            else:
                indices = balanced_indices(self.replay_pools)
            replay = TensorDict({"policy": self.replay_obs[indices]}, [len(indices)])
            replay_loss = ((self.actor(replay)-self.replay_actions[indices])/.03).square().mean()
            terms = dict(surrogate=surrogate, online_retention=self.online_coef*online_loss,
                         rehearsal_retention=self.replay_coef*replay_loss)
            loss = (surrogate + self.value_loss_coef*value_loss
                    + self.online_coef*online_loss + self.replay_coef*replay_loss)
            if not torch.isfinite(loss):
                raise ValueError("nonfinite review loss")
            approx_kl = ((ratio-1)-log_ratio).detach().mean()
            clip_fraction = ((ratio-1).abs() > self.clip_param).float().detach().mean()
            if count == 0 and self.update_index % self.diag_every == 0:
                diagnostics = actor_gradient_diagnostics(terms, self.actor.parameters())
                moving = (batch.observations["policy"][:, 48:51] != 0).any(-1)
                groups = {}
                for label, mask in (("flat_walk", retain & moving), ("flat_stand", retain & ~moving),
                                    ("nonflat_walk", ~retain & moving), ("nonflat_stand", ~retain & ~moving)):
                    n = int(mask.sum())
                    groups[label] = dict(rows=n, advantage_mean=float(advantage[mask].mean()) if n else None,
                                         value_mse=float((values[mask]-batch.returns[mask]).square().mean().detach()) if n else None)
                    if n:
                        groups[label]["actor_gradient"] = actor_gradient_diagnostics(
                            {"surrogate": per_row[mask].mean()}, self.actor.parameters())
                variance = torch.var(batch.returns.detach(), unbiased=False)
                explained = (1-torch.var(batch.returns.detach()-values.detach(), unbiased=False)/variance) if variance > 0 else None
                record = dict(update=self.update_index, batch=count, groups=groups,
                              approx_kl=float(approx_kl), clip_fraction=float(clip_fraction),
                              explained_variance=float(explained) if explained is not None else None,
                              replay_sampling=self.replay_sampling, **diagnostics)
                with self.diag_path.open("a") as stream:
                    stream.write(json.dumps(record, allow_nan=False)+"\n")
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(), self.max_grad_norm)
            self.optimizer.step()
            for name, value in (("value", value_loss), ("surrogate", surrogate),
                                ("online_retention", online_loss), ("rehearsal_retention", replay_loss),
                                ("approx_kl", approx_kl), ("clip_fraction", clip_fraction)):
                sums[name] += value.item()
            count += 1
        if not count:
            raise ValueError("empty PPO update")
        self.storage.clear()
        self.update_index += 1
        return {name: value/count for name, value in sums.items()}
