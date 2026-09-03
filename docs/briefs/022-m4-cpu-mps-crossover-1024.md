# Slice Brief 022 - M4 CPU+MPS crossover at 1024

**Date:** 2026-09-03

## Objective

Extend the accepted matched crossover grid by exactly one already-proven-safe
size, 1024 environments, and close M4 with an exact or bounded decision.

## Preregistered Procedure

- Extend the committed worker/schema to admit 1024 without changing the frozen
  two-warmup, 20-measured-iteration, seed/config, timing, or safety protocol.
- Run CPU+MPS then Metal+MPS at 1024 in separate fresh processes from the same
  clean commit.
- If Metal median total PPO iteration is no slower than CPU, record the grid
  crossover as 1024. Otherwise record it as `>1024`; do not extend further.
- Stop on non-finite state, recorded thermal warning, process failure, or less
  than 25% RSS-proxy headroom and preserve the terminal result.

## Acceptance Criteria

- Both matched rows pass the declared gates and are checksummed with a summary.
- The crossover decision follows median total PPO iteration, not pure physics
  throughput.
- Close M4 by selecting 1024 as the everyday Metal/MPS default only if its
  already-accepted sweep and sustained evidence remain valid. Keep CPU+MPS as
  the explicitly verified debug fallback.

## Evidence Boundary

Performance characterization only. No final candidate, held-out realization,
task-success, transfer, activation, or physical claim.
