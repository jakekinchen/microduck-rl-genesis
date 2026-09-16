import math
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from microduck.heading_servo import HeadingServo
from microduck.filtered_heading_servo import FilteredHeadingServo


def q(yaw):
    return [math.cos(yaw/2),0,0,math.sin(yaw/2)]


class FilteredHeadingTests(unittest.TestCase):
    def test_forward_lateral_and_initial_feedforward_unchanged(self):
        cmd,_=FilteredHeadingServo().step([.12,.02,.4],q(0))
        np.testing.assert_array_equal(cmd,np.array([.12,.02,.4],np.float32))

    def test_zero_stop_and_reset_remove_residual_correction(self):
        s=FilteredHeadingServo();s.step([.12,0,0],q(0))
        for _ in range(20):s.step([.12,0,0],q(.1))
        self.assertLess(s.filtered_correction,0)
        cmd,c=s.step([0,0,0],q(.1))
        np.testing.assert_array_equal(cmd,np.zeros(3,np.float32))
        self.assertEqual(c["filtered_correction_rad_s"],0)
        s.reset();self.assertIsNone(s.previous_wrapped)
        self.assertEqual(s.filtered_correction,0)

    def test_dc_heading_correction_is_preserved_after_settling(self):
        s=FilteredHeadingServo();s.step([.12,0,0],q(0))
        for _ in range(150):cmd,c=s.step([.12,0,0],q(.05))
        self.assertAlmostEqual(float(cmd[2]),-.1,places=6)

    def test_six_hz_correction_is_attenuated(self):
        a,b=HeadingServo(),FilteredHeadingServo();raw=[];filtered=[]
        for i in range(500):
            quat=q(.03*math.sin(2*math.pi*6*i*.02))
            raw.append(a.step([.12,0,0],quat)[0][2])
            filtered.append(b.step([.12,0,0],quat)[0][2])
        self.assertLess(np.std(filtered[250:])/np.std(raw[250:]),.25)

    def test_original_correction_and_command_caps_remain(self):
        s=FilteredHeadingServo();s.step([.12,0,.75],q(0))
        for i in range(400):
            cmd,c=s.step([.12,0,.75],q(-.01*i))
            self.assertLessEqual(abs(float(cmd[2])),.75)
            self.assertLessEqual(abs(c["filtered_correction_rad_s"]),.25+1e-8)

    def test_invalid_sensor_or_command_does_not_mutate_filter(self):
        s=FilteredHeadingServo()
        for cmd,quat,dt in [([0,0,1],q(0),.02),([0,0,0],[2,0,0,0],.02),([0,0,0],q(0),.01)]:
            with self.assertRaises(ValueError):s.step(cmd,quat,dt)
            self.assertEqual(s.filtered_correction,0)


if __name__=="__main__":unittest.main()
