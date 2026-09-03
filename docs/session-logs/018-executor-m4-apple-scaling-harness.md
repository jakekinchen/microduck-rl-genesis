# Executor log 018 - M4 Apple scaling harness

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/018-m4-apple-scaling-harness.md`

## Implemented

- Added a one-size-per-process Metal/MPS benchmark worker with one warmup and
  one measured real PPO iteration.
- Records construction, reset, synchronization, collection, learner update,
  total iteration, throughput, samples/minute, peak RSS, explicit unified-memory
  proxy limitations, package/source/machine identity, thermal warning state,
  finiteness, and termination.
- Added deterministic schema, device/finiteness, and safe-default selection
  tests. No default is selected by this implementation slice.
- Added a run assembler that requires all five clean-commit rows and writes a
  summarized receipt plus SHA-256 checksums for the raw logs and measurements.

## Evidence boundary

Short public development workload only. No final candidate, held-out seed,
task-success classification, transfer, publication, paid compute, activation,
or hardware action occurred.

## Verification

- `.venv-apple/bin/python tests/test_apple_scaling.py` - passed.
- Python compilation of the worker, assembler, and validation module - passed.
- JSON parsing of `benchmarks/apple-scaling-schema-v1.json` - passed.
- `git diff --check` - passed.
