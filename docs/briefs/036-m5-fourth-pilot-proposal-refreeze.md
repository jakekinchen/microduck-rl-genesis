# Slice Brief 036 - M5 fourth-pilot proposal refreeze

**Date:** 2026-09-03

## Objective

Draft and independently validate one fail-closed, non-authorizing fourth-pilot
proposal after Reviewer 035 accepted the local evaluator-bundle correction.
Freeze every input and operating limit needed for a later Manager decision
without creating a Brev workspace or running training.

## Immutable Inputs And Boundaries

- Accepted evaluator-bundle correction: `4a743bb`.
- Reviewer-accepted repository HEAD: `7bc61d5` and Reviewer 035.
- Preserve every accepted receipt byte-for-byte.
- Preserve the exact pilot harness, CUDA runtime, requirements lock, immutable
  linux/amd64 image digest, source commits, and deterministic source-bundle
  hashes.
- `compute_authorized=false` is mandatory and must fail validation if changed.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export,
  candidate, held-out, full CUDA matrix, publication, activation, transfer, or
  physical work.

## Required Proposal

- Bind the unique proposed workspace `microduck-m5-pilot4-20260904` to exactly
  one `hyperstack_A100_80G`: shadeform/hyperstack, x86_64, one A100 80 GB,
  non-stoppable and non-rebootable, with no fallback or second workspace.
- Bind the immutable CUDA image, exact current harness/runtime/lock/source
  bundle hashes, the accepted correction, and Reviewer/HEAD.
- Require the complete authority-enabled suite first. Only after it passes may
  the four frozen public-development 64-environment x five-iteration smokes
  run, followed by retention of normalized ONNX exports.
- Bind a 4,800-second inner timeout and hard create-to-delete ceilings of two
  hours and `$3.24` at no more than `$1.62/hour`.
- Require terminal failure receipts, remote sorted `SHA256SUMS`, complete local
  recovery, an independently regenerated local manifest with exact equality,
  exact-ID teardown, and authenticated empty inventory.
- Require a fresh matching catalog and empty inventory immediately before any
  later authorized creation. This slice's catalog query is proposal evidence
  only.

## Acceptance Criteria

- A machine-readable proposal and dedicated semantic validator reject every
  mutated bound field, hash, limit, workflow order, authority state, and
  prohibition.
- Deterministic source-bundle generation is repeated locally and produces
  byte-identical verified bundles for the three exact source refs.
- Focused proposal tests and validators, the full authority-enabled local
  suite, branch hygiene from `7bc61d5`, all immutable receipt manifests, M5
  contract checks, and the workflow audit pass.
- Executor changes are committed and an independent Reviewer records a
  decision.
- The stop sentinel is restored at the Manager authority boundary.

## Hard Stops

Stop before provisioning or training. Stop on accepted-receipt mutation,
source or authority drift, an unmatched catalog row, a non-empty Brev
inventory, or any proposal state other than non-authorizing.

## Evidence Boundary

This slice can prove only that a precise fourth-pilot proposal is locally
reproducible and reviewable. It cannot authorize compute or establish CUDA
smoke success, M5 completion, task or policy success, candidate admission,
held-out evidence, publication, activation, transfer, or physical authority.
