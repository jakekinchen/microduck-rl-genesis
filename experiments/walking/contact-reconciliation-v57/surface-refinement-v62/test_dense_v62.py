import unittest
import numpy as np
from validate_dense_v62 import analytic_nearest


class AnalyticDistanceTests(unittest.TestCase):
    def test_face_edge_and_vertex_distances_at_three_scales(self):
        triangle = np.array([[[0., 0, 0], [1., 0, 0], [0, 1., 0]]])
        for scale in (1e-4, 1., 1000.):
            for point, expected in (([.2, .3, .4], .4), ([.5, -.2, 0], .2), ([-.3, -.4, 0], .5)):
                _, distance, _ = analytic_nearest(triangle*scale, np.array(point)*scale)
                self.assertAlmostEqual(distance/scale, expected, places=12)

    def test_global_search_selects_nearer_triangle(self):
        triangle = np.array([[[0., 0, 0], [1., 0, 0], [0, 1., 0]]])
        triangles = np.concatenate([triangle+np.array([0, 0, 1]), triangle])
        _, distance, index = analytic_nearest(triangles, np.array([.2, .3, .1]))
        self.assertAlmostEqual(distance, .1)
        self.assertEqual(index, 1)
