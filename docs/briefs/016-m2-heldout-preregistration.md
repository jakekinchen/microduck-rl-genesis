# Slice Brief 016 - M2 held-out preregistration

**Date:** 2026-09-02

## Objective

Create a cryptographically bound development-versus-held-out protocol whose
acceptance seeds cannot be known or tuned against before a candidate is frozen.

## Acceptance Criteria

- Keep visible development suites, public acceptance definitions, and blinded
  held-out realization as distinct proof classes.
- Bind held-out case templates, counts, ranges, evaluator/task/model/BAM locks,
  derivation algorithm, and ordering now.
- Derive concrete held-out seeds only from a named future public randomness
  value published after an immutable candidate-freeze attestation.
- Reject realization when the candidate freeze is not earlier than the beacon,
  the beacon is malformed, or any committed binding drifts.
- Test derivation with synthetic attestations/beacons only; do not inspect a
  final candidate or fetch a live future beacon.

## Evidence Boundary

Preregistration and synthetic protocol tests only. No held-out case is realized
or executed, and no policy result or task success is evaluated.
