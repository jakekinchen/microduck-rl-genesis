"""Small synthetic geometry checks; no simulator or generated CAD proxies."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import trimesh


SPEC = importlib.util.spec_from_file_location("material_validation", Path(__file__).with_name("material_validation.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MaterialValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def inputs(self, name, *, scale=1.0, invalid=False, open_surface=False):
        source = trimesh.creation.box(extents=[0.01, 0.01, 0.01])
        source_path = self.root / f"{name}.stl"
        source_path.write_bytes(source.export(file_type="stl"))
        parts_path = self.root / f"{name}.npz"
        vertices = source.vertices.copy() * scale
        faces = source.faces[:-1].copy() if open_surface else source.faces.copy()
        if invalid:
            vertices[0, 0] = np.nan
        np.savez(parts_path, v000=vertices, f000=faces)
        metadata = {
            "mesh": name, "parts": 1,
            "parts_sha256": hashlib.sha256(parts_path.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        }
        complete_path = self.root / f"{name}.json"
        complete_path.write_text(json.dumps(metadata))
        return {"source_stl": source_path, "parts_npz": parts_path, "complete_json": complete_path}

    def test_exact_box_pass_is_repeatable_and_does_not_claim_cavity_or_model(self):
        inputs = {"cube": self.inputs("cube")}
        first = MODULE.validate_meshes(inputs)
        second = MODULE.validate_meshes(inputs)
        self.assertEqual(first, second)
        self.assertTrue(first["sampled_material_gates_passed"])
        self.assertFalse(first["cavity_bank_evaluated"])
        self.assertFalse(first["cavity_gates_passed"])
        self.assertFalse(first["model_admitted"])
        self.assertFalse(first["model_compiled"])
        self.assertEqual(first["physics_steps"], 0)
        self.assertEqual(first["settings"]["sampled_tolerance_m"], 0.00025)
        self.assertEqual(first["meshes"]["cube"]["source_samples"], 20)
        self.assertEqual(first["meshes"]["cube"]["proxy_samples"], 20)
        self.assertTrue(all(value["sha256"] for value in first["meshes"]["cube"]["inputs"].values()))
        digest = first.pop("result_sha256")
        self.assertEqual(digest, MODULE._json_digest(first))

    def test_missing_archive_records_error_and_later_mesh_still_runs(self):
        missing = self.inputs("a_missing")
        missing["parts_npz"].unlink()
        report = MODULE.validate_meshes({"a_missing": missing, "z_good": self.inputs("z_good")})
        self.assertFalse(report["sampled_material_gates_passed"])
        self.assertTrue(report["meshes"]["z_good"]["passed"])
        self.assertEqual(report["meshes"]["a_missing"]["errors"][0]["stage"], "parts_npz")
        self.assertIsNone(report["meshes"]["a_missing"]["inputs"]["parts_npz"]["sha256"])

    def test_invalid_vertices_and_open_surface_are_rejected_without_aborting(self):
        report = MODULE.validate_meshes({
            "a_invalid": self.inputs("a_invalid", invalid=True),
            "b_open": self.inputs("b_open", open_surface=True),
            "z_good": self.inputs("z_good"),
        })
        self.assertEqual(report["meshes"]["a_invalid"]["errors"][0]["stage"], "proxy_geometry")
        self.assertIn("non_watertight_proxy", report["meshes"]["b_open"]["failures"])
        self.assertTrue(report["meshes"]["z_good"]["passed"])

    def test_missing_and_excess_material_are_separate_failures(self):
        report = MODULE.validate_meshes({
            "missing": self.inputs("missing", scale=0.8),
            "excess": self.inputs("excess", scale=1.2),
        })
        small, large = report["meshes"]["missing"], report["meshes"]["excess"]
        self.assertEqual(small["failures"], ["sampled_missing_material"])
        self.assertEqual(large["failures"], ["sampled_excess_material"])
        self.assertGreater(small["max_sampled_missing_material_m"], 0.001)
        self.assertGreater(large["max_sampled_excess_material_m"], 0.001)
        self.assertFalse(report["sampled_material_gates_passed"])

    def test_metadata_hash_mismatch_is_a_local_error(self):
        bad = self.inputs("a_bad")
        metadata = json.loads(bad["complete_json"].read_text())
        metadata["source_sha256"] = "0" * 64
        bad["complete_json"].write_text(json.dumps(metadata))
        report = MODULE.validate_meshes({"a_bad": bad, "z_good": self.inputs("z_good")})
        self.assertEqual(report["meshes"]["a_bad"]["errors"][0]["stage"], "metadata")
        self.assertTrue(report["meshes"]["z_good"]["passed"])

    def test_watertight_nonconvex_part_does_not_pass(self):
        spec = self.inputs("disconnected")
        left = trimesh.creation.box(extents=[0.004, 0.004, 0.004])
        right = left.copy()
        left.apply_translation([-0.003, 0, 0])
        right.apply_translation([0.003, 0, 0])
        mesh = trimesh.util.concatenate([left, right])
        np.savez(spec["parts_npz"], v000=mesh.vertices, f000=mesh.faces)
        metadata = json.loads(spec["complete_json"].read_text())
        metadata["parts_sha256"] = hashlib.sha256(spec["parts_npz"].read_bytes()).hexdigest()
        spec["complete_json"].write_text(json.dumps(metadata))
        result = MODULE.validate_meshes({"disconnected": spec})["meshes"]["disconnected"]
        self.assertTrue(result["all_parts_watertight"])
        self.assertFalse(result["all_parts_convex"])
        self.assertIn("non_convex_proxy", result["failures"])
        self.assertFalse(result["passed"])

    def test_empty_requested_bank_is_not_a_cavity_pass(self):
        report = MODULE.validate_meshes({"cube": self.inputs("cube")}, cavity_witnesses=[])
        self.assertTrue(report["sampled_material_gates_passed"])
        self.assertFalse(report["all_requested_checks_passed"])
        self.assertFalse(report["cavity_gates_passed"])

    def test_each_required_empty_side_is_checked_even_when_other_side_empty(self):
        # Source-local witnesses are caller assertions here; this specifically
        # tests the per-side rule, not the caller's source-frame conversion.
        witness = {"id": "per-side", "sides": [
            {"mesh": "cube", "local_point_m": [0, 0, 0],
             "source_inside_three_rays": [False, False, False], "source_distance_m": 0.001},
            {"mesh": "cube", "local_point_m": [0.02, 0, 0],
             "source_inside_three_rays": [False, False, False], "source_distance_m": 0.001},
        ]}
        report = MODULE.validate_meshes({"cube": self.inputs("cube")}, cavity_witnesses=[witness])
        check = report["cavity_checks"][0]
        self.assertTrue(check["no_false_pair_contact_at_witness"])
        self.assertFalse(check["source_cavities_preserved"])
        self.assertFalse(check["sides"][0]["cavity_preserved"])
        self.assertTrue(check["sides"][1]["cavity_preserved"])
        self.assertFalse(report["all_requested_checks_passed"])

    def test_absent_proxy_side_is_unknown_and_cannot_pass(self):
        witness = {"id": "missing-side", "sides": [
            {"mesh": mesh, "local_point_m": [0.02, 0, 0],
             "source_inside_three_rays": [False, False, False], "source_distance_m": 0.001}
            for mesh in ("cube", "absent")
        ]}
        report = MODULE.validate_meshes({"cube": self.inputs("cube")}, cavity_witnesses=[witness])
        check = report["cavity_checks"][0]
        self.assertIsNone(check["sides"][1]["inside_convex_part_union"])
        self.assertFalse(check["passed"])
        self.assertFalse(report["cavity_gates_passed"])


if __name__ == "__main__":
    unittest.main()
