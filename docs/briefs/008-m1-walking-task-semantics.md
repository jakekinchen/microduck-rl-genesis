# Slice Brief 008 - M1 walking task semantics

**Date:** 2026-09-02

## Objective

Freeze a backend-independent walking semantic file from the exact committed
official task and the repo-local Genesis implementation. Separate training
curriculum/reward behavior from evaluation starts and reward-independent task
success before any final policy result is inspected.

## Acceptance Criteria

- Bind the same official Microduck commit used by model reconciliation and the
  repo-local interface/model/BAM locks.
- Record command dimensions and ranges, command resampling, 61D actor slices,
  privileged observations, 14D action order and scale, 50 Hz control timing,
  decimation, default pose, actuator delay, and reset behavior.
- Record training-only reward terms, curriculum, pushes, domain randomization,
  assistance, and termination conditions without treating them as success.
- Define backend-independent walking acceptance starts and metrics before
  evaluating a final candidate: survival duration, command-grid coverage,
  tracking error, fall rate, stop drift, foot slip, orientation, joint/torque
  margins, NaN/deadline failures, and deterministic seed handling.
- Identify every semantic field that differs or is unavailable between
  official mjlab and Genesis. Fail on an unclassified action, observation, or
  timing difference.
- Add a schema/validator and bind the semantic file from the generated
  contract. Do not run training or promote task success in this slice.

## Expected Files

- `microduck_contract/tasks/walking-v1.json`
- a deterministic generator or extractor under `scripts/`
- a focused validator under `tests/`
- generated task lock metadata
- `docs/session-logs/008-executor-m1-walking-task-semantics.md`

## Validation

```bash
<python> <walking-semantics-generator> --official-repo <repo> --official-commit 109e06d4ce4921b635c5609e5304079fc30960ae
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python <focused-validator>
BAM_REPO=<pinned-checkout> .venv-apple/bin/python tests/run_all.py
git diff --check
```

## Evidence Boundary

Passing freezes the declared walking contract and future acceptance protocol.
It does not show that any policy walks successfully, passes held-out cases,
transfers to hardware, or has physical authority.

## Stop Conditions

- A load-bearing official task semantic cannot be recovered from the pinned
  commit and no honest unresolved marker can preserve the boundary.
- Freezing a threshold would use final candidate outcomes rather than a
  preregistered requirement.
- The task would need policy activation, physical testing, or paid compute.
