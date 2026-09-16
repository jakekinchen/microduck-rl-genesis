import unittest
from microduck.walking_collision_env import MicroduckCompleteContactWalkingEnv
from microduck.walking_persistent_timing_env import MicroduckPersistentTimingWalkingEnv
from microduck.walking_persistent_contact_env import MicroduckPersistentCompleteWalkingEnv


class PersistentContactCompositionTests(unittest.TestCase):
    def test_only_delay_builder_changes_from_complete_contact(self):
        self.assertIs(MicroduckPersistentCompleteWalkingEnv._build_actuator,
                      MicroduckPersistentTimingWalkingEnv._build_actuator)
        for name in ('step', '_build_scene', '_compute_rewards', '_refresh_state', '_update_contacts',
                     '_compute_observations', 'reset_idx', '_check_termination', '_resample_twist',
                     '_apply_curricula', '_startup_randomization'):
            self.assertIs(getattr(MicroduckPersistentCompleteWalkingEnv, name),
                          getattr(MicroduckCompleteContactWalkingEnv, name))

    def test_mro_runs_both_declared_initializers(self):
        order = MicroduckPersistentCompleteWalkingEnv.mro()
        self.assertLess(order.index(MicroduckCompleteContactWalkingEnv), order.index(MicroduckPersistentTimingWalkingEnv))


if __name__ == '__main__':
    unittest.main()
