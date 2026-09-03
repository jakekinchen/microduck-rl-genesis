# Slice Brief 024 - M6 manifest and attestation schemas

**Date:** 2026-09-03

## Objective

Add policy-manifest-v2 plus reference and hardware attestation schemas, with a
non-executing validator and synthetic official/community fixtures.

## Acceptance Criteria

- Policy manifest binds by SHA-256 the normalized ONNX, normalizer, source
  checkpoint, exporter, model, BAM, task, evaluator, evidence, and license
  inputs, plus exact source/run/checkpoint identity.
- Reference attestation records immutable reference provenance and evaluation
  bindings without granting task, transfer, or physical authority.
- Hardware attestation records exact artifact/hardware/runtime/protocol
  identity, approval and activation state, and terminal result without allowing
  simulation/reference evidence to confer physical authority.
- The validator parses files and hashes bytes only; it never imports repository
  code, initializes ONNX Runtime, runs a policy, activates hardware, downloads,
  or publishes.
- Synthetic official and community fixtures pass; missing bindings, digest
  mismatch, source-class confusion, or state/authority promotion fail closed.

## Evidence Boundary

Synthetic packaging infrastructure only. No real artifact is accepted,
downloaded, imported, evaluated, approved, activated, published, or deployed.
