# M5 third-pilot proposal card

**Date:** 2026-09-03

**State:** `draft_pending_independent_review`

**compute_authorized:** `false`

## Basis

Implementation `bac0375` plus the Reviewer-032 scope correction `d741e60` is
the local-only correction candidate for the three deterministic evidence
failures closed by slice 032. It requires independent Reviewer acceptance before
it can become eligible for a later exact Manager authorization. This card
itself grants no provisioning or execution authority.

## Proposed Purpose

If separately reviewed and later authorized, run one no-fallback Linux/amd64
A100 smoke pilot whose first gate is the complete authority-enabled suite. Only
after that suite passes may the previously bounded four public-development
64-environment x five-iteration smokes and normalized ONNX exports run.

## Proposed Boundaries

- Exactly one named workspace and one exact catalog type selected by a fresh
  price/availability query; no fallback, H100, multi-GPU, or second workspace.
- A later Manager record must bind the exact reviewed implementation, harness,
  runtime, lock, resource type, immutable image digest, name, time ceiling, and
  cost ceiling before creation.
- Candidate comparison, held-out realization, full CUDA matrix, publication,
  activation, transfer, and physical work remain prohibited.
- Abort on source/hash/runtime drift, any suite failure, receipt loss, timeout,
  overspend, or second-workspace requirement.
- Always recover and independently verify a complete terminal receipt before
  deleting the exact non-stoppable workspace and confirming authenticated empty
  inventory.

## Current Decision

No paid action is permitted. A future Reviewer may accept or reject the local
correction, but only a subsequent explicit Manager authorization can change
`compute_authorized=false` for one exact pilot.
