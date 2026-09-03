# Reviewer Message 022 - M4 CPU+MPS crossover at 1024

**Date:** 2026-09-03

## Decision

`STOP`

## Evidence Reviewed

- Executor commits `e6d35ce` and `59d9f38` contain the preregistered extension,
  matched raw rows, summary, README, and passing SHA-256 manifest.
- At 1024, Metal+MPS median total PPO iteration was 2.5271 s versus 3.0963 s
  for CPU+MPS; both completed 20/20 finite iterations with nominal declared
  thermal samples and at least 97.53% RSS-proxy headroom.
- The primary five-size sweep selected 1024 by highest throughput derived from
  total PPO iteration, subject to finite/thermal/memory gates.
- The 120-iteration 1024 sustained run passed its frozen slowdown, finiteness,
  thermal-warning-state, and RSS-proxy gates.
- The full local test suite passed; unavailable BAM-authority tests reported
  their existing explicit skips, and the official-policy check retained its
  terminal missing-authority result.

## Findings

The measured grid crossover is 1024 environments. Set 1024 with Metal physics
and MPS learning as the everyday Apple default. Keep CPU physics plus MPS as the
verified debug fallback; it was faster on the measured 64-512 grid. These are
performance defaults, not policy-quality or task-success evidence.

The thermal method remains `pmset` warning-state sampling rather than direct
temperature/power/throttling telemetry, and peak process RSS remains a unified-
memory proxy. Those limitations are explicit in every receipt.

## Milestone State

M4 is accepted and closed. M2 remains narrowly open only on official-policy
provenance/repeatability. M5 must not begin candidate training without a new
immutable experiment brief, the missing official authority, and authorized
CUDA execution; current constraints do not authorize paid compute.

## Stop Reason

The delegated M4 work is complete. The next milestone crosses a new candidate-
training and external-compute authority boundary, so no M5 run is started.
