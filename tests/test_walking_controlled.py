"""Controlled-walking reward regressions; fixtures are not physical proof."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import torch
from microduck.walking_controlled_env import landing_quality,effort_cost,TorqueRecorder


class ControlledWalkingTests(unittest.TestCase):
    def test_quick_tapping_cannot_out_earn_controlled_step_rate(self):
        air=torch.tensor([.06,.10,.16,.30])
        quality=landing_quality(air)
        self.assertAlmostEqual(float(quality[2]),1.)
        self.assertGreater(float(quality[2]/air[2]),float(quality[0]/air[0]))
        self.assertGreater(float(quality[2]/air[2]),float(quality[1]/air[1]))
        self.assertLess(float(quality[3]),.01)

    def test_effort_cost_prices_each_motor_and_every_substep(self):
        torque=torch.zeros(4,2,14)
        torque[0,0,0]=1.
        torque[3,1,1]=-1.
        torch.testing.assert_close(effort_cost(torque,1.),torch.full((2,),.25))
        torch.testing.assert_close(effort_cost(torch.full_like(torque,.7),1.),torch.zeros(2))

    def test_torque_recorder_does_not_change_return_tensor(self):
        actual=torch.tensor([[.4,-.6]])
        target=torch.tensor([[1.,2.]])
        def compute(value):
            self.assertIs(value,target)
            return actual
        recorder=TorqueRecorder(compute)
        self.assertIs(recorder(target),actual)
        self.assertEqual(recorder.samples[0].numpy().tobytes(),actual.numpy().tobytes())
        actual.zero_()
        self.assertEqual(recorder.samples[0].tolist(),[[.4000000059604645,-.6000000238418579]])


if __name__=="__main__":unittest.main(verbosity=2)
