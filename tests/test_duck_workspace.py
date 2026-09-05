"""Inspection must not turn corrupt, unknown or draft data into authority."""
import hashlib
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.core import Inspector, check_spec, new_behavior, safe_path
from duck_workspace.server import handler_for
from scripts.scan_microduck_history import message


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.directory = self.root / "receipts/laser-follow/example"
        self.directory.mkdir(parents=True)
        self.report = {"schema": "microduck.laser-evaluation/v1", "held_out": False,
                       "proof_class": "first_party_development", "passed_cases": 0, "total_cases": 1,
                       "case_reports": [{"case_id": "forward", "passed": False}],
                       "target_source": "simulated-ground-truth"}
        self.write_report()
        self.inspector = Inspector(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write_report(self):
        (self.directory / "evaluation.json").write_text(json.dumps(self.report))

    def manifest(self, directory=None):
        directory = directory or self.directory
        lines = []
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name != "SHA256SUMS":
                lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(directory)}")
        (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n")

    def test_failed_evaluator_result_is_retained(self):
        self.manifest()
        data = self.inspector.snapshot()
        self.assertEqual(data["evaluations"][0]["passed"], 0)
        self.assertEqual(data["evaluations"][0]["proof_class"], "first_party_development")
        self.assertTrue(data["read_only"])
        self.assertEqual(data["evaluations"][0]["integrity"]["status"], "manifest_verified")

    def test_tampered_report_invalidates_cached_integrity(self):
        self.manifest()
        self.inspector.snapshot()
        self.report["passed_cases"] = 1
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"][0]["integrity"]["status"], "invalid")

    def test_manifest_must_cover_report(self):
        (self.directory / "dummy.json").write_text("{}")
        sha = hashlib.sha256(b"{}").hexdigest()
        (self.directory / "SHA256SUMS").write_text(f"{sha}  dummy.json\n")
        self.assertEqual(self.inspector.snapshot()["evaluations"][0]["integrity"]["status"], "unmanifested")

    def test_parent_manifest_is_supported(self):
        self.manifest(self.directory.parent)
        self.assertEqual(self.inspector.snapshot()["evaluations"][0]["integrity"]["status"], "manifest_verified")

    def test_missing_artifact_is_an_integrity_failure(self):
        path = self.directory / "forward.mp4"
        path.write_bytes(b"fake-video")
        self.manifest()
        path.unlink()
        self.assertEqual(self.inspector.snapshot()["evaluations"][0]["integrity"]["status"], "invalid")

    def test_malformed_run_does_not_hide_valid_runs(self):
        bad = self.directory.parent / "malformed"
        bad.mkdir()
        (bad / "evaluation.json").write_text("{")
        data = self.inspector.snapshot()
        self.assertEqual(len(data["evaluations"]), 1)
        self.assertEqual(len(data["errors"]), 1)

    def test_unknown_schema_has_no_invented_score(self):
        self.report["schema"] = "future-format/v9"
        self.write_report()
        run = self.inspector.snapshot()["evaluations"][0]
        self.assertIsNone(run["passed"])
        self.assertEqual(run["cases"], [])

    def test_dynamic_visible_development_preserves_new_metrics(self):
        self.report.update(schema="microduck.dynamic-laser-evaluation/v1", canonical_held_out=False, split="development")
        del self.report["held_out"]
        self.report["case_reports"][0].update(mean_visible_distance_m=.6, tracking_fraction=.2, deadline_misses=3)
        self.write_report()
        run = self.inspector.snapshot()["evaluations"][0]
        self.assertEqual(run["passed"], 0)
        self.assertEqual(run["cases"][0]["mean_visible_distance_m"], .6)
        self.assertNotIn("final_distance_m", run["cases"][0])

    def test_reserved_named_receipt_is_not_even_parsed(self):
        reserved = self.directory.parent / "reserved-candidate"
        reserved.mkdir()
        (reserved / "evaluation.json").write_text("deliberately not JSON")
        data = self.inspector.snapshot()
        self.assertEqual(len(data["evaluations"]), 1)
        self.assertEqual(data["errors"], [])

    def test_held_out_reports_are_not_displayed(self):
        self.report["held_out"] = True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])

    def test_no_raw_workspace_file_route(self):
        (self.root / "private.json").write_text('{"private":true}')
        for path in ("private.json", "../private.json", "/etc/passwd"):
            with self.assertRaises(ValueError):
                self.inspector.artifact(path)

    def test_symlinked_receipt_and_parent_are_rejected(self):
        with tempfile.TemporaryDirectory() as external:
            outside = Path(external) / "secret.json"
            outside.write_text("{}")
            (self.directory / "secret.json").symlink_to(outside)
            self.assertNotIn("secret.json", self.inspector.snapshot()["evaluations"][0]["artifacts"])
            (self.root / "alias").symlink_to(external, target_is_directory=True)
            with self.assertRaises(ValueError):
                safe_path(self.root, "alias/secret.json")

    def test_detail_preserves_case_timestamps_and_target_loss(self):
        points = [{"case_id": "forward", "time_s": .02, "visible": True},
                  {"case_id": "forward", "time_s": .04, "visible": False}]
        (self.directory / "trajectory.jsonl").write_text("\n".join(json.dumps(p) for p in points))
        detail = self.inspector.detail("receipts/laser-follow/example")
        self.assertEqual([p["time_s"] for p in detail["trajectories"]["forward"]], [.02, .04])
        self.assertFalse(detail["trajectories"]["forward"][1]["visible"])

    def test_video_origin_matches_each_retained_capture_schedule(self):
        rows = [{"case_id": "forward", "time_s": .02}, {"case_id": "forward", "time_s": .04}]
        (self.directory / "trajectory.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
        (self.directory / "forward.mp4").write_bytes(b"fixture")
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["video_time_origins_s"]["forward"], .02)
        self.report.update(schema="microduck.dynamic-laser-evaluation/v1", canonical_held_out=False, split="development")
        self.write_report()
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["video_time_origins_s"]["forward"], .04)

    def test_draft_is_incomplete_and_cannot_overwrite(self):
        path = new_behavior(self.root, "turn-to-sound", "Turn toward a sound")
        self.assertIn("success_metrics", check_spec(path / "spec.json"))
        self.assertIn("budget.training_iterations", check_spec(path / "spec.json"))
        with self.assertRaises(FileExistsError):
            new_behavior(self.root, "turn-to-sound", "Overwrite")
        with self.assertRaises(ValueError):
            new_behavior(self.root, "../../escape", "Escape")

    def test_recorded_starting_status_is_not_live_status(self):
        log = self.root / "logs/abandoned"
        log.mkdir(parents=True)
        (log / "run.json").write_text('{"status":"starting"}')
        self.assertEqual(self.inspector.snapshot()["training"][0]["process_liveness"], "not_checked")

    def test_malformed_draft_groups_remain_actionable(self):
        path = new_behavior(self.root, "draft", "Turn") / "spec.json"
        data = json.loads(path.read_text())
        data.update(budget=None, implementation=False, success_metrics="success")
        path.write_text(json.dumps(data))
        missing = check_spec(path)
        self.assertIn("budget.training_iterations", missing)
        self.assertIn("success_metrics must be a list", missing)

    def test_history_reads_phase_format_and_user_followups(self):
        item = message({"type": "message", "role": "assistant", "phase": "final_answer",
                        "content": [{"type": "output_text", "text": "Measured failure"}]}, "response_item")
        self.assertEqual(item["phase"], "final_answer")
        followup = message({"type": "item_completed", "item": {"type": "UserMessage",
                           "content": [{"type": "text", "text": "Change the target speed"}]}}, "event_msg")
        self.assertEqual(followup["text"], "Change the target speed")

    def test_history_does_not_extract_encrypted_reasoning(self):
        self.assertIsNone(message({"type": "reasoning", "encrypted_content": "opaque"}, "response_item"))

    def test_http_range_and_read_only_boundary(self):
        (self.directory / "forward.mp4").write_bytes(b"0123456789")
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.inspector))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port)
            connection.request("GET", "/artifact?path=receipts/laser-follow/example/forward.mp4", headers={"Range": "bytes=2-5"})
            response = connection.getresponse()
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b"2345")
            connection.request("POST", "/api/train")
            response = connection.getresponse()
            self.assertEqual(response.status, 501)
            response.read()
            connection.request("GET", "/api/snapshot", headers={"Host": "unrelated.example"})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
