"""Portable metadata must never become an execution or acceptance grant."""
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from duck_workspace.core import ROOT
from duck_workspace.exchange import SCHEMA_PATH, SOURCES, check_conformance, export_workspace, load_packet, validate

FIXTURES = ROOT / "docs/workspace/exchange/fixtures"


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.packet = load_packet(FIXTURES / "microduck.source-snapshot.json")

    def test_native_snapshot_is_portable_metadata(self):
        result = validate(self.packet)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["source_verification"], "not_requested")
        self.assertFalse(result["native_gate_checked"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["policy_portability"], "not_established")

    def test_accepted_v1_contract_and_shared_fixture_bytes_are_frozen(self):
        self.assertEqual(hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(),
                         "7f6115335dac03c0493940ed9f63d1aba0c741ba55defd434b5208acedf52bf0")
        self.assertEqual(hashlib.sha256(SCHEMA_PATH.with_name("workspace_adapter.v1.fixtures.json").read_bytes()).hexdigest(),
                         "7ea788e0ddce6ce77a99ae18fb1c87589ec5437806ed68ed6d2b8efde0f6eaa4")

    def test_shared_negative_fixtures(self):
        for mutation in load_packet(FIXTURES / "negative-cases.json"):
            with self.subTest(mutation["id"]):
                packet = deepcopy(self.packet)
                target = packet
                for key in mutation["path"][:-1]:
                    target = target[key]
                target[mutation["path"][-1]] = mutation["value"]
                self.assertFalse(validate(packet)["valid"])

    def test_shared_cross_project_fixtures_without_any_subprocess(self):
        with patch("subprocess.run", side_effect=AssertionError("fixture executed a process")):
            result = check_conformance()
        self.assertTrue(result["passed"], result)
        self.assertEqual(len(result["cases"]), 30)
        for case in result["cases"]:
            self.assertFalse(case["execution_authorized"])
            self.assertFalse(case["policy_portable"])

    def test_duplicate_ids_and_names(self):
        for group in ("sources", "profiles", "capabilities"):
            with self.subTest(group):
                packet = deepcopy(self.packet)
                packet[group].append(deepcopy(packet[group][0]))
                self.assertFalse(validate(packet)["valid"])
        self.packet["profiles"][0]["action"]["ordered_names"][1] = self.packet["profiles"][0]["action"]["ordered_names"][0]
        self.assertFalse(validate(self.packet)["valid"])

    def test_paths_must_be_portable_and_canonical(self):
        for path in ("C:\\source", "file:///source", "a/./b", "a//b", "a/../b", "a\nb", "a/"):
            with self.subTest(path):
                self.packet["sources"][0]["path"] = path
                self.assertFalse(validate(self.packet)["valid"])

    def test_malformed_objects_do_not_crash_or_grant_authority(self):
        for packet in (None, [], {"schema_version": 42}, {**self.packet, "profiles": None}):
            self.assertFalse(validate(packet)["valid"])
        self.packet["profiles"][0]["timing"]["control_hz"] = float("nan")
        self.assertFalse(validate(self.packet)["valid"])
        self.packet["profiles"][0]["action"]["dimension"] = 10 ** 1000
        self.assertFalse(validate(self.packet)["valid"])

    def test_duplicate_keys_and_nonfinite_json_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e9999}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load_packet(path)

    def test_oversized_packet_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b" " * (2 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                load_packet(path)

    def test_fifo_directory_and_symlink_packets_refused_without_open(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "input.json"
            os.mkfifo(fifo)
            link = Path(directory) / "linked.json"
            link.symlink_to(FIXTURES / "microduck.source-snapshot.json")
            for path in (fifo, Path(directory), link):
                with self.subTest(path=path), patch("os.open", side_effect=AssertionError("opened special input")):
                    with self.assertRaises(ValueError):
                        load_packet(path)

    def test_file_changed_during_read_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"value":1}')
            original = os.fstat
            calls = 0
            def changed(descriptor):
                nonlocal calls
                calls += 1
                if calls == 2:
                    path.write_text('{"value":200}')
                return original(descriptor)
            with patch("os.fstat", side_effect=changed):
                with self.assertRaisesRegex(ValueError, "changed while reading"):
                    load_packet(path)

    def test_invalid_packet_never_reads_declared_source_root(self):
        self.packet["sources"][0]["path"] = "../outside"
        result = validate(self.packet, Path("/does-not-exist"))
        self.assertEqual(result["source_verification"], "not_attempted_invalid_packet")

    def test_unknown_native_metadata_is_never_portability(self):
        self.packet["profiles"][0]["native_schema"] = "unknown.robot/v99"
        self.packet["profiles"][0]["action"]["units"] = ["unknown-unit"] * 14
        result = validate(self.packet)
        self.assertTrue(result["valid"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["policy_portability"], "not_established")


class SourceBoundTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for _, relative, _ in SOURCES:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        self.packet = export_workspace("fixture-task", self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_current_sources_verify_without_importing_simulation(self):
        result = validate(self.packet, self.root)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["source_verification"], "verified")
        self.assertEqual(self.packet["native_gate"]["status"], "source_only")
        for module in ("genesis", "torch", "mujoco", "microduck.velocity_env"):
            self.assertNotIn(module, sys.modules)

    def test_changed_and_missing_sources_fail(self):
        (self.root / "AGENTS.md").write_text("changed")
        self.assertFalse(validate(self.packet, self.root)["valid"])
        (self.root / "AGENTS.md").unlink()
        self.assertFalse(validate(self.packet, self.root)["valid"])

    def test_matching_symlink_bytes_are_still_refused(self):
        path = self.root / "AGENTS.md"
        path.unlink()
        path.symlink_to(ROOT / "AGENTS.md")
        result = validate(self.packet, self.root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("symlink" in error for error in result["errors"]))

    def test_branch_and_head_identity_are_checked(self):
        self.git("checkout", "-qb", "changed-branch")
        self.assertFalse(validate(self.packet, self.root)["valid"])
        self.packet["workspace"]["repository"]["branch"] = "changed-branch"
        self.packet["workspace"]["repository"]["head"] = "0" * 40
        self.assertFalse(validate(self.packet, self.root)["valid"])

    def test_native_abi_drift_and_malformed_layout_refuse_export(self):
        action_path = self.root / "microduck_contract/interface/action-v1.json"
        original = action_path.read_bytes()
        action = json.loads(original)
        action["shape"] = [1, 6]
        action_path.write_text(json.dumps(action))
        with self.assertRaises(ValueError):
            export_workspace("fixture-task", self.root)
        action_path.write_bytes(original)
        obs = self.root / "microduck_contract/interface/observation-v1.json"
        observation = json.loads(obs.read_bytes())
        observation["layout"] = None
        obs.write_text(json.dumps(observation))
        with self.assertRaises(ValueError):
            export_workspace("fixture-task", self.root)


if __name__ == "__main__":
    unittest.main()
