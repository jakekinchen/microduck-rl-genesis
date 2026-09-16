"""Adversarial boundary tests, using tiny traces; no simulator or GPU."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch

from experiment_ops.activity import inspect, parse_processes
from experiment_ops.compare import compare, load_trace
from experiment_ops.report import render

ROOT = Path(__file__).resolve().parents[1]


def row(t=0.02, case="forward"):
    return {"case_id": case, "time_s": t, "action_rad": [0.0]*14,
            "command": [0.2, 0.0, 0.0], "robot_xyz_m": [t, 0.0, 0.12],
            "target_xy_m": [0.6, 0.0], "fell": False, "visible": True}


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write(self, name, rows):
        path = self.root/name
        path.write_text("".join(json.dumps(r)+"\n" for r in rows))
        return path

    def result(self, a, b, **kwargs):
        return compare(self.write("a.jsonl", a), self.write("b.jsonl", b), **kwargs)

    def test_exact_repeat_excludes_clock_latency_but_not_actions(self):
        a, b = row(), row()
        a["latency_ms"], b["latency_ms"] = 2.0, 9.0
        result = self.result([a], [b])
        c = result["cases"][0]
        self.assertEqual(c["comparison_kind"], "fixed_recorded_actions")
        self.assertEqual(c["first_differences"], {})
        self.assertEqual(c["physics_causality"], "not_established")
        self.assertEqual(result["behavior_acceptance"], "not_evaluated")
        self.assertEqual(c["coverage"]["contacts"], {"left": 0, "right": 0})

    def test_compressed_trace_binds_stored_bytes_and_preserves_actions(self):
        plain = self.write("plain.jsonl", [row(), row(.04)])
        compressed = self.root / "compressed.jsonl.gz"
        compressed.write_bytes(gzip.compress(plain.read_bytes()))
        cases, identity = load_trace(compressed)
        self.assertEqual(identity["sha256"], hashlib.sha256(compressed.read_bytes()).hexdigest())
        self.assertEqual(identity["bytes"], compressed.stat().st_size)
        self.assertEqual(identity["decoded_bytes"], plain.stat().st_size)
        self.assertEqual(len(cases["forward"]), 2)
        self.assertTrue(compare(plain, compressed)["cases"][0]["recorded_action_values_equal"])

    def test_compressed_trace_cannot_bypass_decoded_or_line_budgets(self):
        path = self.root / "large.jsonl.gz"
        path.write_bytes(gzip.compress(b'{"case_id":"x","time_s":0.02,"padding":"' + b' ' * 10000 + b'"}\n'))
        self.assertLess(path.stat().st_size, 1024)
        with self.assertRaisesRegex(ValueError, "bounded read"):
            load_trace(path, max_bytes=1024)
        path.write_bytes(gzip.compress(b' ' * (128 * 1024 + 1)))
        with self.assertRaisesRegex(ValueError, "bounded read"):
            load_trace(path)
        path.write_bytes(gzip.compress(json.dumps(row()).encode())[:-6])
        with self.assertRaisesRegex(ValueError, "incomplete compressed"):
            load_trace(path)

    def test_feedback_divergence_is_localized_before_action_difference(self):
        a = [row(), row(0.04)]
        b = copy.deepcopy(a)
        b[0]["robot_xyz_m"][0] += 0.001
        b[1]["action_rad"][2] = 0.02
        c = self.result(a, b)["cases"][0]
        self.assertEqual(c["comparison_kind"], "different_recorded_actions")
        self.assertEqual(c["first_differences"]["robot_xyz_m"]["time_s"], 0.02)
        self.assertEqual(c["first_differences"]["action_rad"]["left_line"], 2)

    def test_action_tolerance_never_inherits_position_tolerance(self):
        a, b = row(), row()
        b["action_rad"][0] = 1e-15
        c = self.result([a], [b], position_tolerance_m=100)["cases"][0]
        self.assertFalse(c["recorded_action_values_equal"])

    def test_signed_zero_preserved(self):
        a, b = row(), row()
        b["action_rad"][0] = -0.0
        self.assertFalse(self.result([a], [b])["cases"][0]["recorded_action_values_equal"])

    def test_explicit_repeated_window_budget_remains_bounded(self):
        path = self.write("repeated.jsonl", [{"case_id": "repeat", "time_s": i*.02} for i in range(20001)])
        with self.assertRaisesRegex(ValueError, "row/case"):
            load_trace(path)
        cases, identity = load_trace(path, max_rows=50000, max_bytes=512*1024*1024)
        self.assertEqual(identity["rows"], 20001)
        self.assertEqual(len(cases["repeat"]), 20001)
        for budget in (True, 0, 50001, 1.5):
            with self.assertRaises(ValueError):
                load_trace(path, max_rows=budget)

    def test_truncation_is_not_a_matching_prefix_success(self):
        c = self.result([row(), row(0.04)], [row()])["cases"][0]
        self.assertEqual(c["comparison_kind"], "incomplete_or_misaligned")
        self.assertIsNone(c["recorded_action_values_equal"])
        self.assertEqual(c["first_unmatched_time_s"], 0.04)

    def test_different_case_order_aligns_by_identity(self):
        a, b = row(case="left"), row(case="right")
        result = self.result([a, b], [b, a])
        self.assertTrue(all(c["recorded_action_values_equal"] for c in result["cases"]))

    def test_missing_action_is_unknown(self):
        b = row()
        del b["action_rad"]
        c = self.result([row()], [b])["cases"][0]
        self.assertIsNone(c["recorded_action_values_equal"])
        self.assertEqual(c["comparison_kind"], "action_telemetry_missing")

    def test_missing_case_is_retained(self):
        result = self.result([row(case="left")], [row(case="right")])
        self.assertEqual(len(result["cases"]), 2)
        self.assertTrue(all(c["aligned_rows"] == 0 for c in result["cases"]))

    def test_contact_order_normalized_but_missing_contacts_unknown(self):
        a, b = row(), row()
        a["contacts"] = ["foot/ground", "ball/ground"]
        b["contacts"] = ["ball/ground", "foot/ground"]
        self.assertNotIn("contacts", self.result([a], [b])["cases"][0]["first_differences"])
        b["contacts"] = []
        self.assertIn("contacts", self.result([a], [b])["cases"][0]["first_differences"])

    def test_duplicate_and_out_of_order_timestamps_rejected(self):
        for rows in ([row(), row()], [row(0.04), row(0.02)]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.result(rows, [row()])

    def test_invalid_vector_and_bool_and_time_rejected(self):
        for field, value in (("action_rad", [0.0]*13), ("action_rad", [True]*14),
                             ("time_s", -1), ("time_s", True), ("fell", "false"),
                             ("robot_xyz_m", None), ("contacts", "foot/ground")):
            b = row()
            b[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.result([row()], [b])

    def test_nonfinite_duplicate_json_and_blank_rejected(self):
        path = self.root/"bad.jsonl"
        for text in ('{"case_id":"x","case_id":"y","time_s":0.02}',
                     '{"case_id":"x","time_s":NaN}',
                     '{"case_id":"x","time_s":1e999}', '\n', ''):
            path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_trace(path)

    def test_narrow_position_tolerance_preserves_raw_delta(self):
        a, b = row(), row()
        b["robot_xyz_m"][0] += 1e-7
        c = self.result([a], [b])["cases"][0]
        self.assertNotIn("robot_xyz_m", c["first_differences"])
        self.assertGreater(c["max_abs_component_error"]["robot_xyz_m"], 0)

    def test_sister_repo_action_width_explicit(self):
        a = row()
        a["action_rad"] = [0.0]*6
        c = self.result([a], [a], action_width=6)["cases"][0]
        self.assertTrue(c["recorded_action_values_equal"])

    def test_report_escapes_source_text(self):
        a = row(case='</script><script>alert("x")</script>')
        result = self.result([a], [a])
        text = render(result)
        self.assertNotIn(a["case_id"], text)
        self.assertIn('\\u003c/script\\u003e', text)
        self.assertNotIn('innerHTML', text)

    def test_data_cannot_expand_template_markers(self):
        a = row(case='__REPORT_SCRIPT__')
        html = render(self.result([a], [a]))
        payload = html.split('<script id="data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(payload)['cases'][0]['case_id'], '__REPORT_SCRIPT__')

    @unittest.skipUnless(shutil.which('node'), 'Node is optional; browser QA still required')
    def test_report_javascript_parses(self):
        result = subprocess.run(['node', '--check', str(ROOT/'experiment_ops/report.js')], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_output_refuses_overwrite_and_malformed_input_writes_nothing(self):
        source = self.write("source.jsonl", [row()])
        destination = self.root/"report"
        command = [sys.executable, str(ROOT/"scripts/duck_ops.py"), "compare", str(source), str(source), "--output", str(destination)]
        first = subprocess.run(command, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = (destination/"comparison.json").read_bytes()
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        self.assertEqual(original, (destination/"comparison.json").read_bytes())
        source.write_text('bad')
        command[-1] = str(self.root/"not-created")
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        self.assertFalse((self.root/"not-created").exists())


class ActivityTests(unittest.TestCase):
    def test_sequence_compute_is_detected(self):
        for entrypoint in ["probe_native_sequence_v44.py", "evaluate_native_sequence_flat_v44.py",
                           "evaluate_native_sequence_endurance_v44.py", "evaluate_native_sequence_surfaces_v44.py",
                           "evaluate_native_sequence_fresh_v44.py", "evaluate_native_sequence_flat_v44_r2.py",
                           "evaluate_native_sequence_surfaces_v44_r2.py", "evaluate_component_flat_v45.py",
                           "evaluate_component_endurance_v45.py", "probe_native_sequence_v46.py",
                           "evaluate_native_retention_flat_v46.py", "evaluate_native_retention_endurance_v46.py",
                           "evaluate_native_retention_surfaces_v46.py", "evaluate_native_retention_fresh_v46.py",
                           "probe_handoff_inspection_v47.py", "verify_handoff_inspection_v47.py", "probe_recovery_v49.py", "probe_native_sequence_v50.py",
                           "evaluate_native_retention_flat_v50.py", "evaluate_native_retention_endurance_v50.py", "evaluate_native_retention_surfaces_v50.py", "evaluate_native_retention_fresh_v50.py",
                           "probe_native_sequence_v48.py", "evaluate_native_standing_retention_flat_v48.py",
                           "evaluate_native_standing_retention_endurance_v48.py", "evaluate_native_standing_retention_surfaces_v48.py",
                           "evaluate_native_standing_retention_fresh_v48.py"]:
            result = parse_processes(f"28394 1 01:20 /x/python3.12 scripts/{entrypoint} --output private-path\n")
            self.assertEqual(result[0]["workload"], "simulation_diagnostic")

    def test_terrain_endurance_diagnostic_is_detected(self):
        result = parse_processes('28394 1 01:20 /x/python3.12 -u scripts/evaluate_walking_terrain_endurance.py --bank endurance\n')
        self.assertEqual(result[0]['workload'], 'simulation_diagnostic')

    def test_paired_engine_diagnostic_blocks_competing_compute(self):
        command = '28394 1 01:20 /x/python3.12 -u scripts/probe_walking_pair_genesis_r2.py --output private-path\n'
        ps = subprocess.CompletedProcess([], 0, command, '')
        cwd = subprocess.CompletedProcess([], 0, f'p28394\nfcwd\nn{ROOT}\n', '')
        with patch('experiment_ops.activity.subprocess.run', side_effect=[ps, cwd]):
            result = inspect(ROOT)
        self.assertEqual(result['status'], 'busy')
        self.assertEqual(result['processes'][0]['workload'], 'simulation_diagnostic')
        self.assertNotIn('private-path', json.dumps(result))

    def test_current_gait_trainer_is_detected(self):
        for entrypoint in ("train_laser_gait.py", "train_walking.py", "train_walking_controlled.py", "train_walking_posture.py", "train_walking_tracking.py", "train_walking_contact.py", "train_walking_balance.py", "train_walking_viability.py"):
            result = parse_processes(f'28394 1 01:20 /x/python3.12 scripts/{entrypoint} --run-id private-name\n')
            self.assertEqual([p["entrypoint"] for p in result], [entrypoint])
        self.assertNotIn("private-name", json.dumps(result))

    def test_only_python_training_commands_and_no_argument_disclosure(self):
        text = '12 1 01:20 /x/python3.12 -u scripts/train_laser.py --api-key SECRET\n13 1 01:20 /bin/zsh -c "python train.py"\n14 1 00:02 python3 scripts/evaluate_laser.py\n'
        result = parse_processes(text)
        self.assertEqual([p["pid"] for p in result], [12])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_failed_ps_is_unknown_not_idle(self):
        with patch('experiment_ops.activity.subprocess.run', side_effect=OSError("ps unavailable")):
            result = inspect(ROOT)
        self.assertEqual(result["status"], "unknown")

    def test_unresolved_ownership_stays_busy(self):
        ps = subprocess.CompletedProcess([], 0, '12 1 01:20 python3 scripts/train_laser.py\n', '')
        with patch('experiment_ops.activity.subprocess.run', side_effect=[ps, OSError("no cwd")]):
            result = inspect(ROOT)
        self.assertEqual(result["status"], "busy")
        self.assertEqual(result["processes"][0]["ownership"], "unknown")

    def test_another_checkout_still_reports_host_training_contention(self):
        ps = subprocess.CompletedProcess([], 0, '12 1 01:20 python3 scripts/train_laser.py\n', '')
        cwd = subprocess.CompletedProcess([], 0, 'p12\nfcwd\nn/different/checkout\n', '')
        with patch('experiment_ops.activity.subprocess.run', side_effect=[ps, cwd]):
            result = inspect(ROOT)
        self.assertEqual(result['status'], 'busy')
        self.assertEqual(result['processes'][0]['ownership'], 'different_directory')


if __name__ == '__main__':
    unittest.main()
