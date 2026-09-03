# Executor log 020 - M4 Apple sustained stability

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

## Execution result

- Clean source commit: `3223b260697f222cc29bd47ced48e81110e6d917`.
- Completed two warmups and all 120 measured PPO iterations at 1024
  environments; no checkpoint was saved.
- All per-iteration observation and actor/critic parameter checks were finite.
- All 15 preregistered thermal warning-state samples were nominal.
- Peak RSS proxy was 2.741 GiB with 97.15% proxy headroom.
- First/last 20-iteration medians were 2.5049 s and 2.4372 s, a 0.9730 ratio
  against the 1.25 acceptance ceiling. Overall p50/p95 were 2.4801/2.6064 s.
- Total-iteration-derived throughput was 591,736 samples/min.
- Durable receipt:
  `receipts/apple-scaling/20260903T203517Z-3223b26-sustained/`.

## Verification

- Sustained receipt validation passed all frozen gates.
- `shasum -a 256 -c SHA256SUMS` passed for `receipt.json` and `process.log`.

## Evidence boundary

Performance and stability characterization only. The result keeps 1024
eligible but does not close M4 until the CPU+MPS fallback crossover is recorded.
No final candidate, held-out realization, task-success classification, transfer,
policy activation, paid compute, or hardware action occurred.

## Implementation verification

- `.venv-apple/bin/python tests/test_apple_scaling.py` - passed.
- Python compilation of the sustained worker and validation module - passed.
- JSON parsing of the sustained schema - passed.
- `git diff --check` - passed.
