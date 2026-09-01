# Slice Brief 001 - M0 readiness baseline

**Date:** 2026-09-01

## Objective

Audit, validate, and commit the inherited Apple lock/setup, contract snapshots,
CI check, actualization plan, README changes, and Genesis 1.3.3 test repairs as
one reviewable readiness baseline without altering their evidence claims.

## Product / Project Value

M0 clean-clone reproduction requires a committed source revision. This slice
turns the intentional dirty readiness work into that exact revision while
preserving its distinction between pipeline evidence and task success.

## Acceptance Criteria

- Every inherited changed/untracked readiness file is inspected and belongs to
  the stated Apple/contract/CI/test-repair scope.
- `scripts/freeze_contract.py --check` passes.
- `tests/run_all.py` passes and every skip is recorded.
- Python sources compile and the Apple lock/setup scripts pass static shell
  checks.
- The implementation is committed with explicit paths; workflow bootstrap files
  and existing generated `logs/` artifacts are excluded from this slice.
- No M0 checkbox that requires clean-clone evidence is promoted.

## Expected Files

- `.gitignore`
- `.github/workflows/contract.yml`
- `README.md`
- `TRAINING_ACTUALIZATION.md`
- `environments/apple/**`
- `microduck_contract/**`
- `scripts/freeze_contract.py`
- `scripts/run_apple_smokes.sh`
- `scripts/setup_apple.sh`
- `tests/test_dr.py`
- `tests/test_external_torque.py`
- `tests/test_onnx_deploy.py`
- `docs/session-logs/001-executor-m0-readiness-baseline.md`

## Test Plan

Use the existing `.venv-apple` only as a validation environment. Re-run the
deterministic contract drift check and full CPU reference/conformance suite;
record optional authoritative-BAM skips instead of disguising them as passes.

## Validation Commands

```bash
.venv-apple/bin/python scripts/freeze_contract.py --check
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
.venv-apple/bin/python -m compileall -q microduck scripts tests train.py play.py export_onnx.py
bash -n scripts/setup_apple.sh scripts/run_apple_smokes.sh
git diff --check
```

## Evidence To Record

- Exact commands and exit status.
- Test counts and skip reasons.
- Explicit staged path list and resulting commit.
- Known limitation: prior local smokes are readiness evidence only and are not
  the M0 clean-clone receipt.

## Reachability / Demo Proof

Show that README Apple commands route through the committed setup/smoke scripts
and that CI routes through the committed contract drift check.

## Cross-Doc Impact

Do not promote `TRAINING_ACTUALIZATION.md`; add only a bounded readiness receipt
note if validation materially differs from its current statement.

## Out Of Scope

- Running the second clean clone.
- Creating authoritative BAM vectors.
- Any longer training, held-out success claim, publication, policy activation,
  cloud provisioning, or physical test.

## Stop Conditions

- Any inherited change falls outside the stated readiness scope.
- The full suite fails for a reason not safely fixable within the three stale
  Genesis 1.2 test repairs already present.
- Validation would require downloading or changing dependencies.
