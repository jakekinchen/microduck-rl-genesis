# Slice Brief 035 - M5 evaluator-bundle determinism

**Date:** 2026-09-03

## Objective

Diagnose the sole same-host five-file evaluator-bundle hash mismatch retained by
the third A100 pilot, add fail-closed byte-level diagnostics, and implement the
smallest local producer-boundary correction that makes repeated generation
byte-identical without weakening evidence semantics.

## Immutable Inputs And Boundaries

- Reviewer 034 and accepted base commit `2f780f2`.
- Checksum-bound third-pilot receipt
  `receipts/m5/pilot/20260904T030457Z-4qe7ph6p7/`, especially immutable
  `logs/full-suite.log` and manifest
  `4bac1d24a78f3940c56dba0785a5721755cd869e3fdc0a78d39ec4ce7797deee`.
- Preserve all accepted pilot receipts byte-for-byte.
- Preserve truthful runtime provenance, raw artifact hashes, five-file
  completeness, decoded video/frame semantics, evaluator thresholds, exact
  model variants, 61D observation, 14D action order, 50 Hz unfiltered control,
  BAM authority, and frozen M5 experiment inputs.
- No Brev provisioning, fourth-pilot authorization, training, candidate,
  held-out, full-matrix, publication, activation, transfer, or physical work.

## Required Diagnosis

- Make the repeated-bundle regression report every differing filename, both
  hashes, and useful byte/container/metadata differences before retaining its
  fail-closed equality assertion.
- Stress repeated generation across distinct output directories and mocked
  Linux/x86-64 runtime metadata.
- Isolate stable JSON, Parquet encoding, MP4/ffmpeg output, environment lock,
  and the attestation dependency chain independently.
- Identify with evidence whether the source is codec/container metadata,
  encoder threading/order, Parquet metadata, or another producer boundary.
- Do not infer missing first/second A100 artifacts from the receipt; they were
  not retained.

## Acceptance Criteria

- Add focused diagnostics and stress/regression coverage that would identify
  the A100 mismatch rather than emit only a map-level assertion.
- Correct only the evidenced nondeterministic producer boundary. Do not ignore
  any file, compare only semantics, remove provenance, or rebaseline expected
  bytes without a demonstrated cause.
- Re-run focused evaluator bundle, cross-platform determinism, evaluator core,
  and model-reconciliation tests with exact BAM and official authority.
- Repeat stress generation, then run the full authority-enabled suite.
- Revalidate every accepted receipt manifest, run branch hygiene from
  `2f780f2`, the M5 contract checks, workflow audit, and diff checks.
- Commit a scoped Executor result and obtain an independent Reviewer decision.
- Only after Reviewer acceptance may a separate fourth-pilot proposal card be
  drafted; it must remain `compute_authorized=false` and grants no provisioning.

## Hard Stops

Stop on a semantic evaluator/model change requiring refreeze, accepted receipt
mutation, absent exact authority with no honest local substitute, or any need
for paid/remote compute.

## Evidence Boundary

Local same-host deterministic producer compatibility only. Passing this slice
would not prove a successful CUDA smoke, M5 completion, task or policy success,
candidate admission, held-out performance, transfer, or physical authority.
