# Executor Session Log 001 - M0 readiness baseline

**Date:** 2026-09-01

## Slice

Audited and validated the inherited Apple dependency lane, contract snapshots,
contract-drift CI, actualization plan, README changes, and Genesis 1.3.3 test
repairs described by `docs/briefs/001-m0-readiness-baseline.md`.

## Files Changed

- `.gitignore`
- `.github/workflows/contract.yml`
- `README.md`
- `TRAINING_ACTUALIZATION.md`
- `environments/apple/README.md`
- `environments/apple/requirements.in`
- `environments/apple/requirements.lock`
- `microduck_contract/**`
- `scripts/freeze_contract.py`
- `scripts/run_apple_smokes.sh`
- `scripts/setup_apple.sh`
- `tests/test_dr.py`
- `tests/test_external_torque.py`
- `tests/test_onnx_deploy.py`
- `docs/session-logs/001-executor-m0-readiness-baseline.md`

## Implementation Note

The first contract drift check failed because `compileall` had created
`microduck/assets/microduck/__pycache__/add_backlash.cpython-312.pyc` and the
candidate asset bundle hashed every file under the asset root. The freezer now
excludes Python bytecode and `__pycache__`; CI compiles before checking the
snapshots so command order cannot silently reintroduce this defect. Regenerated
model locks contain no cache path and retain the source-only asset digests.

## Validation

All final commands exited 0:

```text
.venv-apple/bin/python -m compileall -q microduck scripts tests train.py play.py export_onnx.py
.venv-apple/bin/python scripts/freeze_contract.py --check
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
bash -n scripts/setup_apple.sh scripts/run_apple_smokes.sh
git diff --check
scripts/audit_autonomous_workflow.sh
```

`tests/run_all.py` ended with `tous les tests passent`. It recorded these
non-passing coverage classes explicitly:

- BAM formula comparison skipped because the optional authoritative BAM
  checkout was absent.
- Full MuJoCo+BAM actuator-loop comparison skipped for the same reason.
- Default `logs/microduck-velocity` ONNX deployment comparison was not
  applicable because that checkpoint directory was absent.

The external-torque comparison had maximum error `3.115e-08 N.m`; observation
and action checks retained 61 dimensions and 14 actions. These are conformance
and pipeline results, not task-success or physical evidence.

## Reachability

- The README Apple quick start invokes `scripts/setup_apple.sh` and
  `scripts/run_apple_smokes.sh`.
- The setup script syncs the committed hash lock and fails closed unless Torch
  MPS and Genesis Metal are visible.
- The GitHub workflow compiles sources, then runs the same deterministic
  contract drift check used locally.

## Known Limitations

- Prior working-tree smoke artifacts are readiness evidence only; they are not
  the required second-clean-checkout M0 receipt.
- M0 remains open until the committed revision is reproduced from a clean Apple
  checkout with retained stdout, configs, checkpoints, exports, metadata, and a
  SHA-256 manifest.
- Authoritative BAM and official mjlab conformance remain M1 work.

## Suggested Next Slice

Create an isolated clean checkout at this readiness commit, run the full M0
verification gate, and retain the versioned receipt bundle under
`receipts/apple-baseline/<run-id>/`.
