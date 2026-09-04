# Executor log 052 - M6 portable distribution correction

**Date:** 2026-09-04

**Brief:** `docs/briefs/052-m6-portable-distribution-correction.md`

## Reviewer NUDGE Addressed

Reviewer 051 found that slice 051's archive content was exact but its gzip OS
header was interpreter-dependent: Python 3.12 produced byte `0x13`, while
Python 3.9 and 3.13 produced `0xff`. The complete archive digest therefore did
not reproduce across machine-like environments.

The rejected v1 receipt remains byte-for-byte unchanged. The writer now uses
`gzip.GzipFile(filename="", mtime=0, ...)` and refuses output unless its first
ten bytes are exactly `1f8b08000000000002ff`.

## Corrected Receipt

- path: `receipts/m6/distribution/20260904-local-complete-assets-v2/`
- archive: `microduck-complete-assets-v2.tar.gz`
- archive SHA-256:
  `0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9`
- archive size: 9,272,643 bytes
- receipt `SHA256SUMS` SHA-256:
  `9c2a1370e7aba9ad6e46899fdc2ed6cb6935be4bb5af93e86a33ccee71a42790`

The canonical allowlist is unchanged at SHA-256 `8b473f6e...`: 65 complete
files admitted, five missing files quarantined, both ten-role policy manifests
open, and all publication/policy authority absent.

## Multi-Interpreter Regression

The focused test spawns `/usr/bin/python3` 3.9.6, project Python 3.12.12, and
available Python 3.13.11. Each independently regenerates the canonical
allowlist and v2 archive and matches the retained bytes exactly. The focused
suite itself passes under all three interpreters.

## Validation

- Python 3.9/3.12/3.13 focused and subprocess reproduction matrix: pass.
- Corrected receipt, fixed header, legacy receipt preservation, adversarial
  mutations, corrupted archive, and byte-only staging gates: pass.
- Python compilation, v2 receipt checksum, and diff check: pass.
- Full authority-enabled `tests/run_all.py` suite: pass, ending
  `tous les tests passent`.
- Branch hygiene from Reviewer base `68b0094...`: pass with 17 manifests and
  71 immutable logs. Workflow audit and staged/unstaged diff checks: clean.
- Closing `brev ls --json`: `workspaces: null`.
- Isolated exact-Executor-commit clone/staging proof is required after commit
  and is recorded by independent re-review.

## Evidence Boundary

Portable deterministic local packaging and byte-only staging only. No policy
was imported, parsed, loaded, executed, evaluated, approved, activated, or
published. No credential, hardware, remote publication, or compute action
occurred. M6 remains open and M5 remains externally blocked.
