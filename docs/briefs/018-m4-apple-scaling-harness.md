# Slice Brief 018 - M4 Apple scaling harness

**Date:** 2026-09-02

## Objective

Replace the ad-hoc single-size benchmark with a bounded, receipt-producing
Apple scaling harness for 64, 128, 256, 512, and 1024 environments.

## Acceptance Criteria

- Record construction, warmup, physics collection, learner-update, reset,
  synchronization, peak RSS/unified-memory proxy, thermal state, finiteness,
  device/backend, and environment metadata per size.
- Use a short public development workload only; no candidate training or task
  success classification.
- Emit stable JSON schema and a run-scoped receipt; select no default until all
  required sizes and a sustained thermal run complete.
- Fail closed on non-finite state or unsupported device selection.

## Evidence Boundary

Performance characterization only. It does not train or rank a candidate,
close M4 without the sustained run, or establish task/physical success.
