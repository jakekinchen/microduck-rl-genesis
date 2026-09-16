"""The ground fix changes only the native floor mask, not the robot or actions."""
import ast
import inspect
from pathlib import Path
import sys
import textwrap
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from microduck.velocity_env import MicroduckVelocityEnv
from microduck.walking_ground_env import MicroduckGroundAlignedWalkingEnv


class GroundAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import genesis as gs
        import torch
        torch.set_num_threads(1)
        gs.init(backend=gs.cpu,logging_level="warning",seed=76532)

    def test_scene_diff_is_only_explicit_plane_collision_masks(self):
        old=ast.parse(textwrap.dedent(inspect.getsource(MicroduckVelocityEnv._build_scene)))
        new=ast.parse(textwrap.dedent(inspect.getsource(MicroduckGroundAlignedWalkingEnv._build_scene)))
        matches=0
        for node in ast.walk(new):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="Plane":
                self.assertEqual({k.arg:ast.literal_eval(k.value) for k in node.keywords},{"contype":1,"conaffinity":1})
                node.keywords=[];matches+=1
        self.assertEqual(matches,1)
        self.assertEqual(ast.dump(old),ast.dump(new))

    def test_native_floor_keeps_feet_but_not_self_only_parts(self):
        from genesis.options.morphs import Plane
        floor=Plane(contype=1,conaffinity=1)
        self.assertTrue((floor.contype&1) or (floor.conaffinity&1))
        self.assertFalse((floor.contype&2) or (floor.conaffinity&2))


if __name__=="__main__":unittest.main(verbosity=2)
