# Slice Brief 038 - M5 fifth-pilot replacement-provider proposal

**Date:** 2026-09-04

## Objective

Freeze and independently review one fail-closed, non-authorizing fifth-pilot
proposal using a different single-A100 provider row after Reviewer 037 accepted
the fourth pilot as a provisioning-health terminal negative.

## Immutable Inputs And Boundaries

- Reviewer-accepted base: `957499a` and Reviewer 037.
- Accepted evaluator correction `4a743bb` and Reviewer/HEAD `7bc61d5`.
- Preserve the accepted fourth-pilot proposal, terminal receipt, and every
  earlier receipt byte-for-byte.
- Do not retry `hyperstack_A100_80G` or reuse consumed Manager authorization
  010.
- `compute_authorized=false` is mandatory and must fail validation if changed.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export,
  candidate, held-out, full CUDA matrix, publication, activation, transfer, or
  physical work.

## Required Proposal

- Use only exact type `massedcompute_A100_sxm4_80G_DGX` if fresh catalog and
  exact-command dry-run evidence support its immutable container mode.
- Bind shadeform/massedcompute, x86_64, one A100 80 GB, 16 vCPUs, 160 GiB RAM,
  non-stoppable, non-rebootable, and exact observed rate `$1.656/hour`.
- Bind a unique workspace, one instance/GPU, no fallback/substitution/second
  workspace, the immutable image, exact harness/runtime/lock/source-bundle
  hashes, and the full accepted Reviewer chain.
- Bind a 4,800-second inner timeout, 7,200 seconds create-to-delete, and exact
  `$3.312` cost ceiling.
- Require the full authority-enabled suite first. Only after it passes may the
  four frozen public-development 64x5 smokes and named normalized ONNX exports
  run.
- Require complete success/failure receipts, remote/local sorted SHA-256
  equality, exact-ID deletion, and authenticated empty inventory.

## Acceptance Criteria

- A machine-readable proposal, schema, semantic validator, and mutation suite
  reject every bound-field/hash/limit/order/authority mutation.
- Focused validators, the full local authority suite, branch hygiene from
  `957499a`, every accepted receipt manifest, and workflow audit pass.
- Executor changes are committed and an independent Reviewer records a
  decision.
- The stop sentinel is restored at the separate Manager authority boundary.

## Hard Stops

Stop with an explicit proposal blocker if the exact DGX row, immutable
container-mode dry run, empty inventory, or any frozen input cannot be proven.
Do not fall back to another type.

## Evidence Boundary

This slice can prove only an exact locally reviewable replacement-provider
proposal. It cannot authorize compute or establish CUDA compatibility, M5,
task/policy success, candidate or held-out evidence, publication, activation,
transfer, or physical authority.
