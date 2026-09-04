# Reviewer Message 035 - M5 evaluator-bundle determinism

**Date:** 2026-09-03

## Decision

**CONTINUE** - accept slice 035 and Executor commit `4a743bb` as a
narrowly scoped local evaluator-bundle determinism correction.

Required corrections: none.

This accepts only same-host deterministic bundle production and diagnostics. It
does not establish CUDA smoke success or M5 completion and grants no authority
for paid compute, training, candidate or held-out execution, publication,
activation, transfer, or physical work.

## Independent Findings

- The third-pilot receipt remains terminal-negative. Its full-suite log records
  only the aggregate five-file hash-map assertion. No temporary bundles,
  individual file hashes, MP4s, or Parquet files survived. The historical A100
  mismatch therefore remains honestly unattributed.
- The receipt subtree is byte-identical between `2f780f2` and `4a743bb`,
  with Git tree `a1a44264fe1136ae5ca0228bc95591a7ca173f4c`. All eight
  manifests and 68 immutable logs revalidated. The third-pilot manifest remains
  `4bac1d24a78f3940c56dba0785a5721755cd869e3fdc0a78d39ec4ce7797deee`.
- `evaluator/bundle_diagnostics.py` reports every differing filename, both
  SHA-256 values, sizes, first-byte offset/windows, JSON field paths, Parquet
  table/schema/metadata state, decoded-video metadata and frame differences,
  first pixel delta, and changed attestation dependencies.
- A deliberate simultaneous mutation of all five required files returned all
  five names in canonical order with the required detailed diagnostics. Exact
  byte equality remains fail-closed in `tests/test_evaluator_bundle.py`; no
  file is ignored and no semantic-only comparison replaces the hash gate.
- The runtime change is confined to the MP4 producer in `evaluator/bundle.py`:
  FFmpeg muxer/codec bit-exact flags and explicit single-thread x264
  frame/lookahead ordering. An independent old-versus-corrected probe produced
  different encoded bytes while preserving identical metadata and all eight
  decoded frames.
- Raw artifact hashes remain recorded and verified; they were not suppressed or
  rebaselined. Runtime provenance, five-file completeness, evaluator
  thresholds, 61D observations, 14D actions, 50 Hz unfiltered control, BAM
  authority, model variants, and frozen M5 inputs remain intact.

## Independent Validation

- Six-run distinct-directory/Linux-metadata bundle test: pass.
- Eight separate-process Linux/x86-64 generations: one unique hash for each of
  all five files.
- Isolated Parquet and MP4 producer checks: pass.
- Focused bundle, cross-platform determinism, evaluator-core, and
  model-reconciliation tests with clean BAM `62bd8ce`, official source
  `109e06d`, and locked official runtime: pass.
- Full authority-enabled `tests/run_all.py`, including both Genesis
  environment smokes: pass.
- M5 immutable experiment, CUDA runtime, artifact-attestation, contract-freeze,
  compilation, diff, branch-hygiene, and workflow-audit checks: pass.
- Commit chain is exactly `2f780f2 -> 1669aae -> 4a743bb`; worktree is clean
  and `main` is 97 commits ahead of `origin/main`.
- Closing authenticated Brev inventory: `{"workspaces": null}`.

## Claim And Authority Boundary

Slice 035 closes only the local producer-determinism correction. The terminal
third-pilot result is not reclassified, M5 remains open, and the stop sentinel
remains required.

A fourth-pilot proposal may be drafted only in a later, separate slice after
this acceptance. It must remain `compute_authorized=false`; drafting it would
grant no provisioning or execution authority.
