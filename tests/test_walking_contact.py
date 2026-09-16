"""Native constraint timing is explicit and isolated from reward/action changes."""
import ast
import inspect
from pathlib import Path
import sys
import textwrap
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from microduck.walking_ground_env import MicroduckGroundAlignedWalkingEnv
from microduck.walking_contact_env import MicroduckContactAlignedWalkingEnv, MicroduckContactTrackingWalkingEnv
from microduck.walking_tracking_env import MicroduckTrackingWalkingEnv


class ContactAlignmentTests(unittest.TestCase):
    def test_scene_diff_only_sets_native_default_constraint_timing(self):
        import mujoco
        model = mujoco.MjModel.from_xml_path(str(ROOT/"microduck/assets/microduck/scene_walk.xml"))
        reference = float(model.geom("floor").solref[0])
        old = ast.parse(textwrap.dedent(inspect.getsource(MicroduckGroundAlignedWalkingEnv._build_scene)))
        new = ast.parse(textwrap.dedent(inspect.getsource(MicroduckContactAlignedWalkingEnv._build_scene)))
        found = 0
        for node in ast.walk(new):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "RigidOptions":
                matches = [k for k in node.keywords if k.arg == "constraint_timeconst"]
                self.assertEqual(len(matches), 1)
                self.assertEqual(ast.literal_eval(matches[0].value), reference)
                node.keywords = [k for k in node.keywords if k.arg != "constraint_timeconst"]
                found += 1
        self.assertEqual(found, 1)
        self.assertEqual(ast.dump(old), ast.dump(new))

    def test_tracking_variant_keeps_reward_and_action_functions_identical(self):
        for name in ("step", "_compute_rewards", "_compute_observations", "reset_idx", "_build_actuator"):
            self.assertIs(getattr(MicroduckContactTrackingWalkingEnv, name), getattr(MicroduckTrackingWalkingEnv, name))


if __name__ == "__main__":
    unittest.main(verbosity=2)
