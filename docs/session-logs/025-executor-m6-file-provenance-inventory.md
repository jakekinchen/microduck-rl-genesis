# Executor log 025 - M6 file provenance inventory

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/025-m6-file-provenance-inventory.md`

## Implemented

- Added a deterministic file-level generator/validator for all tracked
  MicroDuck MJCF/STL assets, asset license exceptions, ONNX weights, and
  distributed demo media.
- Exact source comparison uses git blobs at official walking commit `109e06d`
  without importing source code.
- Dataset scope is explicitly empty; no provenance is invented.
- Policies retain missing checkpoint/run/exporter/normalizer/file-license
  blockers. Media retains missing production/source/license/attribution
  blockers. The local `ball.xml` upstream-byte mismatch remains partial.

## Evidence boundary

Inventory and negative evidence only. No artifact was accepted, downloaded,
imported, evaluated, published, approved, activated, or deployed.

## Result

- 70 files inventoried: 63 complete, 2 partial, and 5 missing.
- The partial entries are the exact-byte-divergent `ball.xml` and the actuator
  parameter file whose BAM license attribution lacks an upstream path/blob
  binding.
- The five missing entries are three repository policy weights and two demo
  media files. None was promoted or executed.

## Verification

- Generation followed by `--check` reproduced the committed JSON exactly and
  rechecked all exact official git blobs.
- Focused tests reject coverage gaps, local digest drift, false policy
  completeness, and lifecycle evaluation promotion.
- Python compilation, JSON parsing, and `git diff --check` pass.
