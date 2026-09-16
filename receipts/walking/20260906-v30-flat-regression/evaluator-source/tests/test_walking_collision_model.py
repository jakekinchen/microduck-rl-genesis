import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import mujoco
from experiments.walking.collision_model import ASSETS, ROOT, materialize, verify_physical_arrays


def collider_key(model, g):
    return (model.body(int(model.geom_bodyid[g])).name, model.mesh(int(model.geom_dataid[g])).name)


def allowed_pairs(model):
    active = [i for i in range(model.ngeom) if model.geom_bodyid[i] and (model.geom_contype[i] or model.geom_conaffinity[i])]
    return {tuple(sorted((collider_key(model, a), collider_key(model, b)))) for a in active for b in active
            if model.geom_bodyid[a] != model.geom_bodyid[b] and
            ((model.geom_contype[a] & model.geom_conaffinity[b]) or (model.geom_contype[b] & model.geom_conaffinity[a]))}


class CollisionModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='duck-collision-model-')
        cls.folder = Path(cls.temporary.name)
        cls.robot_path, cls.scene_path = materialize(cls.folder)
        cls.reduced = mujoco.MjModel.from_xml_path(str(ASSETS/'scene_walk.xml'))
        cls.full = mujoco.MjModel.from_xml_path(str(ASSETS/'scene.xml'))
        cls.model = mujoco.MjModel.from_xml_path(str(cls.scene_path))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_physical_fields_unchanged(self):
        verify_physical_arrays(self.reduced, self.model)
        verify_physical_arrays(self.full, self.model)

    def test_contact_filter_superset(self):
        self.assertLessEqual(allowed_pairs(self.reduced), allowed_pairs(self.model))
        self.assertLessEqual(allowed_pairs(self.full), allowed_pairs(self.model))
        self.assertIn(tuple(sorted((('trunk_base', 'np_f970'), ('leg', 'leg')))), allowed_pairs(self.model))
        self.assertIn(tuple(sorted((('trunk_base', 'power_support'), ('leg', 'leg')))), allowed_pairs(self.model))

    def test_every_collider_can_contact_floor(self):
        ids = [i for i in range(self.model.ngeom) if self.model.geom_contype[i] or self.model.geom_conaffinity[i]]
        self.assertGreater(len(ids), 6)
        for i in ids:
            self.assertEqual((int(self.model.geom_contype[i]), int(self.model.geom_conaffinity[i])), (1, 1))

    def test_visuals_and_existing_full_geometry_unchanged(self):
        for field in ('geom_type', 'geom_dataid', 'geom_pos', 'geom_quat', 'geom_size',
                      'geom_rgba', 'geom_matid', 'mesh_vert', 'mesh_face'):
            np.testing.assert_array_equal(getattr(self.full, field), getattr(self.model, field))

    def test_home_has_no_self_contacts(self):
        from microduck.constants import DEFAULT_JOINT_POS
        d = mujoco.MjData(self.model)
        d.qpos[:] = np.r_[0., 0., .125, 1., 0., 0., 0., DEFAULT_JOINT_POS]
        mujoco.mj_forward(self.model, d)
        self.assertFalse([c for c in d.contact if self.model.geom_bodyid[c.geom1] and self.model.geom_bodyid[c.geom2]])

    def test_materializer_is_idempotent_and_refuses_drift(self):
        before = self.scene_path.read_bytes()
        materialize(self.folder)
        self.assertEqual(before, self.scene_path.read_bytes())
        with tempfile.TemporaryDirectory(prefix='duck-collision-drift-') as folder:
            target = Path(folder)/'robot.xml'
            target.write_text('user owned')
            with self.assertRaises(ValueError):
                materialize(folder)
            self.assertEqual(target.read_text(), 'user owned')
            self.assertFalse((Path(folder)/'scene.xml').exists())


if __name__ == '__main__':
    unittest.main()
