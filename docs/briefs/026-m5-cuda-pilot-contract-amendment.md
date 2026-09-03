# Slice Brief 026 - M5 CUDA pilot contract amendment

**Date:** 2026-09-03

## Objective

Amend the accepted M5 experiment contract for exactly one bounded A100 pilot by
binding an immutable linux/amd64 CUDA image, the dated Manager authorization,
and fail-closed resource, cost, recovery, and teardown rules without authorizing
candidate or held-out execution.

## Acceptance Criteria

- Bind the exact CUDA image repository, human-readable tag, linux/amd64 manifest
  digest, and a reproducible registry-inspection command.
- Encode one preferred `hyperstack_A100_80G` workspace at the rechecked
  $1.62/hour envelope, two-hour/$3.24 pilot ceiling, and the conditional
  104-GPU-hour/$210 full ceiling.
- Make clear that the full CUDA matrix is not executable until an independent
  Reviewer accepts the pilot, and that official-policy provenance plus
  candidate freeze still gate candidate admission.
- Freeze exact pilot contents: hardware/CUDA/Warp/MuJoCo checks, the applicable
  test suite, and walking/backflip 64-env x 5-iteration smokes with configs,
  checkpoints, normalized exports, logs, manifests, independent checksums, and
  exact elapsed/cost accounting.
- Freeze artifact recovery and non-stoppable workspace deletion semantics.
- Update schema, validator, matrix authority fields, and lock hashes; add tests
  proving image, resource, cost, candidate, held-out, and teardown drift fail
  closed.
- Obtain an independent Reviewer `GO` decision before any paid workspace is
  created.

## Evidence Boundary

This slice establishes pilot execution authority and immutable infrastructure
only. It does not execute a paid resource, admit a candidate, realize held-out
inputs, establish official-policy provenance, prove task success, publish or
activate a policy, or authorize physical operation.
