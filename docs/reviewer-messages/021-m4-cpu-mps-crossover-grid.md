# Reviewer Message 021 - M4 CPU+MPS crossover grid

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commits `8b9116e` and `0a96039` contain the matched harness and
  checksummed eight-row receipt through 512 environments.
- CPU and Metal rows share source, seed/config, MPS learner, 20 measured PPO
  iterations, and the declared finite/thermal/memory gates.
- CPU median total PPO time remained lower through 512; all rows were finite,
  nominal by the thermal method, and above 97.69% RSS-proxy headroom.

## Findings

The CPU+MPS fallback is operational. The frozen crossover was not observed on
the 64-512 grid, so the accepted result is `>512`, not an inferred exact point.
Because the primary and sustained receipts already establish 1024 as locally
finite and memory-safe, one matched 1024 extension is bounded and feasible.

## Milestone State

The fallback grid is accepted. M4 remains active for the preregistered 1024
extension and final default/fallback decision.

## Next Slice

Proceed to `docs/briefs/022-m4-cpu-mps-crossover-1024.md`.
