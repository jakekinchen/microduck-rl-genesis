import unittest
import numpy as np
import trimesh
from cad_refinement_v62r2 import to_manifold, from_manifold, refine, excess_distances, face_samples


class GeometryTests(unittest.TestCase):
    def test_small_triangle_surface_and_real_excess_have_correct_distances(self):
        source = trimesh.creation.box(extents=[.0003, .0003, .001])
        points = np.array([[.00005, 0, .0005], [.00005, 0, .0008]])
        np.testing.assert_allclose(excess_distances(source, points), [0, .0003], atol=1e-12)

    def test_convex_source_keeps_exact_input(self):
        source = trimesh.creation.box(extents=[.01, .01, .01])
        parts, records = refine(source, [source], self.config())
        np.testing.assert_array_equal(parts[0].vertices, source.vertices)
        self.assertEqual(records[0]['decision'], 'unchanged')

    def test_source_recess_is_preserved_and_partition_conserves_material(self):
        box = trimesh.creation.box(extents=[.01, .01, .004])
        cutter = trimesh.creation.box(extents=[.006, .006, .006])
        cutter.apply_translation([.004, .004, 0])
        source = from_manifold(to_manifold(box)-to_manifold(cutter))
        parts, records = refine(source, [box], self.config())
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(p.is_convex and p.is_watertight for p in parts))
        self.assertLessEqual(max(excess_distances(source, face_samples(p)).max() for p in parts), .00012)
        self.assertGreaterEqual(sum(p.volume for p in parts), source.volume-1e-15)
        self.assertEqual(records[0]['decision'], 'source_partition')

    def test_local_budget_failure_is_not_a_geometry_pass(self):
        box = trimesh.creation.box(extents=[.01, .01, .004])
        cutter = trimesh.creation.box(extents=[.006, .006, .006])
        cutter.apply_translation([.004, .004, 0])
        source = from_manifold(to_manifold(box)-to_manifold(cutter))
        config = self.config() | {'maximum_depth': 0}
        with self.assertRaises(RuntimeError):
            refine(source, [box], config)

    @staticmethod
    def config():
        return {'selection_threshold_m': .00018, 'refinement_target_m': .00012,
                'maximum_depth': 16, 'maximum_leaves_per_parent': 128, 'maximum_total_parts': 4096}


if __name__ == '__main__':
    unittest.main()
