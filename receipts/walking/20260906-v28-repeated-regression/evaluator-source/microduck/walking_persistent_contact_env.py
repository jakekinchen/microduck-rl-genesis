"""V13 persistent device delays on the verified complete-contact model."""
from .walking_collision_env import MicroduckCompleteContactWalkingEnv
from .walking_persistent_timing_env import MicroduckPersistentTimingWalkingEnv


class MicroduckPersistentCompleteWalkingEnv(MicroduckCompleteContactWalkingEnv, MicroduckPersistentTimingWalkingEnv):
    def __init__(self, num_envs, **kwargs):
        super().__init__(num_envs, **kwargs)
        self.cfg.update(task="Walking-Complete-Contacts-Persistent-Timing-v13", walking_version="v13",
                        inherited_behavior="v9 objective/actions/observations; v11 complete geometry; episode-persistent delay process")
