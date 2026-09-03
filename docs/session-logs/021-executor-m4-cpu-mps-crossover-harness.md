# Executor log 021 - M4 CPU+MPS crossover harness

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/021-m4-cpu-mps-crossover.md`

## Implemented

- Added matched CPU-or-Metal physics plus MPS learner benchmark rows with two
  warmups and 20 measured PPO iterations.
- Preserved exact seed/config parity and recorded the preregistered timing,
  finite-state, thermal, memory-proxy, provenance, and evidence-boundary fields.
- Added deterministic crossover decision coverage and a stable row schema.

## Evidence boundary

Implementation only. No fallback result, final candidate, held-out realization,
task-success, transfer, activation, paid compute, or hardware action occurred.

## Verification

- Focused Apple scaling/crossover tests - passed in `.venv-apple`.
- Python compilation and crossover-schema JSON parsing - passed.
- `git diff --check` - passed.
