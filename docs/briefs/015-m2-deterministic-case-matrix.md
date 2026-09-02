# Slice Brief 015 - M2 deterministic case matrix

**Date:** 2026-09-02

## Objective

Implement the complete visible, synthetic-policy evaluator matrix for standing,
command grid, start/stop/reversal, perturbation, friction, joint margin, NaN,
deadline, and termination behavior.

## Acceptance Criteria

- Freeze every case ID, seed, inputs, expected evaluator outcome, and evidence
  boundary before candidate inspection.
- Exercise real evaluator paths for state initialization, command schedules,
  external perturbation, friction changes, joint-limit margins, non-finite
  rejection, deadline classification, and deterministic termination.
- Keep the retained zero-output synthetic policy and `task_success:
  not_evaluated`; no official or Genesis candidate may be used.
- Reports from two same-host runs must be byte-identical after excluding no
  fields; measured wall-clock latency must not define a deterministic expected
  result.
- Add focused negative tests for malformed case expectations.

## Validation

```bash
BAM_REPO=/tmp/microduck-bam-authority-exact \
  .venv-apple/bin/python tests/test_evaluator_case_matrix.py
.venv-apple/bin/python scripts/freeze_contract.py --check
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

This is evaluator infrastructure with a synthetic zero policy. It does not
evaluate walking/backflip success, a held-out acceptance suite, backend
superiority, transfer, or physical authority.
