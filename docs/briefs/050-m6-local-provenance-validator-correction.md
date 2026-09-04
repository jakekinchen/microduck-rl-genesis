# Brief 050 - M6 local provenance validator correction

**Date:** 2026-09-04

## Objective

Resolve Reviewer 049's anchor-75 NUDGE without changing the substantiated
archaeology result. Preserve the rejected v1 receipt, emit a versioned v2
receipt with stable history scope, and make every material license, media, and
remote claim fail closed after manifest recomputation.

## Required Changes

- Replace transient all-ref counting with exact ancestry of accepted commit
  `321f0a9396b7596e62a0834d79c167a9fe8ce32a`.
- Bind the exact upstream license-introduction commit/tree/parent/README blob
  and digest, license scope, contemporaneous ball blob, and ancestry ordering.
- Bind exact media digests and every non-authoritative metadata field.
- Bind every public repository, branch/head, root-only target-history result,
  separate-policy path/SHA/disposition, and positive-control statement.
- Require exact evidence-map coverage and add mutation probes for each prior
  blind spot.

## Acceptance

- All Reviewer 049 mutations fail after their manifest entries are recomputed.
- Exact root/source/license/later-change relations reproduce from Git objects.
- Inventory remains 65 complete / 0 partial / 5 missing and unaccepted until
  independent re-review.
- Focused/full suites, receipt manifests, branch hygiene, workflow/diff gates,
  and empty Brev inventory pass.

## Stop Conditions

No target policy download, parsing, loading, execution, evaluation, training,
publication, activation, credentials, hardware action, or compute provisioning.
Do not promote the five missing files or M6.
