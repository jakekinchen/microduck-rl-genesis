"""Comparable routed/shared actors with frozen coordinates and rehearsal PPO."""
import torch
from rsl_rl.models import MLPModel
from rsl_rl.algorithms import PPO
from tensordict import TensorDict
from microduck.sequence_actor_v44 import SequenceActor


class SharedActor(MLPModel):
    def update_normalization(self, obs):
        # The initialization and deployment use the original walking coordinates.
        pass


RoutedActor = SequenceActor


def mode_pools(observations):
    standing = (observations[:,48:51] == 0).all(-1)
    pools = tuple(torch.nonzero(select).flatten() for select in (~standing, standing))
    if not all(len(pool) for pool in pools):
        raise ValueError('both replay modes are required')
    return pools


def balanced_indices(pools, count=256):
    return torch.cat([pool[torch.randint(len(pool), (count,), device=pool.device)] for pool in pools])


class RecipePPO(PPO):
    """Original clipped nonrecurrent PPO plus identical two-mode retention losses."""
    def update(self):
        if (self.rnd or self.symmetry or self.is_multi_gpu or self.actor.is_recurrent
                or self.schedule != 'fixed'):
            raise ValueError('unsupported V54 PPO configuration')
        sums = dict(value=0., surrogate=0., online_retention=0., rehearsal_retention=0.)
        count = 0
        for batch in self.storage.mini_batch_generator(self.num_mini_batches,self.num_learning_epochs):
            if batch.masks is not None:
                raise ValueError('unexpected recurrent masks')
            self.actor(batch.observations, stochastic_output=True)
            log_prob = self.actor.get_output_log_prob(batch.actions)
            values = self.critic(batch.observations)
            ratio = torch.exp(log_prob-batch.old_actions_log_prob.squeeze(-1))
            advantage = batch.advantages.squeeze(-1)
            surrogate = torch.maximum(-advantage*ratio,
                -advantage*ratio.clamp(1-self.clip_param,1+self.clip_param)).mean()
            if self.use_clipped_value_loss:
                clipped = batch.values+(values-batch.values).clamp(-self.clip_param,self.clip_param)
                value_loss = torch.maximum((values-batch.returns).square(),
                    (clipped-batch.returns).square()).mean()
            else:
                value_loss = (values-batch.returns).square().mean()
            with torch.no_grad():
                target = self.teacher(batch.observations)
            current = self.actor(batch.observations)
            distance = ((current-target)/.03).square().mean(-1)
            retain = batch.observations['flat_retention'].squeeze(-1).bool()
            online_loss = (distance*retain).sum()/retain.sum().clamp_min(1)
            indices = balanced_indices(self.replay_pools)
            replay = TensorDict({'policy':self.replay_obs[indices]}, [len(indices)])
            replay_loss = ((self.actor(replay)-self.replay_actions[indices])/.03).square().mean()
            loss = surrogate+self.value_loss_coef*value_loss+online_loss+replay_loss
            if not torch.isfinite(loss):
                raise ValueError('nonfinite V54 learning loss')
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(),self.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(),self.max_grad_norm)
            self.optimizer.step()
            for name,value in [('value',value_loss),('surrogate',surrogate),
                    ('online_retention',online_loss),('rehearsal_retention',replay_loss)]:
                sums[name] += value.item()
            count += 1
        self.storage.clear()
        return {name:value/count for name,value in sums.items()}
