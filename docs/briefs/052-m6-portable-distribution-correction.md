# Brief 052 - M6 portable distribution correction

**Date:** 2026-09-04

## Objective

Resolve Reviewer 051's sole anchor-100 NUDGE: preserve the rejected v1 receipt
and emit a versioned archive whose complete bytes reproduce across supported
standard-library Python interpreters, not merely within one interpreter.

## Required Changes

- Use `gzip.GzipFile(filename="", mtime=0, ...)` and require exact gzip header
  `1f8b08000000000002ff` before writing the archive.
- Preserve the v1 receipt and add a v2 receipt bound to Reviewer correction base
  `68b0094...`, the fixed header fields, exact new archive digest, and unchanged
  allowlist/inventory/lifecycle boundaries.
- Build in subprocesses with system Python, project Python, and Python 3.13 when
  available; require exact allowlist and archive byte equality.
- Repeat the fresh isolated exact-commit staging proof during review.

## Acceptance

- Python 3.9, 3.12, and 3.13 reproduce exact v2 archive bytes, size, digest,
  allowlist, and `staged_not_imported` result.
- Rejected v1 bytes and receipt manifest stay unchanged.
- Focused/adversarial/full suites, receipt/hygiene/workflow/diff gates, and
  empty Brev inventory pass; independent Reviewer accepts the correction.

## Stop Conditions

No publication or push and no policy import, parsing, loading, execution,
evaluation, approval, activation, hardware, credentials, or compute action.
Keep five terminal negatives quarantined and both ten-role manifests open.
