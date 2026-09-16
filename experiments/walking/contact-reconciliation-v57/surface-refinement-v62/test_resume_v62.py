from pathlib import Path
import json
import tempfile
import unittest
import numpy as np
import trimesh
from cad_refinement_v62r8 import ROOT, refine


class ResumeTests(unittest.TestCase):
    def fixture(self, path):
        config = {'selection_threshold_m': .00018, 'refinement_target_m': .00012,
                  'maximum_depth': 16, 'maximum_leaves_per_parent': 128,
                  'maximum_parts_per_region': 256, 'maximum_total_parts': 8192,
                  'coacd_params': {}, 'reuse_mesh': 'fixture',
                  'source_stl_sha256': 'source-digest', 'parent_parts_sha256': 'parent-digest',
                  'region_directory': str((path/'regions').relative_to(ROOT)),
                  'reuse_index': str((path/'index.json').relative_to(ROOT)),
                  'reuse_protocol': str((path/'protocol.json').relative_to(ROOT))}
        (path/'index.json').write_text(json.dumps([{'parent_part': 0, 'output_start': 0,
                                                  'decision': 'unchanged', 'output_count': 1}]))
        (path/'protocol.json').write_text(json.dumps({'config': config,
            'meshes': {'fixture': {'source_stl': 'source.stl', 'parts_npz': 'parent.npz'}},
            'input_sha256': {'source.stl': 'source-digest', 'parent.npz': 'parent-digest'}}))
        return config

    def test_complete_prefix_retains_geometry(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.workspace') as directory:
            config = self.fixture(Path(directory))
            source = trimesh.creation.box(extents=[.01, .01, .01])
            parts, records = refine(source, [source], config)
            np.testing.assert_array_equal(parts[0].vertices, source.vertices)
            np.testing.assert_array_equal(parts[0].faces, source.faces)
            self.assertEqual(len(records), 1)

    def test_changed_source_or_local_recipe_rejects_reuse(self):
        for key, value in [('source_stl_sha256', 'changed'), ('parent_parts_sha256', 'changed'),
                           ('refinement_target_m', .0002)]:
            with tempfile.TemporaryDirectory(dir=ROOT/'.workspace') as directory:
                config = self.fixture(Path(directory))
                config[key] = value
                source = trimesh.creation.box(extents=[.01, .01, .01])
                with self.assertRaises(RuntimeError):
                    refine(source, [source], config)
