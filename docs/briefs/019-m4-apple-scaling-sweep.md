# Slice Brief 019 - M4 Apple scaling sweep

**Date:** 2026-09-03

## Objective

Run the committed Apple scaling harness at 64, 128, 256, 512, and, only after
the 512-row safety check, 1024 environments. Assemble a durable raw and summary
receipt from a clean source commit.

## Preregistered Procedure

- Run each size in a fresh process with Genesis Metal physics and MPS PPO.
- Use one warmup and one measured public-development PPO iteration, with 24
  rollout steps per environment and the committed training configuration.
- Run sizes sequentially in ascending order.
- Continue from 512 to 1024 only when the 512 row completed with finite
  observations and learner parameters, nominal recorded thermal state, and at
  least 25% peak-RSS-proxy unified-memory headroom.
- Stop the sweep on a non-finite result, thermal warning, failed process, or
  less than 25% proxy headroom. Preserve the failing log; do not impute data.
- Do not select the everyday default from this sweep alone. The sustained
  preregistered slice must pass first.

## Acceptance Criteria

- Required safe sizes have raw JSON and process logs with construction, warmup,
  collection, learner-update, total iteration, reset/sync, samples/minute,
  memory proxy, devices, thermal method, finiteness, and termination.
- The summary validates common clean commit provenance and the stable schema.
- `SHA256SUMS` covers raw rows/logs and `sweep.json`.
- The receipt remains performance characterization only.

## Evidence Boundary

Short public development workload only. No final candidate, task-success
classification, held-out realization, transfer, or physical claim.
