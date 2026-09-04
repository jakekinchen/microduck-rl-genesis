# Slice Brief 039 - M5 fifth-pilot cost-binding correction

**Date:** 2026-09-04

## Objective

Resolve Reviewer 038's NUDGE entirely locally by binding the replacement
provider's exact `$1.656/hour` rate into a fifth-specific pilot harness and by
removing stale fourth-pilot limits from current authority text. Refreeze and
independently review the non-authorizing proposal without provisioning Brev or
running training.

## Immutable Inputs And Boundaries

- Preserve `scripts/run_m5_cuda_pilot.sh` byte-for-byte as the accepted
  fourth-pilot harness.
- Preserve every accepted receipt and the accepted chain through Reviewer 037.
- Preserve the exact replacement resource, immutable image, runtime lock,
  source commits, deterministic source bundles, execution order, seeds,
  receipt requirements, teardown requirements, and prohibitions in proposal
  038.
- `compute_authorized=false` remains mandatory.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export,
  candidate, held-out, full CUDA matrix, publication, activation, transfer, or
  physical work.

## Required Correction

- Add a fifth-specific harness whose receipt cost calculation uses exactly
  `PRICE_USD_PER_HOUR=1.656`; do not modify the fourth-pilot harness.
- Bind the new harness path and SHA-256 in the fifth-pilot proposal.
- Require the semantic validator to extract the harness price and prove exact
  equality with both catalog and limit rates.
- Add a direct negative regression that an embedded `$1.62/hour` harness rate
  is rejected.
- Mark the `$1.62/hour` hyperstack preference and `$3.24` ceiling in
  `GOAL.md` as historical, forbid retry, and state the proposed exact
  `massedcompute_A100_sxm4_80G_DGX` type with `$1.656/hour` / `$3.312` limits.

## Acceptance Criteria

- The corrected proposal, new harness, validator, and test bindings are frozen
  by exact hashes and pass focused mutation checks.
- The original fourth-pilot harness and all accepted receipts are unchanged.
- The full authority-enabled local suite, static CUDA and artifact checks,
  Python compilation, all tracked manifests and immutable logs, branch hygiene,
  diff checks, workflow audit, and closing authenticated empty Brev inventory
  pass.
- Executor changes are committed and an independent Reviewer records a final
  decision.
- The stop sentinel is restored at the Manager authority boundary.

## Evidence Boundary

This correction can prove only that the non-authorizing fifth-pilot proposal is
internally cost-consistent and locally reproducible. It cannot authorize paid
compute or prove CUDA smoke, M5, task, policy, candidate, held-out,
publication, activation, transfer, or physical success.
