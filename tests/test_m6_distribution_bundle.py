"""Verify provenance-gated M6 distribution and fail-closed mutations."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from artifact_contract.distribution import (
    build_bundle,
    validate_allowlist,
    validate_bundle,
    validate_legacy_receipt,
    validate_receipt,
)

ALLOWLIST = ROOT / "artifact_contract/distribution-allowlist-v1.json"
BUNDLE = ROOT / "receipts/m6/distribution/20260904-local-complete-assets-v2/microduck-complete-assets-v2.tar.gz"
RECEIPT = BUNDLE.parent
LEGACY_RECEIPT = ROOT / "receipts/m6/distribution/20260904-local-complete-assets-v1"
value = json.loads(ALLOWLIST.read_text())
validate_allowlist(ROOT, value)
result = validate_bundle(ROOT, ALLOWLIST, BUNDLE)
validate_receipt(RECEIPT, ROOT, ALLOWLIST)
validate_legacy_receipt(LEGACY_RECEIPT, ROOT, ALLOWLIST)
assert hashlib.sha256((LEGACY_RECEIPT / "SHA256SUMS").read_bytes()).hexdigest() == "7c09028cf77754f7b7ea7d8793daa640c872e5ea892e8ca03eaaddc4bcf821c2"
assert BUNDLE.read_bytes()[:10].hex() == "1f8b08000000000002ff"
assert result["allowlisted_file_count"] == 65
assert result["quarantined_file_count"] == 5
assert result["lifecycle"]["library_stage"] == "not_requested"
assert {item["path"] for item in value["quarantined_files"]} == {
    "demo/apercu.gif",
    "demo/microduck-parcours-30s.mp4",
    "policies/backlash.onnx",
    "policies/rough.onnx",
    "policies/velocity.onnx",
}
assert value["policy_manifest_requirements"]["official"]["status"] == "open_no_complete_policy_manifest"
assert value["policy_manifest_requirements"]["community"]["status"] == "open_no_complete_policy_manifest"


def rejected(mutator) -> None:
    candidate = copy.deepcopy(value)
    mutator(candidate)
    try:
        validate_allowlist(ROOT, candidate)
    except AssertionError:
        return
    raise AssertionError("invalid distribution allowlist mutation accepted")


def receipt_rejected(mutator) -> None:
    with tempfile.TemporaryDirectory(prefix="microduck-distribution-receipt-mutation-") as temp:
        copied = Path(temp) / "receipt"
        shutil.copytree(RECEIPT, copied)
        result_path = copied / "SEARCH_RESULT.json"
        candidate = json.loads(result_path.read_text())
        mutator(candidate)
        result_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
        lines = (copied / "SHA256SUMS").read_text().splitlines()
        digest = hashlib.sha256(result_path.read_bytes()).hexdigest()
        (copied / "SHA256SUMS").write_text("\n".join(
            f"{digest}  ./SEARCH_RESULT.json" if line.endswith("./SEARCH_RESULT.json") else line
            for line in lines
        ) + "\n")
        try:
            validate_receipt(copied, ROOT, ALLOWLIST)
        except AssertionError:
            return
        raise AssertionError("rehashed invalid distribution receipt mutation accepted")


rejected(lambda item: item["allowlisted_files"].append(item["quarantined_files"][0]))
rejected(lambda item: item["quarantined_files"].pop())
rejected(lambda item: item["allowlisted_files"][0].__setitem__("sha256", "sha256:" + "0" * 64))
rejected(lambda item: item["allowlisted_files"][0].__setitem__("declared_license", "unresolved"))
rejected(lambda item: item["allowlisted_files"][0]["source"].__setitem__("revision", "0" * 40))
rejected(lambda item: item["lifecycle"].__setitem__("library_import", "completed"))
rejected(lambda item: item["lifecycle"].__setitem__("publication", "completed"))
rejected(lambda item: item["authority"].__setitem__("policy_activation", "authorized"))
rejected(lambda item: item["policy_manifest_requirements"]["official"].__setitem__("status", "complete"))
rejected(lambda item: item["policy_manifest_requirements"]["community"]["required_roles"].pop())
receipt_rejected(lambda item: item["verification"].__setitem__("library_stage", "imported"))
receipt_rejected(lambda item: item["actions"].__setitem__("policy_executed", True))
receipt_rejected(lambda item: item["inventory"].__setitem__("quarantined_missing", 0))
receipt_rejected(lambda item: item["deterministic_encoding"].__setitem__("gzip_os_byte", 19))

with tempfile.TemporaryDirectory(prefix="microduck-distribution-test-") as temp:
    temp_root = Path(temp)
    first = temp_root / "first.tar.gz"
    second = temp_root / "second.tar.gz"
    assert build_bundle(ROOT, ALLOWLIST, first) == build_bundle(ROOT, ALLOWLIST, second)
    assert first.read_bytes() == second.read_bytes() == BUNDLE.read_bytes()
    interpreters = [Path("/usr/bin/python3"), Path(sys.executable)]
    python313 = shutil.which("python3.13")
    if python313:
        interpreters.append(Path(python313))
    seen: set[Path] = set()
    for index, interpreter in enumerate(interpreters):
        resolved = interpreter.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        generated_allowlist = temp_root / f"allowlist-{index}.json"
        generated_bundle = temp_root / f"bundle-{index}.tar.gz"
        subprocess.run([
            str(interpreter), str(ROOT / "scripts/build_m6_distribution_bundle.py"),
            "--root", str(ROOT), "--generate",
            "--allowlist", str(generated_allowlist), "--bundle", str(generated_bundle),
        ], check=True, capture_output=True)
        assert generated_allowlist.read_bytes() == ALLOWLIST.read_bytes()
        assert generated_bundle.read_bytes() == BUNDLE.read_bytes()
    stage = temp_root / "library-stage"
    staged = validate_bundle(ROOT, ALLOWLIST, BUNDLE, stage)
    assert staged["lifecycle"]["library_stage"] == "staged_not_imported"
    assert not (stage / "policies").exists()
    assert not (stage / "demo").exists()
    assert json.loads((stage / "LIBRARY-STAGE.json").read_text())["lifecycle"]["library_import"] == "not_performed"

    corrupted = temp_root / "corrupted.tar.gz"
    shutil.copyfile(BUNDLE, corrupted)
    data = bytearray(corrupted.read_bytes())
    data[len(data) // 2] ^= 1
    corrupted.write_bytes(data)
    try:
        validate_bundle(ROOT, ALLOWLIST, corrupted)
    except (AssertionError, tarfile.TarError, EOFError):
        pass
    else:
        raise AssertionError("corrupted bundle accepted")

print("M6 provenance-gated deterministic distribution bundle verified")
