"""Standing-only PPO with deterministic frozen walking and flat retention."""
import copy
import torch
from torch.distributions import Normal
from rsl_rl.algorithms import PPO
from microduck.sequence_actor_v44 import SequenceActor


class RetainedStanderActor(SequenceActor):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.walking.requires_grad_(False)
        self.teacher=copy.deepcopy(self.standing).requires_grad_(False)

    def forward(self,obs,masks=None,hidden_state=None,stochastic_output=False):
        if masks is not None:raise ValueError('nonrecurrent V48 only')
        stand=(obs['policy'][...,48:51]==0).all(-1,keepdim=True)
        wm,sm=self.walking(obs),self.standing(obs)
        mean=torch.where(stand,sm,wm)
        if not stochastic_output:return mean
        self.standing.distribution.update(sm)
        # The walking branch is deterministic and excluded from the PPO actor
        # objective. Its storage-only unit Normal has no trainable parameters.
        std=torch.where(stand,self.standing.distribution.std,torch.ones_like(mean))
        self._standing_mask=stand
        self.distribution._distribution=Normal(mean,std)
        return torch.where(stand,self.distribution.sample(),wm)


    def get_output_log_prob(self,outputs):
        value=self.distribution.log_prob(outputs)
        return torch.where(self._standing_mask.squeeze(-1),value,torch.zeros_like(value))

    @property
    def output_std(self):
        return torch.where(self._standing_mask,self.distribution.std,torch.zeros_like(self.distribution.std))


class StandingRetentionPPO(PPO):
    """Scoped nonrecurrent PPO: original clipped objective plus two L2 anchors."""
    def update(self):
        if self.rnd or self.symmetry or self.is_multi_gpu or self.actor.is_recurrent or self.schedule!='fixed':
            raise ValueError('unsupported V48 PPO configuration')
        sums=dict(value=0.,surrogate=0.,online_retention=0.,rehearsal_retention=0.)
        count=0
        for batch in self.storage.mini_batch_generator(self.num_mini_batches,self.num_learning_epochs):
            if batch.masks is not None:raise ValueError('unexpected recurrent masks')
            self.actor(batch.observations,stochastic_output=True)
            log_prob=self.actor.get_output_log_prob(batch.actions)
            values=self.critic(batch.observations)
            active=(batch.observations['policy'][:,48:51]==0).all(-1)
            retain=active & batch.observations['flat_retention'].squeeze(-1).bool()
            ratio=torch.exp(log_prob-batch.old_actions_log_prob.squeeze(-1))
            advantage=batch.advantages.squeeze(-1)
            surrogate=torch.maximum(-advantage*ratio,-advantage*ratio.clamp(1-self.clip_param,1+self.clip_param))
            actor_loss=(surrogate*active).sum()/active.sum().clamp_min(1)
            if self.use_clipped_value_loss:
                clipped=batch.values+(values-batch.values).clamp(-self.clip_param,self.clip_param)
                value_loss=torch.maximum((values-batch.returns).square(),(clipped-batch.returns).square()).mean()
            else:value_loss=(values-batch.returns).square().mean()
            with torch.no_grad():target=self.actor.teacher(batch.observations)
            current=self.actor.standing(batch.observations)
            distance=((current-target)/.05).square().mean(-1)
            online_loss=(distance*retain).sum()/retain.sum().clamp_min(1)
            indices=torch.randint(len(self.replay_obs),(512,),device=self.device)
            from tensordict import TensorDict
            replay=TensorDict({'policy':self.replay_obs[indices]},[len(indices)])
            replay_loss=((self.actor.standing(replay)-self.replay_actions[indices])/.05).square().mean()
            loss=actor_loss+self.value_loss_coef*value_loss+online_loss+.2*replay_loss
            self.optimizer.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(),self.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(),self.max_grad_norm)
            self.optimizer.step()
            for name,value in [('value',value_loss),('surrogate',actor_loss),('online_retention',online_loss),('rehearsal_retention',replay_loss)]:
                sums[name]+=value.item()
            count+=1
        self.storage.clear()
        return {name:value/count for name,value in sums.items()}
