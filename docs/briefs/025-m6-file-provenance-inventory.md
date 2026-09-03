# Slice Brief 025 - M6 file provenance inventory

**Date:** 2026-09-03

## Objective

Generate and validate a file-level license/provenance inventory for every
repository MJCF, mesh, policy weight, dataset, and distributed media file while
preserving explicit missing and negative results.

## Acceptance Criteria

- Inventory every tracked `.xml` and `.stl` under the MicroDuck asset tree,
  every `policies/*.onnx`, every distributed `demo` GIF/MP4, and the relevant
  license evidence by path, size, SHA-256, class, source, revision, license,
  status, and blocker.
- Compare MJCF/mesh bytes to the exact official walking repository commit
  without importing source code. Record any mismatch rather than normalizing it.
- Record that no dataset files are present; do not invent dataset provenance.
- Keep current policy weights `missing`/unaccepted where checkpoint, run,
  exporter, normalizer, or file-level license provenance is absent.
- Keep media unresolved where production/source/license receipts are absent.
- Validation rejects coverage gaps, digest drift, false completeness, or any
  download/import/evaluation/approval/activation promotion.

## Evidence Boundary

Inventory and negative provenance evidence only. No artifact acceptance,
download, import, evaluation, publication, activation, or physical action.
