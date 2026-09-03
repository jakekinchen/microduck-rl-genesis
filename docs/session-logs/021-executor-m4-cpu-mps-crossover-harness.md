# Executor log 021 - M4 CPU+MPS fallback crossover

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/021-m4-cpu-mps-crossover.md`

## Implemented

- Added matched CPU-or-Metal physics plus MPS learner benchmark rows with two
  warmups and 20 measured PPO iterations.
- Preserved exact seed/config parity and recorded the preregistered timing,
  finite-state, thermal, memory-proxy, provenance, and evidence-boundary fields.
- Added deterministic crossover decision coverage and a stable row schema.

## Execution result

- Ran matched CPU+MPS and Metal+MPS pairs at 64, 128, 256, and 512 from clean
  commit `8b9116e`, following the frozen stop/continue rule.
- CPU median total PPO iteration was lower at every size: 0.4475 vs 2.1608 s
  at 64, 0.5417 vs 2.2552 s at 128, 0.9432 vs 2.2923 s at 256, and 1.5747 vs
  2.3473 s at 512.
- All eight rows completed 20/20 finite measured iterations, had nominal
  thermal warning-state samples, and retained at least 97.69% RSS-proxy
  headroom.
- The crossover was not observed through the preregistered grid and is honestly
  reported as `>512`, pending a separately preregistered 1024 extension.
- Durable receipt:
  `receipts/apple-scaling/20260903T204713Z-8b9116e-crossover/`.

## Verification

- Focused Apple scaling/crossover tests - passed in `.venv-apple`.
- Python compilation and crossover-schema JSON parsing - passed.
- `git diff --check` - passed.

## Evidence boundary

Performance characterization only. No final candidate, held-out realization,
task-success, transfer, activation, paid compute, or hardware action occurred.
