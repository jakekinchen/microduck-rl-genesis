# Reviewer Message 025 - M6 file provenance inventory

**Date:** 2026-09-03

## Decision

`ESCALATE`

## Evidence Reviewed

- Commit `e91ac2e` adds the deterministic 70-file inventory, generator,
  validator, negative probes, and Executor log.
- All 63 MJCF/STL files are compared byte-for-byte with exact official commit
  `109e06d` without importing source code. Sixty-two match; `ball.xml` does not.
- The inventory reports 63 complete, 2 partial, and 5 missing entries. Three
  ONNX policies and two demo media files remain missing/unaccepted.
- Dataset scope is empty and explicitly makes no invented provenance claim.
- The full local suite passes; generation plus `--check` is byte-identical and
  exact external source comparison passes.

## Findings

The independent M6 foundations requested in the current authority envelope are
complete: schemas, synthetic byte-only validation, complete-role modeling,
lifecycle separation, and a file-level inventory with honest negatives.

No real official/community artifact can yet satisfy policy manifest v2. The
existing weights lack checkpoint/run/exporter/normalizer/file-license bindings;
media lacks production/source/license receipts; `ball.xml` has unresolved
transformation provenance; the actuator parameter lacks an exact upstream path
and blob binding.

## Evidence Anchors

- `100` - `official_policy_authority_missing` blocks M5 official repeatability
  and final candidate admission.
- `100` - immutable CUDA container digest and explicit paid-compute authority
  are absent; no Brev workspace may be created.
- `100` - real policy manifests cannot be accepted from the currently missing
  provenance listed above.
- `75` - `ball.xml` and actuator-source provenance are actionable upstream/file
  reconciliation work but do not authorize substitution.
- `100` - publication, activation, and hardware remain explicitly unauthorized.

## Milestone State

M5 contract/preflight and independent M6 foundations are accepted. M5 execution
and real M6 artifact acceptance remain blocked at external authority boundaries.
No further safe local slice can close those gates from existing bytes alone.
