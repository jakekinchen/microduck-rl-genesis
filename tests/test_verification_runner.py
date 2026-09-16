"""Exercise runner outcomes with isolated tiny suites, never simulator tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VerificationRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "tests").mkdir()

    def run_fixture(self, source, pattern="test_fixture.py"):
        (self.root / "tests/test_fixture.py").write_text(textwrap.dedent(source))
        result_path = self.root / "result.json"
        command = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts import verify_workspace as runner
runner.ROOT = Path(sys.argv[2])
runner.WORKSPACE_TESTS = (sys.argv[3],)
raise SystemExit(runner.main(["--json-out", sys.argv[4]]))
"""
        process = subprocess.run(
            [sys.executable, "-c", command, str(ROOT), str(self.root), pattern, str(result_path)],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertTrue(result_path.is_file(), process.stdout + process.stderr)
        return process, json.loads(result_path.read_text())

    def test_success_runs_from_an_unrelated_directory(self):
        process, result = self.run_fixture("""
            import unittest
            class Example(unittest.TestCase):
                def test_runs(self):
                    self.assertEqual(2 + 2, 4)
        """)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["tests_run"], 1)
        self.assertEqual(Path(result["root"]), self.root)
        self.assertIn("test_runs", process.stderr)

    def test_test_failure_and_import_error_both_fail_and_save_results(self):
        for source, field in (("""
            import unittest
            class Example(unittest.TestCase):
                def test_breaks(self):
                    self.fail("fixture failure")
        """, "failures"), ('raise ImportError("fixture import failure")', "errors")):
            with self.subTest(field=field):
                process, result = self.run_fixture(source)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result[field], 1)
                self.assertIn("Traceback", process.stderr)

    def test_empty_or_missing_module_is_not_a_successful_run(self):
        for pattern in ("test_fixture.py", "test_missing.py"):
            with self.subTest(pattern=pattern):
                process, result = self.run_fixture("# No runnable tests\n", pattern)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["tests_run"], 0)
                self.assertIn("no tests discovered", result["discovery_errors"][0])

    def test_skip_keeps_its_reason_and_is_not_reported_as_full_pass(self):
        process, result = self.run_fixture("""
            import unittest
            class Example(unittest.TestCase):
                @unittest.skip("optional fixture dependency absent")
                def test_optional(self):
                    self.fail("must not execute")
        """)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(result["status"], "passed_with_skips")
        self.assertEqual(result["skipped"][0]["reason"], "optional fixture dependency absent")

    def test_unexpected_success_is_a_failure(self):
        process, result = self.run_fixture("""
            import unittest
            class Example(unittest.TestCase):
                @unittest.expectedFailure
                def test_unexpected(self):
                    pass
        """)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["unexpected_successes"], 1)
        self.assertIn("1 unexpected successes", process.stdout)

    def test_both_entrypoints_list_the_same_suite_from_another_directory(self):
        outputs = []
        for script, args in (("scripts/verify_workspace.py", ["--list"]),
                             ("scripts/duck_workspace.py", ["verify", "--list"])):
            process = subprocess.run([sys.executable, str(ROOT / script), *args],
                                     cwd=self.root, capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr)
            outputs.append(process.stdout)
        self.assertEqual(outputs[0], outputs[1])
        self.assertIn("tests/test_experiment_ops.py", outputs[0])
        self.assertIn("tests/test_verification_runner.py", outputs[0])


if __name__ == "__main__":
    unittest.main()
