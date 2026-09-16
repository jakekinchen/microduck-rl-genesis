import unittest
import numpy as np
import trimesh
from parallel_geometry_v62 import initialize, score_points


class PointQueryTests(unittest.TestCase):
    def test_inside_outside_and_unit_normalization(self):
        source = trimesh.creation.box(extents=[.01, .01, .01])
        initialize(source.export(file_type='stl'))
        points = np.array([[0., 0, 0], [.006, 0, 0], [.0049, 0, 0]])
        for scale in (1., 1000.):
            result = score_points((7, points, scale))
            self.assertEqual(result['part'], 7)
            self.assertEqual(result['samples'], 3)
            self.assertEqual(result['violations'], 1)
            self.assertAlmostEqual(max(x['distance_m'] for x in result['witnesses']), .001, places=8)
