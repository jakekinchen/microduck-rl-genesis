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
from duck_workspace.core import Inspector, check_spec, new_behavior, safe_path, training_counts, sections, case_failure_summary
from duck_workspace.server import handler_for
from scripts.scan_microduck_history import message


class WorkspaceTests(unittest.TestCase):
    def test_failure_summary_exposes_posture_and_preserves_unknowns(self):
        self.assertEqual(case_failure_summary({"passed": False, "failures": [
            "posture_maximum_mean_joint_error_rad", "posture_p95_worst_joint_error_rad",
            "mean_abs_yaw_error_rad_s"]}), "Head posture; Turning accuracy")
        self.assertEqual(case_failure_summary({"passed": False, "failures": ["new_gate"]}), "new gate")
        self.assertIn("not recorded", case_failure_summary({"passed": False}))
        self.assertEqual(case_failure_summary({}), "Outcome not recorded.")
        self.assertIn("not physical or full walking acceptance", case_failure_summary({"passed": True}))

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

    def test_gait_reader_keeps_target_and_gait_gates_separate(self):
        self.report = {"schema": "microduck.laser-gait-evaluation/v3", "proof_class": "visible_development",
                       "reserved_opened": False, "physical_transfer_validated": False, "passed_cases": 0,
                       "spec_sha256": "a" * 64, "case_reports": [{"case_id": "face-circle",
                       "development_passed": False, "failures": ["missing_bilateral_steps"],
                       "target": {"passed": True, "fell": False, "mean_visible_distance_m": .2},
                       "gait": {"rejection_gate_passed": False}}]}
        self.write_report()
        run = self.inspector.snapshot()["evaluations"][0]
        self.assertEqual((run["passed"], run["total"]), (0, 1))
        self.assertFalse(run["cases"][0]["passed"])
        self.assertTrue(run["cases"][0]["target"]["passed"])
        self.assertEqual(run["suite_sha256"], "a" * 64)
        (self.directory / "face-circle.mp4").write_bytes(b"fixture")
        (self.directory / "trajectory.jsonl").write_text(json.dumps({"case_id": "face-circle", "time_s": .02})+"\n")
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["video_time_origins_s"]["face-circle"], .02)
        self.report["case_reports"][0]["development_passed"] = True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])

    def test_reserved_gait_result_is_not_admitted(self):
        self.report.update(schema="microduck.laser-gait-evaluation/v3", proof_class="visible_development",
                           reserved_opened=True, physical_transfer_validated=False)
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])

    def test_v4_gait_negative_is_visible_without_weakening_admission(self):
        self.report = {"schema": "microduck.laser-gait-evaluation/v4", "proof_class": "visible_development",
                       "reserved_opened": False, "physical_transfer_validated": False, "passed_cases": 0,
                       "spec_sha256": "a" * 64, "case_reports": [{"case_id": "front-circle",
                       "development_passed": False, "failures": ["missing_bilateral_steps"],
                       "target": {"passed": True, "fell": False},
                       "gait": {"rejection_gate_passed": False, "qualified_swings_left_right": [0, 0]}}]}
        self.write_report()
        self.manifest()
        snapshot = self.inspector.snapshot()
        self.assertEqual(snapshot["errors"], [])
        run = snapshot["evaluations"][0]
        self.assertEqual((run["passed"], run["total"]), (0, 1))
        self.assertEqual(run["integrity"]["status"], "manifest_verified")
        self.assertTrue(run["cases"][0]["target"]["passed"])
        self.assertFalse(run["cases"][0]["passed"])
        self.report["case_reports"][0]["development_passed"] = True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])
        self.report["case_reports"][0]["development_passed"] = False
        self.report["reserved_opened"] = True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])

    def test_reserved_named_receipt_is_not_even_parsed(self):
        reserved = self.directory.parent / "reserved-candidate"
        reserved.mkdir()
        (reserved / "evaluation.json").write_text("deliberately not JSON")
        data = self.inspector.snapshot()
        self.assertEqual(len(data["evaluations"]), 1)
        self.assertEqual(data["errors"], [])

    def test_walking_timing_reader_preserves_failure_and_refuses_false_pass(self):
        self.report={"schema":"microduck.walking-evaluation/v1","proof_class":"visible_development",
                     "reserved_opened":False,"physical_transfer_validated":False,"held_out":False,
                     "passed_cases":0,"total_cases":1,"case_reports":[{"case_id":"timed-turn","passed":False,
                     "failures":["no_useful_turning"],"gait":{"fell":False},"metrics":{"mean_abs_yaw_error_rad_s":.5}}]}
        self.write_report();self.manifest()
        run=self.inspector.snapshot()["evaluations"][0]
        self.assertEqual((run["passed"],run["total"]),(0,1))
        self.assertEqual(run["cases"][0]["metrics"]["mean_abs_yaw_error_rad_s"],.5)
        self.report["case_reports"][0]["passed"]=True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"],[])

    def test_held_out_reports_are_not_displayed(self):
        self.report["held_out"] = True
        self.write_report()
        self.assertEqual(self.inspector.snapshot()["evaluations"], [])

    def test_additive_posture_failure_cannot_be_hidden_by_motor_pass(self):
        self.report={"schema":"microduck.walking-evaluation/v1","acceptance_variant":"motor-plus-neutral-head-v1",
                     "proof_class":"visible_development","reserved_opened":False,"physical_transfer_validated":False,
                     "held_out":False,"passed_cases":0,"total_cases":1,"case_reports":[{"case_id":"head",
                     "passed":False,"failures":["posture_maximum_mean_joint_error_rad"],"gait":{"fell":False},
                     "motor_battery_passed":True,"posture":{"passed":False}}]}
        self.write_report();self.manifest()
        self.assertEqual(self.inspector.snapshot()["evaluations"][0]["passed"],0)
        self.report["passed_cases"]=1
        self.report["case_reports"][0].update(passed=True,failures=[])
        self.write_report();self.manifest()
        self.assertEqual(self.inspector.snapshot()["evaluations"],[])

    def heading_fixture(self):
        policy = b"synthetic UI fixture, not a policy"
        self.report = {"schema": "microduck.walking-evaluation/v1", "proof_class": "visible_development",
                       "reserved_opened": False, "physical_transfer_validated": False, "held_out": False,
                       "policy_sha256": hashlib.sha256(policy).hexdigest(), "passed_cases": 1, "total_cases": 1,
                       "case_reports": [{"case_id": "forward", "passed": True, "failures": [], "gait": {"fell": False}}]}
        self.write_report()
        (self.directory / "policy.onnx").write_bytes(policy)
        (self.directory / "trajectory.jsonl").write_text("")
        (self.directory / "training.json").write_text(json.dumps({"status": "completed", "checkpoint_sha256": "a" * 64}))
        self.manifest()
        sibling = self.directory.with_name(self.directory.name + "-heading")
        sibling.mkdir()
        heading = {"schema": "microduck.walking-heading-evaluation/v1", "held_out": False,
                   "physical_transfer_validated": False, "policy_sha256": self.report["policy_sha256"],
                   "checkpoint_sha256": "a" * 64, "total_cases": 1, "original_passed_cases": 1,
                   "heading_passed_cases": 0, "combined_passed_cases": 0,
                   "input_sha256": {name: hashlib.sha256((self.directory / name).read_bytes()).hexdigest()
                                    for name in ("SHA256SUMS", "evaluation.json", "trajectory.jsonl", "training.json")},
                   "case_reports": [{"case_id": "forward", "original_passed": True, "combined_passed": False,
                                     "heading": {"passed": False, "failures": ["endpoint_heading_error_deg"],
                                                 "metrics": {"endpoint_heading_error_deg": 35.0}}}]}
        self.write_heading(sibling, heading)
        return sibling, heading

    def write_heading(self, sibling, heading):
        (sibling / "evaluation.json").write_text(json.dumps(heading))
        self.manifest(sibling)

    def test_verified_heading_failure_does_not_rewrite_original_motor_pass(self):
        sibling, _ = self.heading_fixture()
        before = (self.directory / "evaluation.json").read_bytes()
        detail = self.inspector.detail("receipts/laser-follow/example")
        self.assertEqual(detail["passed"], 1)
        self.assertTrue(detail["cases"][0]["passed"])
        self.assertEqual(detail["heading_evidence"]["status"], "verified")
        self.assertEqual(detail["heading_evidence"]["combined_passed_cases"], 0)
        self.assertEqual(detail["heading_evidence"]["receipt"], str(sibling.relative_to(self.root)))
        self.assertEqual(before, (self.directory / "evaluation.json").read_bytes())

    def test_missing_heading_is_unknown_not_original_pass(self):
        sibling, _ = self.heading_fixture()
        sibling.rename(sibling.with_name("reserved-heading-do-not-open"))
        evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
        self.assertEqual(evidence, {"status": "missing", "combined_passed_cases": None})

    def test_heading_wrong_policy_checkpoint_or_input_is_invalid(self):
        sibling, heading = self.heading_fixture()
        mutations = (("policy_sha256", "b" * 64), ("checkpoint_sha256", "b" * 64),
                     ("input_sha256", {}), ("held_out", True), ("physical_transfer_validated", True))
        for field, value in mutations:
            with self.subTest(field=field):
                self.write_heading(sibling, {**heading, field: value})
                result = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
                self.assertEqual(result["status"], "invalid")
                self.assertIsNone(result["combined_passed_cases"])

    def test_heading_inconsistent_count_and_case_are_invalid(self):
        sibling, heading = self.heading_fixture()
        for field, value in (("combined_passed_cases", 1), ("heading_passed_cases", True),
                             ("case_reports", []), ("case_reports", heading["case_reports"] * 2)):
            with self.subTest(field=field, value=value):
                self.write_heading(sibling, {**heading, field: value})
                self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")
        heading["case_reports"][0]["combined_passed"] = True
        self.write_heading(sibling, heading)
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_heading_stale_parent_and_tampered_sibling_fail_closed(self):
        sibling, heading = self.heading_fixture()
        self.inspector.detail("receipts/laser-follow/example")
        heading["combined_passed_cases"] = 1
        (sibling / "evaluation.json").write_text(json.dumps(heading))
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")
        heading["combined_passed_cases"] = 0
        self.write_heading(sibling, heading)
        (self.directory / "trajectory.jsonl").write_text("\n")
        self.manifest()
        run = self.inspector.evaluations("receipts/laser-follow/example")[0][0]
        self.assertEqual(self.inspector.heading_evidence(self.directory, run)["status"], "invalid")

    def test_heading_requires_manifest_coverage_of_training_and_policy(self):
        sibling, heading = self.heading_fixture()
        manifest = self.directory / "SHA256SUMS"
        manifest.write_text("\n".join(line for line in manifest.read_text().splitlines() if "policy.onnx" not in line) + "\n")
        heading["input_sha256"]["SHA256SUMS"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.write_heading(sibling, heading)
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_heading_symlinked_sibling_is_rejected(self):
        sibling, _ = self.heading_fixture()
        other = sibling.with_name("other")
        sibling.rename(other)
        sibling.symlink_to(other, target_is_directory=True)
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def complete_controller_fixture(self):
        self.heading_fixture()
        self.report.update(acceptance_variant="imu-heading-command-servo-v12",
                           controller="explicit upstream IMU controller, synthetic fixture",
                           passed_cases=0, model_scope={"variant": "complete-contact-v11", "old_reduced_model_acceptance": False})
        case = self.report["case_reports"][0]
        case.update(passed=False, failures=["self_contact:self_penetration_over_1mm"],
                    original_motor_posture_passed=True, motor_battery_passed=True,
                    posture={"passed": True}, heading={"passed": True, "failures": [], "metrics": {"endpoint_heading_error_deg": 1.}},
                    self_contact={"passed": False, "failures": ["self_penetration_over_1mm"]})
        for name in ("scene", "robot"):
            path = self.directory/f"evaluator-source/experiments/walking/models/contact-v11/{name}.xml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"synthetic {name} UI identity fixture, not a physical model")
            self.report["model_scope"][name+"_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_report()
        self.manifest()

    def test_embedded_body_failure_is_not_hidden_by_heading_and_motor_pass(self):
        self.complete_controller_fixture()
        before = (self.directory/"evaluation.json").read_bytes()
        evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
        self.assertEqual(evidence["status"], "verified")
        self.assertEqual((evidence["original_passed_cases"], evidence["heading_passed_cases"], evidence["self_contact_passed_cases"], evidence["combined_passed_cases"]), (1, 1, 0, 0))
        self.assertIn("IMU", evidence["controller"])
        self.assertEqual(before, (self.directory/"evaluation.json").read_bytes())

    def test_embedded_false_combined_pass_is_refused(self):
        self.complete_controller_fixture()
        self.report["case_reports"][0].update(passed=True, failures=[])
        self.report["passed_cases"] = 1
        self.write_report()
        self.manifest()
        runs, errors = self.inspector.evaluations("receipts/laser-follow/example")
        self.assertEqual(runs, [])
        self.assertTrue(errors)

    def test_embedded_model_hash_or_scope_is_not_accepted(self):
        self.complete_controller_fixture()
        scope = self.report["model_scope"].copy()
        for replacement in ({**scope, "robot_sha256": "b"*64}, {**scope, "old_reduced_model_acceptance": True}):
            self.report["model_scope"] = replacement
            self.write_report()
            self.manifest()
            evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
            self.assertEqual(evidence["status"], "invalid")
            self.assertIsNone(evidence["combined_passed_cases"])

    def test_embedded_omitted_model_manifest_entry_is_invalid(self):
        self.complete_controller_fixture()
        path = self.directory/"SHA256SUMS"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.endswith("/robot.xml"))+"\n")
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_embedded_gate_booleans_and_failure_lists_are_strict(self):
        self.complete_controller_fixture()
        self.report["case_reports"][0]["heading"]["passed"] = 1
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.evaluations("receipts/laser-follow/example")[0], [])
        self.report["case_reports"][0]["heading"] = {"passed": True, "failures": ["hidden failure"]}
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.evaluations("receipts/laser-follow/example")[0], [])

    def test_embedded_all_gates_pass_remains_controller_scoped(self):
        self.complete_controller_fixture()
        self.report["case_reports"][0].update(passed=True, failures=[], self_contact={"passed": True, "failures": []})
        self.report["passed_cases"] = 1
        self.write_report()
        self.manifest()
        evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
        self.assertEqual(evidence["combined_passed_cases"], 1)
        self.assertIn("not raw-policy", evidence["boundary"])

    def standing_fixture(self):
        self.complete_controller_fixture()
        self.report.update(acceptance_variant="command-stand-switch-v14", standing_policy_used=True)
        case = self.report["case_reports"][0]
        case.update(self_contact={"passed": True, "failures": []},
                    self_load={"passed": False, "failures": ["continuous_body_bracing"]},
                    failures=["self_load:continuous_body_bracing"])
        for relative in ("source-checkpoint.pt", "standing/source-checkpoint.pt", "standing/policy.onnx"):
            path = self.directory/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic component fixture, not executable policy")
        training = self.directory/"training.json"
        record = json.loads(training.read_text())
        record["checkpoint_sha256"] = hashlib.sha256((self.directory/"source-checkpoint.pt").read_bytes()).hexdigest()
        training.write_text(json.dumps(record))
        (self.directory/"standing/training.json").write_text(json.dumps(record))
        self.report["standing_policy_sha256"] = hashlib.sha256((self.directory/"standing/policy.onnx").read_bytes()).hexdigest()
        self.write_report()
        self.manifest()

    def test_body_bracing_failure_cannot_hide_behind_geometry_pass(self):
        self.standing_fixture()
        e = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
        self.assertEqual(e["status"], "verified")
        self.assertEqual((e["self_contact_passed_cases"], e["self_load_passed_cases"], e["combined_passed_cases"]), (1, 0, 0))

    def test_ramped_walking_v18_preserves_every_component_gate(self):
        self.standing_fixture()
        self.report["acceptance_variant"] = "unbraced-walking-ramped-v18"
        self.write_report()
        self.manifest()
        evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
        self.assertEqual(evidence["status"], "verified")
        self.assertEqual(evidence["combined_passed_cases"], 0)
        self.report["standing_policy_used"] = False
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_heading_variants_preserve_load_rejection_and_standing_identity(self):
        self.standing_fixture()
        valid_sha = self.report["standing_policy_sha256"]
        for variant in ["yaw-refinement-filtered-heading-v21", "heading-persistence-v24-flat-regression",
                        "motion-heading-v28-flat-regression", "heading-headroom-v29-flat-regression",
                        "heading-headroom-v30-flat-regression", "stopping-ramp-v38-flat-regression",
                        "native-standing-v41-flat-regression", "native-standing-v42-flat-regression",
                        "native-sequence-v44-flat-regression", "component-isolation-v45-flat", "native-retention-v46-flat-regression"]:
            with self.subTest(variant=variant):
                self.report["acceptance_variant"] = variant
                self.report["standing_policy_sha256"] = valid_sha
                self.write_report()
                self.manifest()
                evidence = self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]
                self.assertEqual(evidence["status"], "verified")
                self.assertEqual(evidence["self_load_passed_cases"], 0)
                self.assertEqual(evidence["combined_passed_cases"], 0)
                self.report["standing_policy_sha256"] = "b"*64
                self.write_report()
                self.manifest()
                self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_body_bracing_false_combined_pass_or_missing_gate_rejected(self):
        self.standing_fixture()
        case = self.report["case_reports"][0]
        case.update(passed=True, failures=[])
        self.report["passed_cases"] = 1
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.evaluations("receipts/laser-follow/example")[0], [])
        case.pop("self_load")
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.evaluations("receipts/laser-follow/example")[0], [])

    def test_standing_policy_identity_and_use_are_required(self):
        self.standing_fixture()
        self.report["standing_policy_sha256"] = "b"*64
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")
        self.report["standing_policy_sha256"] = hashlib.sha256((self.directory/"standing/policy.onnx").read_bytes()).hexdigest()
        self.report["standing_policy_used"] = False
        self.write_report()
        self.manifest()
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

    def test_standing_component_manifest_omission_is_rejected(self):
        self.standing_fixture()
        path = self.directory/"SHA256SUMS"
        path.write_text("\n".join(line for line in path.read_text().splitlines() if not line.endswith("standing/policy.onnx"))+"\n")
        self.assertEqual(self.inspector.detail("receipts/laser-follow/example")["heading_evidence"]["status"], "invalid")

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

    def test_detail_preserves_actor_mode_and_all_physics_load_samples(self):
        loads = [{"interval_start_s": i*.005, "total_normal_n": float(i)} for i in range(4)]
        row = {"case_id": "forward", "time_s": .02, "session_time_s": 18.02,
               "actor_mode": "standing", "self_load_physics": loads}
        (self.directory/"trajectory.jsonl").write_text(json.dumps(row)+"\n")
        point = self.inspector.detail("receipts/laser-follow/example")["trajectories"]["forward"][0]
        self.assertEqual(point["self_load_physics"], loads)
        self.assertEqual(point["actor_mode"], "standing")
        self.assertEqual(point["session_time_s"], 18.02)

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

    def test_running_counter_is_not_a_zero_transition_budget(self):
        result = training_counts({"status": "running", "planned_new_transitions": 36864000, "new_transitions": 0})
        self.assertEqual(result["planned_transitions"], 36864000)
        self.assertIsNone(result["finalized_completed_transitions"])
        self.assertIsNone(result["legacy_recorded_transitions"])

    def test_recorded_running_work_is_first_without_claiming_liveness(self):
        for name, status in (("a-running", "running"), ("b-starting", "starting"), ("z-completed", "completed")):
            folder = self.root/"logs"/name
            folder.mkdir(parents=True)
            (folder/"run.json").write_text(json.dumps({"status": status}))
        rows = self.inspector.snapshot()["training"]
        self.assertEqual([r["id"] for r in rows], ["a-running", "b-starting", "z-completed"])
        self.assertTrue(all(r["process_liveness"] == "not_checked" for r in rows))

    def test_interrupted_count_stays_separate_from_plan_and_partial_work(self):
        result = training_counts({"status": "interrupted", "planned_new_transitions": 24576000,
                                  "new_transitions": 7962624, "partial_iteration_transitions": "unknown"})
        self.assertEqual(result["planned_transitions"], 24576000)
        self.assertEqual(result["finalized_completed_transitions"], 7962624)
        self.assertTrue(result["partial_iteration_unknown"])

    def test_legacy_count_does_not_become_completed_or_planned(self):
        result = training_counts({"status": "failed", "new_transitions": 24576000})
        self.assertIsNone(result["planned_transitions"])
        self.assertIsNone(result["finalized_completed_transitions"])
        self.assertEqual(result["legacy_recorded_transitions"], 24576000)

    def test_completed_and_invalid_transition_counts(self):
        self.assertEqual(training_counts({"status": "completed", "planned_new_transitions": 7680,
                                          "new_transitions": 7680})["finalized_completed_transitions"], 7680)
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                training_counts({"planned_new_transitions": bad})

    def test_history_is_separate_from_current_status(self):
        result = sections("## Current Status\nCurrent run only.\n## Historical context\nOld negative results.")
        self.assertEqual(result["Current Status"], "Current run only.")
        self.assertEqual(result["Historical context"], "Old negative results.")

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
