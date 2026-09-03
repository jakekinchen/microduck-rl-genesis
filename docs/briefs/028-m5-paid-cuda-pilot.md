# Slice Brief 028 - M5 paid CUDA pilot

**Date:** 2026-09-03

## Objective

Execute the independently authorized one-workspace CUDA pilot, recover and
independently verify every required artifact, delete the non-stoppable resource,
and obtain a separate Reviewer decision before any full-run eligibility.

## Acceptance Criteria

- Recheck authenticated empty inventory and the exact A100 row immediately
  before creation; abort on any type, GPU count, architecture, stoppability,
  price, or provider/cloud drift.
- Create exactly one container-mode workspace with the immutable linux/amd64
  image reference and no fallback.
- Materialize the frozen Genesis, official walking, official backflip, and BAM
  source identities; record hardware/runtime versions.
- Run the full applicable suite with BAM and official mjlab authority supplied.
- Run Genesis CUDA and official mjlab CUDA walking/backflip smokes at 64
  environments x 5 iterations using public development seeds only.
- Retain configs, checkpoints, normalized ONNX exports, logs, source identities,
  elapsed time, exact price/cost accounting, manifest, and remote `SHA256SUMS`.
- Recover the complete receipt locally; regenerate a local sorted checksum list
  and require exact equality before deletion.
- Delete the non-stoppable workspace and poll authenticated inventory to empty.
- Commit the receipt and Executor log, then obtain an independent Reviewer
  decision. Do not begin full CUDA candidate work in this slice.

## Stop Conditions

Stop and preserve a terminal receipt on two elapsed hours/$3.24, any second
workspace, catalog/image/source drift, GPU/runtime failure, missing artifact,
checksum mismatch, or unrecoverable remote state. Cleanup remains mandatory.

## Evidence Boundary

CUDA pipeline pilot evidence only. A successful smoke is not task success,
candidate admission, held-out evaluation, official-policy acceptance,
publication, activation, transfer, or physical authority.
