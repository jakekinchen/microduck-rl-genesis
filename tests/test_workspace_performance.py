"""Individual viewer requests must retain receipt admission and tamper checks."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.core import Inspector


class SelectedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_id = "receipts/laser-follow/example"
        self.directory = self.root / self.run_id
        self.directory.mkdir(parents=True)
        self.report = {"schema": "microduck.laser-evaluation/v1", "held_out": False,
                       "passed_cases": 0, "total_cases": 1,
                       "case_reports": [{"case_id": "forward", "passed": False}]}
        (self.directory / "evaluation.json").write_text(json.dumps(self.report))
        self.video = self.directory / "forward.mp4"
        self.video.write_bytes(b"original")
        self.manifest(self.directory)
        self.inspector = Inspector(self.root)

    def manifest(self, directory):
        lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(directory)}"
                 for path in sorted(directory.rglob("*"))
                 if path.is_file() and path.name != "SHA256SUMS"]
        (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n")

    def test_selected_result_keeps_full_manifest_tamper_detection(self):
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "manifest_verified")
        previous = self.video.stat()
        self.video.write_bytes(b"tampered")  # Same size, with the old mtime restored.
        os.utime(self.video, ns=(previous.st_atime_ns, previous.st_mtime_ns))
        integrity = self.inspector.detail(self.run_id)["integrity"]
        self.assertEqual(integrity["status"], "invalid")
        self.assertEqual(integrity["mismatches"], ["forward.mp4"])
        self.video.unlink()
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "invalid")
        with self.assertRaises(ValueError):
            self.inspector.artifact(self.run_id + "/forward.mp4")

    def test_parent_manifest_still_checks_sibling_artifacts(self):
        sibling = self.directory.parent / "sibling.json"
        sibling.write_text("{}")
        (self.directory / "SHA256SUMS").unlink()
        self.manifest(self.directory.parent)
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "manifest_verified")
        sibling.write_text('{"changed":true}')
        integrity = self.inspector.detail(self.run_id)["integrity"]
        self.assertEqual(integrity["status"], "invalid")
        self.assertEqual(integrity["mismatches"], ["sibling.json"])

    def test_manifest_changes_are_rechecked(self):
        self.inspector.detail(self.run_id)
        manifest = self.directory / "SHA256SUMS"
        manifest.write_text("invalid manifest")
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "invalid")
        self.manifest(self.directory)
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "manifest_verified")
        manifest.unlink()
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "unmanifested")

    def test_admission_is_rechecked_after_report_changes(self):
        self.inspector.detail(self.run_id)
        self.report["held_out"] = True
        (self.directory / "evaluation.json").write_text(json.dumps(self.report))
        for request in (lambda: self.inspector.detail(self.run_id),
                        lambda: self.inspector.artifact(self.run_id + "/forward.mp4")):
            with self.assertRaises(ValueError):
                request()
        self.report["held_out"] = False
        (self.directory / "evaluation.json").write_text(json.dumps(self.report))
        self.assertEqual(self.inspector.artifact(self.run_id + "/forward.mp4"), self.video)
        (self.directory / "evaluation.json").unlink()
        with self.assertRaises(ValueError):
            self.inspector.detail(self.run_id)

    def test_new_run_is_discovered_without_restart(self):
        added_id = "receipts/laser-follow/added"
        with self.assertRaises(ValueError):
            self.inspector.detail(added_id)
        added = self.root / added_id
        added.mkdir()
        (added / "evaluation.json").write_text(json.dumps(self.report))
        self.assertEqual(self.inspector.detail(added_id)["id"], added_id)

    def test_individual_routes_reject_unindexed_and_reserved_paths(self):
        for prefix in ("private", "receipts/laser-follow/reserved-example"):
            directory = self.root / prefix
            directory.mkdir(parents=True)
            (directory / "evaluation.json").write_text(json.dumps(self.report))
            (directory / "forward.mp4").write_bytes(b"unindexed")
        for run_id in ("private", "receipts/laser-follow/reserved-example",
                       "../" + self.run_id, "/" + self.run_id,
                       self.run_id + "/../example", ""):
            with self.subTest(run_id=run_id):
                with self.assertRaises(ValueError):
                    self.inspector.detail(run_id)
                with self.assertRaises(ValueError):
                    self.inspector.artifact(run_id + "/forward.mp4")

    def test_symlinks_cannot_reuse_a_previous_verified_result(self):
        self.inspector.detail(self.run_id)
        outside = self.root / "outside.mp4"
        outside.write_bytes(b"original")
        self.video.unlink()
        self.video.symlink_to(outside)
        self.assertEqual(self.inspector.detail(self.run_id)["integrity"]["status"], "invalid")
        with self.assertRaises(ValueError):
            self.inspector.artifact(self.run_id + "/forward.mp4")
        relocated = self.root / "relocated"
        self.directory.rename(relocated)
        self.directory.symlink_to(relocated, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.inspector.detail(self.run_id)


if __name__ == "__main__":
    unittest.main()
