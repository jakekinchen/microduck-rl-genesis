"""Run V59's unchanged contract cases against V62, plus scale regressions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import trimesh

import material_validation_v62 as current
from validate_dense_v62 import analytic_nearest

spec = importlib.util.spec_from_file_location(
    'v59_contract_tests', Path(__file__).parent.parent/'proxy-diagnostics-v59/test_material_validation.py')
previous_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous_tests)
previous_tests.MODULE = current
MaterialValidationTests = previous_tests.MaterialValidationTests


class UnitScaleRegressions(unittest.TestCase):
    def test_small_surface_distance_agrees_with_analytic_triangles(self):
        mesh = trimesh.creation.box(extents=[.0003, .0003, .001])
        points = mesh.triangles_center
        raw = trimesh.proximity.closest_point(mesh, points)[1]
        normalized = mesh.copy()
        normalized.apply_scale(1000.)
        stable = trimesh.proximity.closest_point(normalized, points*1000.)[1]/1000.
        exact = np.array([analytic_nearest(normalized.triangles, p*1000.)[1]/1000. for p in points])
        self.assertGreater(raw.max(), 1e-6)
        np.testing.assert_allclose(stable, exact, atol=1e-12, rtol=0)
        self.assertLess(stable.max(), 1e-12)

    def test_thin_cylinder_cap_exact_material_passes(self):
        mesh = trimesh.creation.cylinder(radius=.005, height=.002, sections=512)
        faces = mesh.faces.copy()
        for i in np.flatnonzero(np.abs(mesh.face_normals[:, 2]) > .99):
            center = np.argmin(np.linalg.norm(mesh.vertices[faces[i], :2], axis=1))
            faces[i] = np.roll(faces[i], 2-center)
        mesh = trimesh.Trimesh(mesh.vertices, faces, process=False)
        result = self.validate(mesh, lambda vertices: vertices)
        self.assertTrue(result['passed'], result['failures'])
        self.assertLess(result['max_sampled_excess_material_m'], 1e-9)
        self.assertLess(result['max_sampled_missing_material_m'], 1e-9)

    def test_real_three_tenths_mm_error_still_fails_both_directions(self):
        mesh = trimesh.creation.box(extents=[.01, .01, .01])
        result = self.validate(mesh, lambda vertices: vertices+np.array([.0003, 0., 0.]))
        self.assertFalse(result['passed'])
        self.assertEqual(set(result['failures']), {'sampled_missing_material', 'sampled_excess_material'})
        self.assertAlmostEqual(result['max_sampled_missing_material_m'], .0003, places=12)
        self.assertAlmostEqual(result['max_sampled_excess_material_m'], .0003, places=12)

    def validate(self, mesh, transform):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source.stl'
            source.write_bytes(mesh.export(file_type='stl'))
            canonical = current._source_mesh(source.read_bytes())
            parts = root/'parts.npz'
            np.savez(parts, v000=transform(canonical.vertices.copy()), f000=canonical.faces)
            complete = root/'complete.json'
            complete.write_text(json.dumps({
                'mesh': 'shape', 'parts': 1,
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'parts_sha256': hashlib.sha256(parts.read_bytes()).hexdigest(),
            }))
            result = current.validate_meshes({'shape': {
                'source_stl': source, 'parts_npz': parts, 'complete_json': complete}})
            self.assertEqual(result['settings']['sampled_tolerance_m'], .00025)
            self.assertFalse(result['model_admitted'])
            return result['meshes']['shape']


if __name__ == '__main__':
    unittest.main()
