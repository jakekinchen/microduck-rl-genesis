#!/usr/bin/env python3
"""Verify workspace tooling without importing a simulator or installing packages."""
import argparse
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# One list for the local CLI, legacy full suite and workspace CI. Keep simulator,
# training and environment-dependent contract tests in their existing lanes.
WORKSPACE_TESTS = (
    "test_duck_workspace.py",
    "test_behavior_quality_plan.py",
    "test_active_workspace.py",
    "test_workspace_exchange.py",
    "test_experiment_ops.py",
    "test_handoff_snapshots_v43.py",
    "test_compute_preflight.py",
    "test_workspace_performance.py",
    "test_verification_runner.py",
)


def run_tests(directory, patterns, stream):
    suite = unittest.TestSuite()
    discovered = []
    discovery_errors = []
    for pattern in patterns:
        try:
            tests = unittest.TestLoader().discover(str(directory), pattern=pattern)
            count = tests.countTestCases()
            suite.addTests(tests)
        except (ImportError, OSError) as error:
            count = 0
            discovery_errors.append(f"{pattern}: {error}")
        discovered.append({"module": pattern, "tests": count})
        print(f"DISCOVER {pattern}: {count} tests", file=stream, flush=True)
        if count == 0:
            discovery_errors.append(f"{pattern}: no tests discovered")
    if not discovered:
        discovery_errors.append("No test modules selected")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    for error in discovery_errors:
        print(f"DISCOVERY ERROR: {error}", file=stream)
    passed = result.wasSuccessful() and not discovery_errors
    return {
        "status": ("passed_with_skips" if result.skipped else "passed") if passed else "failed",
        "discovered": discovered,
        "discovery_errors": discovery_errors,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
    }


def add_arguments(parser):
    parser.add_argument("--list", action="store_true", help="list selected modules without importing tests")
    parser.add_argument("--json-out", type=Path, help="also save a machine-readable result, including failures and skips")


def verify(args):
    if args.list:
        print("\n".join(f"tests/{name}" for name in WORKSPACE_TESTS))
        return 0
    started = time.monotonic()
    result = run_tests(ROOT / "tests", WORKSPACE_TESTS, sys.stderr)
    result.update(root=str(ROOT), python=sys.executable,
                  elapsed_seconds=round(time.monotonic() - started, 3),
                  scope="workspace tooling only; no simulator, task acceptance or physical validation")
    print(f"Workspace verification: {result['status']}; {result['tests_run']} tests, "
          f"{result['failures']} failures, {result['errors']} errors, {len(result['skipped'])} skipped, "
          f"{result['expected_failures']} expected failures, {result['unexpected_successes']} unexpected successes, "
          f"{len(result['discovery_errors'])} discovery errors")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n")
    return 1 if result["status"] == "failed" else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    return verify(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
