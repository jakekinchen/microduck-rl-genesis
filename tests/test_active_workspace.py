"""The working focus must bind visible evidence before steering inspection."""
import hashlib
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.active import focus, prepare
from duck_workspace.core import Inspector, read_json


class ActiveWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/workspace").mkdir(parents=True)
        (self.root / "world.py").write_text("fixture world")
        self.config = {"schema": "microduck.active-workspace/v1", "id": "fixture", "phase": "diagnose",
                       "question": "What causes this visible fall?", "case_id": "75003-figure-eight",
                       "suite_sha256": "a" * 64, "source_paths": ["world.py"],
                       "before_training": ["Diagnose before changing reward"], "boundary": "No launch authority"}
        for role, fell in (("primary", True), ("comparison", False)):
            directory = self.root / "receipts/laser-dynamic" / role
            (directory / "source").mkdir(parents=True)
            (directory / "source/world.py").write_text("fixture world")
            policy = role.encode()
            (directory / "policy.onnx").write_bytes(policy)
            digest = hashlib.sha256(policy).hexdigest()
            self.config[role] = str(directory.relative_to(self.root))
            self.config[role + "_policy_sha256"] = digest
            report = {"schema": "microduck.dynamic-laser-evaluation/v1", "canonical_held_out": False,
                      "split": "development", "policy_sha256": digest, "suite_sha256": "a" * 64,
                      "case_reports": [{"case_id": "75003-figure-eight", "fell": fell,
                                        "domain": {"push_at_s": 23., "sensor_delay_steps": 0}}]}
            (directory / "evaluation.json").write_text(json.dumps(report))
            rows = [{"case_id": "75003-figure-eight", "time_s": t, "fell": fell and t == 1.56,
                     "robot_xyz_m": [0., 0., .1], "action_rad": [0.] * 14} for t in (1.54, 1.56)]
            (directory / "trajectory.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            self.manifest(directory)
        self.write_config()

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self):
        (self.root / "docs/workspace/active-experiment.json").write_text(json.dumps(self.config))

    def manifest(self, directory, exclude=()):
        (directory / "SHA256SUMS").write_text("".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(directory)}\n"
            for path in sorted(directory.rglob("*")) if path.is_file() and path.name != "SHA256SUMS"
            and str(path.relative_to(directory)) not in exclude))

    def prepare(self):
        with patch("experiment_ops.activity.inspect", return_value={"status": "no_known_training_process"}):
            return prepare(self.root)

    def test_current_focus_and_first_fall_are_source_bound(self):
        result = self.prepare()
        self.assertTrue(result["ready_for_diagnosis"], result)
        self.assertEqual(result["cases"]["primary"]["first_fall"]["time_s"], 1.56)
        self.assertIsNone(result["cases"]["comparison"]["first_fall"])
        self.assertTrue(any("precedes" in value for value in result["observations"]))
        self.assertFalse(result["training_started"])
        self.assertFalse(result["execution_authorized_by_report"])

    def test_compressed_focus_retains_manifest_and_fall_bindings(self):
        directory = self.root / self.config["primary"]
        plain = directory / "trajectory.jsonl"
        compressed = directory / "trajectory.jsonl.gz"
        compressed.write_bytes(gzip.compress(plain.read_bytes()))
        plain.unlink()
        self.manifest(directory)
        result = self.prepare()
        self.assertTrue(result["ready_for_diagnosis"], result)
        self.assertEqual(result["cases"]["primary"]["first_fall"]["time_s"], 1.56)
        identity = result["cases"]["primary"]["trajectory"]
        self.assertEqual(identity["sha256"], hashlib.sha256(compressed.read_bytes()).hexdigest())
        detail = Inspector(self.root).detail(self.config["primary"])
        self.assertEqual(len(detail["trajectories"][self.config["case_id"]]), 2)
        self.manifest(directory, exclude=("trajectory.jsonl.gz",))
        with self.assertRaisesRegex(ValueError, "trajectory.*manifest"):
            self.prepare()

    def test_tampered_policy_cannot_select_focus(self):
        (self.root / self.config["primary"] / "policy.onnx").write_bytes(b"changed")
        self.assertFalse(self.prepare()["ready_for_diagnosis"])

    def test_single_baseline_is_not_an_invented_comparison(self):
        self.config.pop("comparison")
        self.config.pop("comparison_policy_sha256")
        self.write_config()
        result=self.prepare()
        self.assertTrue(result["ready_for_diagnosis"],result)
        self.assertNotIn("comparison",result["cases"])
        self.assertTrue(any("baseline only" in s for s in result["observations"]))

    def test_source_drift_is_reported_before_reproduction(self):
        (self.root / "world.py").write_text("changed")
        result = self.prepare()
        self.assertFalse(result["ready_for_diagnosis"])
        self.assertTrue(any("differs" in error for error in result["errors"]))

    def test_unmanifested_policy_trace_or_source_is_refused(self):
        directory = self.root / self.config["primary"]
        for missing in ("policy.onnx", "trajectory.jsonl", "source/world.py"):
            with self.subTest(missing):
                self.manifest(directory, exclude=(missing,))
                with self.assertRaises(ValueError):
                    self.prepare()

    def test_absent_or_reserved_focus_does_not_invent_a_selection(self):
        self.config["primary"] = "receipts/laser-dynamic/reserved-case"
        self.write_config()
        runs, _ = Inspector(self.root).evaluations()
        self.assertEqual(focus(self.root, runs)["status"], "unavailable")

    def test_wrong_policy_or_suite_identity_refuses_focus(self):
        for field in ("primary_policy_sha256", "suite_sha256"):
            saved = self.config[field]
            self.config[field] = "f" * 64
            self.write_config()
            self.assertFalse(self.prepare()["ready_for_diagnosis"])
            self.config[field] = saved

    def test_different_domains_do_not_become_controlled_comparison(self):
        directory = self.root / self.config["comparison"]
        path = directory / "evaluation.json"
        report = json.loads(path.read_text())
        report["case_reports"][0]["domain"]["sensor_delay_steps"] = 2
        path.write_text(json.dumps(report))
        self.manifest(directory)
        self.assertFalse(self.prepare()["ready_for_diagnosis"])

    def test_running_record_sources_are_checked_without_claiming_process_identity(self):
        directory = self.root / "logs/gait-v3"
        directory.mkdir(parents=True)
        record = {"status": "running", "variant": "gait-v3", "source_sha256": {
            "world.py": hashlib.sha256((self.root / "world.py").read_bytes()).hexdigest()}}
        (directory / "run.json").write_text(json.dumps(record))
        running = self.prepare()["active_training_records"][0]
        self.assertTrue(running["current_sources_match_record"])
        self.assertEqual(running["exact_process_to_run_binding"], "not_checked")
        (self.root / "world.py").write_text("drift")
        self.assertFalse(self.prepare()["active_training_records"][0]["current_sources_match_record"])

    def test_unreadable_training_evidence_reports_incomplete_inspection(self):
        logs = self.root / "logs"
        logs.mkdir()
        with tempfile.TemporaryDirectory() as external:
            target = Path(external)
            (target / "run.json").write_text('{"status":"running"}')
            (logs / "external-run").symlink_to(target, target_is_directory=True)
            with patch("duck_workspace.active.read_json", wraps=read_json) as reader:
                result = self.prepare()
            self.assertTrue(all(call.args[0].resolve() != target / "run.json"
                                for call in reader.call_args_list))
        self.assertEqual(result["focus"]["status"], "verified")
        self.assertFalse(result["ready_for_diagnosis"])
        self.assertEqual(result["active_training_records"], [])
        self.assertEqual(result["active_training_record_errors"], [{
            "path": "logs/external-run/run.json", "error": "symlinked evidence is not served"}])
        self.assertTrue(any("training record unavailable" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
