# Slice Brief 037 - M5 fourth CUDA pilot

**Date:** 2026-09-03

## Objective

Execute exactly one bounded fourth CUDA smoke pilot under committed Manager
authorization 010 and preserve a complete independently verifiable terminal
receipt before exact-ID teardown.

## Authority And Inputs

- Manager authority: `docs/manager-log/010-m5-fourth-pilot-authorization.md`.
- Reviewer-accepted proposal state: `125493c` and Reviewer 036.
- Proposal byte SHA-256:
  `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`.
- All commits, hashes, resource fields, source bundles, image, limits, ordering,
  receipts, teardown, and prohibitions in Manager log 010 are mandatory.

## Execution Gate

- Remove the stop sentinel only for this authorized slice.
- Revalidate the exact proposal and inputs, reproduce/verify source bundles,
  and query fresh inventory/catalog immediately before creation.
- Create exactly `microduck-m5-pilot4-20260904` only if every gate passes.
- Invoke the harness once with the exact 4,800-second timeout. The complete
  suite runs first; any suite failure skips all smoke and export commands.
- Recover and independently verify the complete receipt before exact-ID
  deletion and authenticated empty-inventory confirmation.

## Acceptance Criteria

- One and only one authorized workspace is created, or no workspace is created
  if a pre-create gate fails.
- The terminal receipt is complete, self-checking, and matches an independent
  local sorted manifest exactly.
- Exact-ID deletion and authenticated empty inventory are proven before the
  slice can end.
- Executor commits the immutable receipt and session log, restores the stop
  sentinel, and obtains an independent Reviewer decision.

## Evidence Boundary

At most fourth-pilot CUDA pipeline compatibility. A passing smoke is not M5,
task success, policy acceptance, transfer, or physical authority. A terminal
failure is retained without reclassification.
