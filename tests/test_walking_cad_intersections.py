import unittest
import numpy as np
from scripts.audit_walking_cad_intersections import intersection_witness


class TriangleWitnessTests(unittest.TestCase):
    def test_crossing_triangles(self):
        a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        b = np.array([[.2, .2, -1.], [.2, .2, 1.], [.8, .2, 0.]])
        result = intersection_witness(a, np.array([[0, 1, 2]]), b, np.array([[0, 1, 2]]))
        self.assertIsNotNone(result)
        self.assertEqual(result['triangle_a'], 0)
        self.assertEqual(result['triangle_b'], 0)

    def test_disjoint_triangles(self):
        a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        self.assertIsNone(intersection_witness(a, np.array([[0, 1, 2]]), a+2., np.array([[0, 1, 2]])))

    def test_coplanar_is_not_positive_witness(self):
        a = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
        self.assertIsNone(intersection_witness(a, np.array([[0, 1, 2]]), a, np.array([[0, 1, 2]])))


if __name__ == '__main__':
    unittest.main()
