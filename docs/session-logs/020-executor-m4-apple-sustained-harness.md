# Executor log 020 - M4 Apple sustained harness

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/020-m4-apple-sustained-stability.md`

## Implemented

- Added the frozen 1024-environment, two-warmup, 120-measured-iteration worker.
- Added per-iteration total/collection/update/synchronization timing and finite
  observation plus separate actor/critic parameter checks.
- Added preregistered thermal sampling, slowdown, peak-RSS-proxy memory, package,
  source, and non-serial machine provenance gates.
- Added deterministic sustained-summary coverage and a stable JSON schema.

## Evidence boundary

Implementation only. No sustained result, default selection, final candidate,
held-out realization, task-success classification, transfer, policy activation,
paid compute, or hardware action occurred in this slice.

## Verification

- `.venv-apple/bin/python tests/test_apple_scaling.py` - passed.
- Python compilation of the sustained worker and validation module - passed.
- JSON parsing of the sustained schema - passed.
- `git diff --check` - passed.
