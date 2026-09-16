"""Walker-only PPO with deterministic frozen standing and teacher retention."""
import copy
import torch
from torch.distributions import Normal
from rsl_rl.algorithms import PPO
from microduck.sequence_actor_v44 import SequenceActor


class RetainedWalkerActor(SequenceActor):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.standing.requires_grad_(False)
        self.teacher=copy.deepcopy(self.walking).requires_grad_(False)

    def forward(self,obs,masks=None,hidden_state=None,stochastic_output=False):
        if masks is not None:raise ValueError('nonrecurrent V50 only')
        stand=(obs['policy'][...,48:51]==0).all(-1,keepdim=True)
        wm,sm=self.walking(obs),self.standing(obs)
        mean=torch.where(stand,sm,wm)
        if not stochastic_output:return mean
        self.walking.distribution.update(wm)
        # The standing branch is deterministic and excluded from the PPO actor
        # objective. Its storage-only unit Normal has no trainable parameters.
        std=torch.where(stand,torch.ones_like(mean),self.walking.distribution.std)
        self._standing_mask=stand
        self.distribution._distribution=Normal(mean,std)
        return torch.where(stand,sm,self.distribution.sample())


    def get_output_log_prob(self,outputs):
        value=self.distribution.log_prob(outputs)
        return torch.where(self._standing_mask.squeeze(-1),torch.zeros_like(value),value)

    @property
    def output_std(self):
        return torch.where(self._standing_mask,torch.zeros_like(self.distribution.std),self.distribution.std)


class RetentionPPO(PPO):
    """Scoped nonrecurrent PPO: original clipped objective plus two L2 anchors."""
    def update(self):
        if self.rnd or self.symmetry or self.is_multi_gpu or self.actor.is_recurrent or self.schedule!='fixed':
            raise ValueError('unsupported V50 PPO configuration')
        sums=dict(value=0.,surrogate=0.,online_retention=0.,rehearsal_retention=0.)
        count=0
        for batch in self.storage.mini_batch_generator(self.num_mini_batches,self.num_learning_epochs):
            if batch.masks is not None:raise ValueError('unexpected recurrent masks')
            self.actor(batch.observations,stochastic_output=True)
            log_prob=self.actor.get_output_log_prob(batch.actions)
            values=self.critic(batch.observations)
            moving=(batch.observations['policy'][:,48:51]!=0).any(-1)
            ratio=torch.exp(log_prob-batch.old_actions_log_prob.squeeze(-1))
            advantage=batch.advantages.squeeze(-1)
            surrogate=torch.maximum(-advantage*ratio,-advantage*ratio.clamp(1-self.clip_param,1+self.clip_param))
            actor_loss=(surrogate*moving).sum()/moving.sum().clamp_min(1)
            if self.use_clipped_value_loss:
                clipped=batch.values+(values-batch.values).clamp(-self.clip_param,self.clip_param)
                value_loss=torch.maximum((values-batch.returns).square(),(clipped-batch.returns).square()).mean()
            else:value_loss=(values-batch.returns).square().mean()
            with torch.no_grad():target=self.actor.teacher(batch.observations)
            current=self.actor.walking(batch.observations)
            distance=((current-target)/.03).square().mean(-1)
            retain=moving & batch.observations['flat_retention'].squeeze(-1).bool()
            online_loss=(distance*retain).sum()/retain.sum().clamp_min(1)
            indices=torch.randint(len(self.replay_obs),(512,),device=self.device)
            from tensordict import TensorDict
            replay=TensorDict({'policy':self.replay_obs[indices]},[len(indices)])
            replay_loss=((self.actor.walking(replay)-self.replay_actions[indices])/.03).square().mean()
            loss=actor_loss+self.value_loss_coef*value_loss+online_loss+replay_loss
            self.optimizer.zero_grad();loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(),self.max_grad_norm)
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(),self.max_grad_norm)
            self.optimizer.step()
            for name,value in [('value',value_loss),('surrogate',actor_loss),('online_retention',online_loss),('rehearsal_retention',replay_loss)]:
                sums[name]+=value.item()
            count+=1
        self.storage.clear()
        return {name:value/count for name,value in sums.items()}
