import ast
from pathlib import Path
import tempfile
import unittest
import mujoco
import numpy as np
from experiments.walking.public_surface_v25 import configure_native,PROFILES,training_panels
from experiments.walking.collision_model import materialize

ROOT=Path(__file__).resolve().parents[1]


class PublicSurfaceTests(unittest.TestCase):
    def test_application_is_absolute_and_preserves_robot_inertials(self):
        with tempfile.TemporaryDirectory() as td:
            _,scene=materialize(td)
            m=mujoco.MjModel.from_xml_path(str(scene))
            baseline={k:getattr(m,k).copy() for k in ['body_mass','body_inertia','jnt_range','dof_armature','dof_damping']}
            configure_native(m,PROFILES[1]);first=m.geom_solref.copy(),m.geom_friction.copy()
            configure_native(m,PROFILES[3]);configure_native(m,PROFILES[1])
            np.testing.assert_array_equal(m.geom_solref,first[0]);np.testing.assert_array_equal(m.geom_friction,first[1])
            for k,v in baseline.items():np.testing.assert_array_equal(getattr(m,k),v)
            # Unit-friction non-sole colliders remain unit; internal sole-sole
            # friction becomes .1 and must be disclosed, not called invariant.
            soles={m.geom(n).id for n in ['left_foot_collision','right_foot_collision']}
            for i in range(m.ngeom):
                if m.geom_bodyid[i]!=0 and i not in soles:self.assertEqual(m.geom_friction[i,0],1.)

    def test_materialization_is_reproducible_and_refuses_drift(self):
        with tempfile.TemporaryDirectory() as td:
            p=training_panels(Path(td)/'panels.xml');original=p.read_bytes()
            training_panels(p);self.assertEqual(p.read_bytes(),original)
            m=mujoco.MjModel.from_xml_path(str(p))
            self.assertEqual(m.ngeom,4)
            np.testing.assert_allclose(m.geom_pos[:,2]+m.geom_size[:,2],0.,atol=1e-12)
            p.write_text('drift')
            with self.assertRaises(ValueError):training_panels(p)

    def test_genesis_scene_only_replaces_the_ground_construction(self):
        def scene_method(path,classname):
            tree=ast.parse((ROOT/path).read_text())
            cls=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name==classname)
            return next(m for m in cls.body if isinstance(m,ast.FunctionDef) and m.name=='_build_scene')
        old=scene_method('microduck/walking_contact_env.py','MicroduckContactAlignedWalkingEnv')
        new=scene_method('microduck/public_surface_env_v25.py','SurfaceSceneMixin')
        # First scene construction and all robot/index setup must be identical.
        self.assertEqual(ast.dump(old.body[0]),ast.dump(new.body[0]))
        self.assertEqual([ast.dump(x) for x in old.body[2:]],[ast.dump(x) for x in new.body[3:]])


if __name__=='__main__':unittest.main()
