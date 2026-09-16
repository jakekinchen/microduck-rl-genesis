"""Course boundary checks and observational invariance on exact motor actions."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from experiments.laser.course_v2 import laser_target,navigation_command,materialize_course,CourseWorld
from scripts.evaluate_laser_course import SOURCE,ROOT,collision_audit,physics_observer

class CourseTests(unittest.TestCase):
    def test_dot_moves_continuously_and_loss_stops(self):
        points=np.array([laser_target(t)[0] for t in np.arange(1,61,.02)])
        speed=np.linalg.norm(np.diff(points,axis=0),axis=1)/.02
        self.assertGreater(speed.min(),.07)
        self.assertLess(speed.max(),.11)
        for t in [0,.98,61,65.98]:
            target,visible=laser_target(t)
            self.assertFalse(visible)
            np.testing.assert_array_equal(navigation_command(target,[0,0],[1,0,0,0],visible),np.zeros(3))

    def test_navigation_does_not_mutate_state_and_bounds_commands(self):
        q=np.array([1.,0,0,0]);xy=np.zeros(2)
        for target in [[1,0],[0,1],[-1,0],[1,-1]]:
            c=navigation_command(target,xy,q,True)
            self.assertLessEqual(abs(c[2]),.650001)
            self.assertLessEqual(c[0],.120001)
            self.assertEqual(c[1],0)
        np.testing.assert_array_equal(xy,[0,0]);np.testing.assert_array_equal(q,[1,0,0,0])
        self.assertEqual(navigation_command([-1,0],xy,q,True)[0],0)
        with self.assertRaises(ValueError):navigation_command([np.nan,0],xy,q,True)

    def test_instrumentation_preserves_exact_actions_and_physics(self):
        with tempfile.TemporaryDirectory() as tmp:
            scene=materialize_course(Path(tmp)/'scene')
            def make():
                return CourseWorld(SOURCE/'policy.onnx',ROOT/'.workspace/bam',standing_policy=SOURCE/'standing/policy.onnx',
                    model_directory=ROOT/'experiments/walking/models/contact-v11',terrain_scene=scene,
                    domain={'mass_inertia_scale':1.,'sliding_friction_scale':1.},motor_ticks=4,sensor_ticks=1,yaw=0.,seed=26091301,render=False)
            first=make();before=first.core.data.qpos.copy()
            audit=collision_audit(first)
            self.assertEqual(len(audit['obstacles']),12)
            np.testing.assert_array_equal(before,first.core.data.qpos)
            controls=[]
            try:
                for i in range(150):
                    target,visible=laser_target(i*.02)
                    c=navigation_command(target,first.core.data.qpos[:2],first.core.data.qpos[3:7],visible)
                    first.step_command(c)
                    controls.append((c,first.last_action.copy(),first.core.data.qpos.copy(),first.core.data.qvel.copy()))
            finally:first.close()
            second=make()
            try:
                np.testing.assert_array_equal(before,second.core.data.qpos)
                with physics_observer(second) as samples:
                    for c,action,qpos,qvel in controls:
                        second.step_command(c)
                        self.assertEqual(action.tobytes(),second.last_action.tobytes())
                        self.assertEqual(qpos.tobytes(),second.core.data.qpos.tobytes())
                        self.assertEqual(qvel.tobytes(),second.core.data.qvel.tobytes())
                self.assertEqual(len(samples),600)
            finally:second.close()

if __name__=='__main__':unittest.main()
