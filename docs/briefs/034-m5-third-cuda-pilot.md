# Slice Brief 034 - M5 third CUDA pilot

**Date:** 2026-09-03

## Objective

Execute the newly authorized M5 third CUDA smoke pilot exactly once, recover
and independently verify its complete terminal receipt, delete the exact
non-stoppable workspace, and obtain an independent Reviewer decision.

## Immutable Authority

- Manager authorization: `docs/manager-log/009-m5-third-pilot-authorization.md`,
  committed at `d29c8dc`.
- Reviewer: `docs/reviewer-messages/033-m5-deterministic-evidence-correction.md`.
- Reviewed implementation `d741e60`; contract HEAD `2376821`.
- Proposal SHA-256:
  `5ab9cfa4ddd3015483abcae8d3fc015fbd91a0934691c4f2dc886723d52ee4f9`.
- Harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Runtime SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- Requirements-lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.

## Acceptance Criteria

- Immediately before creation, require clean source state, exact bound hashes,
  authenticated empty inventory, and the exact current `hyperstack_A100_80G`
  catalog row at no more than `$1.62/hour`; abort on drift.
- Create only `microduck-m5-pilot3-20260904` using the immutable linux/amd64
  CUDA image, with no fallback or second workspace.
- Verify copied inputs and launch the exact harness no more than once for one
  receipt ID with an inner timeout no greater than 4,800 seconds.
- Run the complete suite first. Only after it passes, run the four bounded
  64-environment x five-iteration public-development smokes and normalized
  ONNX exports.
- On every outcome, retain terminal status, evidence boundary, identities,
  logs/artifacts, elapsed/cost record, and remote sorted `SHA256SUMS`.
- Recover the complete receipt, independently regenerate an identical local
  manifest, delete the exact workspace, and poll inventory to empty.
- Commit the receipt/log/status and obtain independent review.

## Hard Stops

Two hours create-to-delete, `$3.24`, source/image/catalog drift, hardware or
runtime mismatch, any suite/smoke/export failure, timeout, receipt loss,
checksum mismatch, second workspace, fallback, H100, or multi-GPU. Teardown is
mandatory after every terminal path.

## Evidence Boundary

At most third-pilot CUDA pipeline compatibility. A passed smoke is not M5,
task, policy, candidate, held-out, transfer, or physical success.
