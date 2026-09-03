# Slice Brief 021 - M4 CPU+MPS fallback crossover

**Date:** 2026-09-03

## Objective

Verify the existing Genesis CPU physics plus MPS learner debug fallback and
measure its crossover against Metal physics using matched bounded workloads.

## Preregistered Procedure

- At each tested size, run CPU+MPS and Metal+MPS in separate fresh processes
  from one clean commit, with identical seed/configuration, two warmups, and 20
  measured PPO iterations. Retain no checkpoint.
- Begin at 64 environments. Define the grid crossover as the smallest tested
  environment count where Metal's median total PPO iteration is no slower than
  CPU's matched median.
- If Metal is already no slower at 64, report the crossover as at or below the
  tested lower bound (`<=64`) and stop. Otherwise double through 128, 256, and
  512 until the crossover is observed.
- Require finite observations and actor/critic parameters, nominal declared
  thermal state, and at least 25% RSS-proxy memory headroom for both rows.
- Do not use pure physics SPS for the comparison.

## Acceptance Criteria

- The fallback executes a real PPO collection and update with CPU physics and
  MPS learner on the smallest tested size.
- A checksummed receipt records per-backend construction, warmup, per-iteration
  collection/update/total/sync, samples/minute, memory proxy, thermal method,
  devices, exact packages/source/machine without serial, finiteness, and
  termination.
- The crossover decision follows the frozen median-total-iteration rule.
- If accepted, select the everyday Metal/MPS default only from the completed
  primary sweep plus sustained stability; retain CPU+MPS as debug fallback.

## Evidence Boundary

Performance characterization only. No final candidate, held-out realization,
task-success, transfer, activation, or physical claim.
