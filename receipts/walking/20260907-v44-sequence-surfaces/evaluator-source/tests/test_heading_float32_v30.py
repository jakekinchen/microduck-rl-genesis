import unittest
import numpy as np
from microduck.motion_heading_servo_v28 import MotionHeadingServo
from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
from tests.test_persistent_heading_v24 import orientation


class Float32HeadingTests(unittest.TestCase):
    def test_arbitrary_nonsaturating_commands_are_byte_identical(self):
        old,new=MotionHeadingServo(),Float32HeadingHeadroomServo()
        rng=np.random.default_rng(26090630)
        for i in range(1000):
            if i==500:old.reset();new.reset()
            command=np.array([rng.uniform(-.2,.2),0,rng.uniform(-.35,.35)],np.float32)
            if i%7==0:command[:]=0
            q=orientation(rng.uniform(-3,3))
            a,_=old.step(command,q);b,_=new.step(command,q)
            self.assertEqual(a.tobytes(),b.tobytes())
            self.assertEqual(old.reference,new.reference)
            self.assertEqual(old.filtered_correction,new.filtered_correction)

    def test_headroom_and_zero_stop_remain_bounded(self):
        s=Float32HeadingHeadroomServo()
        for _ in range(100):cmd,_=s.step([0,0,.738],orientation(0))
        self.assertGreater(cmd[2],.75);self.assertLessEqual(cmd[2],np.float32(.8))
        reference=s.reference
        cmd,_=s.step([0,0,0],orientation(.1))
        self.assertEqual(cmd.tobytes(),np.zeros(3,np.float32).tobytes())
        self.assertEqual(reference,s.reference)
