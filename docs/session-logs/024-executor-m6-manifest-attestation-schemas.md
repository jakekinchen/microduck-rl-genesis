# Executor log 024 - M6 manifest and attestation schemas

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/024-m6-manifest-attestation-schemas.md`

## Implemented

- Added policy-manifest-v2, reference-attestation-v1, and
  hardware-attestation-v1 schemas.
- Added synthetic official and community bundles binding normalized ONNX,
  normalizer, checkpoint, exporter, model, BAM, task, evaluator, evidence, and
  license bytes by SHA-256 and size.
- Added non-executing validation for source class, 61D/14D/50 Hz interface,
  baked-and-bound normalization, exact provenance, path containment, complete
  roles, separated lifecycle states, and evidence/physical authority.
- Fixture exporters raise on import, and fixture ONNX/checkpoint files are plain
  non-executable markers.

## Verification

- Both synthetic bundles pass the CLI validator.
- Negative probes reject missing roles, digest mismatch, official/community
  confusion, activation promotion, reference task-success promotion, and
  synthetic physical-authority promotion.
- Python compilation, JSON parsing, and `git diff --check` pass.

## Evidence boundary

Synthetic packaging infrastructure only. No real artifact was downloaded,
imported, evaluated, approved, activated, published, or deployed. No task,
transfer, or physical authority was created.
