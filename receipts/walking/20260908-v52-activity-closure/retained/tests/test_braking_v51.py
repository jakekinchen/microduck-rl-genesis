import unittest
import numpy as np
from experiments.walking.recovery_v51 import TransientStander
from scripts.probe_recovery_v51 import eligible

class BrakingEligibilityTests(unittest.TestCase):
    def test_transient_base_returns_to_original_at_exact_control(self):
        class Actor:
            def __init__(self,value):self.value=np.full((1,14),value,np.float32)
            def infer(self,obs):return self.value.copy(),0.
        early,steady=Actor(2),Actor(1);policy=TransientStander(early,steady)
        for step,expected in [(0,early),(124,early),(125,steady),(900,steady)]:
            policy.step=step
            self.assertEqual(policy.infer(np.zeros((1,61),np.float32))[0].tobytes(),expected.value.tobytes())
    def test_demonstration_does_not_waive_failed_safety_or_missing_duration(self):
        def report(failures,controls=900):return {'case_reports':[{'failures':failures,'observed_controls':controls}]}
        yaw=['mean_abs_yaw_error_rad_s','endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s']
        self.assertTrue(eligible(report(yaw)))
        for failure in ['fall','nonfoot_support','self_load:continuous_body_bracing','persistent_loaded_foot_slip','mean_abs_forward_error_m_s']:
            self.assertFalse(eligible(report(yaw+[failure])))
        self.assertFalse(eligible(report([],899)))
if __name__=='__main__':unittest.main()
