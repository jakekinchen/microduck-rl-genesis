# Slice Brief 031 - M5 second CUDA pilot

**Date:** 2026-09-03

## Objective

Execute the newly authorized, independently reviewed second M5 CUDA smoke
pilot, recover and independently verify its complete receipt, delete the exact
non-stoppable workspace, and obtain an independent Reviewer decision.

## Immutable Authority

- Manager authorization: `docs/manager-log/007-m5-second-pilot-authorization.md`.
- Reviewer: `docs/reviewer-messages/030-m5-cu128-install-source-correction.md`.
- Proposal: `experiments/m5/second-pilot-proposal-v1.json`, SHA-256
  `f020df3f1cfb29b160ec86765a06e184a696af940fe62d690fda371653aa536e`.
- Reviewed runtime source commit: `764d923` with implementation `ba319ee`.

## Acceptance Criteria

- Recheck empty authenticated inventory and the exact current catalog row
  immediately before creation; abort on any frozen attribute or price drift.
- Create exactly one `microduck-m5-pilot2-20260903` container workspace using
  `hyperstack_A100_80G` and the immutable linux/amd64 CUDA digest.
- Verify source bundles and run the exact reviewed harness with an inner timeout
  no greater than 4,800 seconds.
- Run the full applicable suite before four 64-environment x five-iteration
  public-development smokes and their normalized ONNX exports.
- On success or failure, retain terminal status, evidence boundary, runtime
  identities, logs/artifacts produced, elapsed/cost record, and remote sorted
  `SHA256SUMS`.
- Recover the complete receipt, independently regenerate an identical local
  manifest, delete the exact workspace, and poll inventory to empty.
- Commit the receipt/log and obtain independent review. Do not begin candidate,
  held-out, full-matrix, publication, activation, transfer, or physical work.

## Hard Stops

Two hours create-to-delete, `$3.24`, any second workspace, fallback/substitute
resource, source/image/hash drift, runtime or suite failure, timeout, receipt
loss, or checksum mismatch. Teardown remains mandatory after any terminal path.

## Evidence Boundary

Second-pilot CUDA pipeline compatibility only. Smoke output is not task success,
candidate admission, held-out evaluation, policy acceptance, transfer, or
physical authority.
