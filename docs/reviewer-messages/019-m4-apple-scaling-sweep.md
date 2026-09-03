# Reviewer Message 019 - M4 Apple scaling sweep

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commit `e393b21` contains five raw JSON rows, five process logs, a
  summary, and passing SHA-256 checksums for run
  `20260903T202404Z-aa4c567`.
- All accepted rows name clean source commit `aa4c567`, the same package and
  non-serial machine identity, Metal physics, and MPS learner.
- All rows report finite observations/learner parameters, nominal declared
  thermal state, and at least 97.75% RSS-proxy headroom.

## Findings

1024 environments had the highest total-iteration-derived throughput at
345,246 samples/min. Its 4.271 s total iteration, 2.164 GiB peak RSS proxy, and
nominal thermal warning state make it the measured candidate for sustained
testing. This is not yet the everyday default: the single measured iteration
does not establish sustained stability or thermal behavior.

## Milestone State

The primary Metal/MPS size sweep is accepted. M4 remains active pending the
preregistered sustained slice and CPU+MPS fallback crossover.

## Next Slice

Proceed to `docs/briefs/020-m4-apple-sustained-stability.md`.
