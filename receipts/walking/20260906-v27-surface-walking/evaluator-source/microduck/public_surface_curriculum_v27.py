"""V27 changes only episode surface sampling; preserve V25 physics and rewards."""
import torch
from .public_surface_env_v25 import PublicSurfaceWalkingEnv


def probabilities(control_step):
    if control_step < 2000:return (.8,.2,0.,0.)
    if control_step < 4000:return (.6,.3,.1,0.)
    return (.5,.3,.2,0.)


class ConservativeSurfaceWalkingEnv(PublicSurfaceWalkingEnv):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.cfg.update(task='Public-Surface-Curriculum-v27',walking_version='v27',
            curriculum='0..1999: .8/.2/0/0; 2000..3999: .6/.3/.1/0; >=4000: .5/.3/.2/0',
            training_surface_ids=[0,1,2],stress_only_surface_ids=[3],
            boundary='Training-distribution intervention only; all original proxy challenge cases remain required and unrelabelled.')

    def _terrain_curriculum(self,env_ids):
        u=torch.rand(len(env_ids),device=self.device)
        p=probabilities(self.common_step_counter)
        buckets=(u>=p[0]).long()+(u>=p[0]+p[1]).long()
        self.env_origins[env_ids,0]=0.
        self.env_origins[env_ids,1]=buckets.to(self.env_origins.dtype)*16
        self.env_origins[env_ids,2]=0.
        self.surface_resets+=torch.bincount(buckets,minlength=4)
