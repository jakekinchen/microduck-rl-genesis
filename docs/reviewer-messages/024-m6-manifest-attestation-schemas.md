# Reviewer Message 024 - M6 manifest and attestation schemas

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `973a204` adds policy-manifest-v2, reference-attestation-v1, and
  hardware-attestation-v1 schemas plus a non-executing validator.
- Synthetic official and community bundles bind all ten required artifact
  classes by size and SHA-256. Their exporter raises on import, while validation
  succeeds because it only parses metadata and hashes bytes.
- Negative probes reject missing bindings, digest mismatch, source-class
  confusion, activation promotion, task-success promotion, and physical-
  authority promotion.
- The full local suite passes with existing explicit authority skips.

## Findings

Download, library import, evaluation, approval, and activation are independent
states. Reference evidence cannot grant task, transfer, hardware, or activation
authority; synthetic hardware evidence cannot grant physical authority.

These fixtures prove schema mechanics only. They do not accept the existing
repository policies or any upstream artifact.

## Milestone State

The M6 schema/validator foundation is accepted. M6 remains open for the
file-level provenance inventory and real attributable artifacts.

## Next Slice

Proceed to `docs/briefs/025-m6-file-provenance-inventory.md`.
