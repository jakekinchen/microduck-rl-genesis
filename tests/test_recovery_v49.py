import unittest
import numpy as np
from experiments.walking.recovery_v49 import KnotPolicy,command_at

class RecoveryTests(unittest.TestCase):
    def test_absolute_command_boundaries(self):
        session={'windows':[{'duration_s':18,'move_start_s':1,'stop_start_s':13,'command':[.1,0,0]}]*10}
        self.assertEqual(command_at(4249,session),([.1,0,0],4,649))
        self.assertEqual(command_at(4250,session),([0,0,0],4,650))
        self.assertEqual(command_at(4500,session),([0,0,0],5,0))
        self.assertEqual(command_at(4550,session),([.1,0,0],5,50))
        with self.assertRaises(ValueError):command_at(9000,session)

    def test_zero_and_completed_residual_preserve_raw_bytes(self):
        class Base:
            def infer(self,obs):return np.array([[-0.0]+[.25]*13],np.float32),0.
        base=Base();obs=np.zeros((1,61),np.float32)
        policy=KnotPolicy(base,np.zeros((5,14),np.float32))
        self.assertEqual(policy.infer(obs)[0].tobytes(),base.infer(obs)[0].tobytes())
        policy=KnotPolicy(base,np.ones((5,14),np.float32));policy.step=125
        self.assertEqual(policy.infer(obs)[0].tobytes(),base.infer(obs)[0].tobytes())
        policy.step=0
        self.assertEqual(float(policy.infer(obs)[0][0,1]),1.25)
        with self.assertRaises(ValueError):KnotPolicy(base,np.full((5,14),np.nan))
        with self.assertRaises(ValueError):KnotPolicy(base,np.full((5,14),1.6))

if __name__=='__main__':unittest.main()
