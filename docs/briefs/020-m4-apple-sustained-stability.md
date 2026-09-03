# Slice Brief 020 - M4 Apple sustained stability

**Date:** 2026-09-03

## Objective

Run a bounded sustained Metal/MPS public-development PPO workload at the
measured 1024-environment candidate and decide whether it is stable enough to
remain eligible as the everyday default.

## Preregistered Procedure

- Source size selection only from the accepted sweep: 1024 had the highest
  samples/minute computed from total PPO iteration, while remaining finite,
  thermally nominal, and memory-safe by the declared proxies.
- Use one fresh process, two warmup PPO iterations, then 120 consecutive
  measured PPO iterations at 24 steps/environment with the committed public
  development configuration. Do not save a checkpoint.
- Record collection, learner update, synchronization, and wall time for every
  measured iteration; sample `pmset -g therm` before construction, after
  warmup, every ten measured iterations, and after completion.
- Check observations and actor/critic parameters for finiteness every measured
  iteration. Record peak process RSS and the same explicit unified-memory proxy.
- Stop without selecting a default on non-finite state, process failure,
  recorded thermal warning, or less than 25% proxy headroom.

## Acceptance Criteria

- All 120 measured iterations complete with finite state and nominal recorded
  thermal status; proxy memory headroom remains at least 25%.
- The median total PPO iteration of the last 20 iterations is no more than
  1.25 times the median of the first 20 iterations.
- Receipt records per-iteration timings, first/last medians, p50/p95 total
  iteration, total samples/minute, thermal samples, peak RSS proxy, provenance,
  limitations, termination, and SHA-256 checksums.
- Passing the slice only keeps 1024 eligible. The CPU+MPS fallback crossover
  must be recorded before M4 closes.

## Evidence Boundary

Performance and stability characterization only. No final candidate,
task-success classification, held-out realization, transfer, or physical claim.
