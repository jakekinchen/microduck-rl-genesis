import unittest
import torch
from microduck.braking_v53 import BrakeController,retention_loss
class RetentionTests(unittest.TestCase):
    def test_verified_zero_states_penalize_worst_joint(self):
        p=torch.zeros(384,14,requires_grad=True);target=torch.zeros_like(p)
        with torch.no_grad():p[128,3]=.03
        loss,(positive,mean,worst)=retention_loss(p,target)
        self.assertEqual(float(positive),0.)
        self.assertAlmostEqual(float(mean),1/(256*14),places=8)
        self.assertAlmostEqual(float(worst),1/256,places=8)
        loss.backward();self.assertGreater(float(p.grad[128,3]),0.)
        self.assertEqual(int(torch.count_nonzero(p.grad)),1)
    def test_router_retains_exact_original_lifetime(self):
        b=BrakeController(None);b.prepare([.1,0,0])
        for i in range(130):b.prepare([0,0,0]);self.assertEqual(b.active,i<125)
        b.prepare([.1,0,0]);b.prepare([0,0,0]);self.assertTrue(b.active)
        b.prepare([0,.1,0]);self.assertFalse(b.active)
if __name__=='__main__':unittest.main()
