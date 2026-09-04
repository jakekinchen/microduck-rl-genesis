"""Ensure immutable receipt hygiene is generic and manifest-bound."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_M5_MANIFEST = "1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b"

attributes = (ROOT / ".gitattributes").read_text()
assert "receipts/**/*.log whitespace=-trailing-space,-space-before-tab" in attributes
assert "receipts/apple-baseline/**/*.log" not in attributes

script = (ROOT / "scripts/check_branch_hygiene.sh").read_text()
assert "git ls-files 'receipts/**/SHA256SUMS'" in script
assert "git ls-files 'receipts/**/*.log'" in script
assert "receipts/apple-baseline" not in script

manifest = ROOT / "receipts/m5/pilot/20260903T2334Z-tudexszf6/SHA256SUMS"
assert hashlib.sha256(manifest.read_bytes()).hexdigest() == EXPECTED_M5_MANIFEST

result = subprocess.run(
    [str(ROOT / "scripts/check_branch_hygiene.sh"), "0a0c2c9"],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
assert result.returncode == 0, result.stdout + result.stderr
assert "manifests=6" in result.stdout
assert "immutable_logs=38" in result.stdout

print("generic manifest-bound receipt hygiene verified")
