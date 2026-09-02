# Slice Brief 011 - M2 C MuJoCo evaluator core

**Date:** 2026-09-02

## Objective

Build the first CPU-only independent evaluator core around official MuJoCo,
ONNX Runtime CPU, and the pinned BAM `MujocoController`. Freeze the 5 ms physics
and 50 Hz unfiltered policy loop, model/interface/task inputs, deterministic
case identity, and report envelope before any candidate policy is inspected.

## Acceptance Criteria

- Load only a validated ONNX artifact and use the CPU execution provider with
  one inference thread and a 61D float32 input / 14D float32 output check.
- Load the pinned model lock and all-collisions or walking MJCF as declared by
  the task; reject digest, joint-order, timestep, or actuator-order drift.
- Drive all 14 joints through the pinned BAM CPU MuJoCo controller at every
  5 ms physics step; update the target only every four steps with no action
  filter.
- Define deterministic case IDs, SHA-256-counter seed material, observation
  state, action/deadline telemetry, finite-state checks, and policy-bound report
  metadata without using a training backend's rewards.
- Add a bounded synthetic or known-fixture smoke that proves reset, inference,
  BAM control, stepping, and byte-stable report generation. Its classification
  must remain infrastructure-only, never task success.
- Add focused tests, Executor log, scoped commit, and separate Reviewer
  decision. Do not yet emit or claim the complete M2 evidence bundle.

## Expected Files

- evaluator implementation and versioned configuration under `evaluator/`
- a small deterministic ONNX fixture and expected report under `tests/fixtures/`
- focused evaluator tests and default runner integration
- `docs/session-logs/011-executor-m2-c-mujoco-evaluator-core.md`

## Validation

```bash
.venv-apple/bin/python <focused-evaluator-test>
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python tests/run_all.py
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

A deterministic synthetic/known-fixture rollout proves evaluator plumbing only.
It does not establish walking or backflip task success, a held-out result,
backend superiority, transfer, or physical authority.

## Stop Conditions

- The evaluator would silently reimplement BAM instead of consuming the pinned
  controller or cannot bind the source authority.
- Required dependency or model authority is unavailable and no honest
  infrastructure-only negative result can be recorded.
- The next action would inspect a final candidate, publish, push, require
  credentials, spend paid compute, activate a policy, or operate hardware.
