# Executor log 011 - M2 C MuJoCo evaluator core

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/011-m2-c-mujoco-evaluator-core.md`

## Implemented

- Added a CPU-only evaluator core using official MuJoCo's C engine through its
  Python bindings, ONNX Runtime `CPUExecutionProvider` with one thread, and the
  pinned BAM `bam.mujoco.MujocoController`.
- Bound the walking/backflip task digests, their referenced interface/model/BAM
  contracts, model root and scene digests, BAM parameter digest and clean
  authority commit, 14-joint actuator order, 5 ms physics step, four-step
  control decimation, and no action filter.
- Added an independent 61D observation builder, finite-state checks,
  SHA-256-counter seed primitive, action/deadline counters, and deterministic
  trajectory/report hashing. Training rewards are not imported or consulted.
- Added a 3.7 KiB zero-output ONNX fixture and retained 40-step report. The
  fixture holds HOME, exercises ten ONNX calls and 40 BAM/MuJoCo updates, and
  stays explicitly `infrastructure_only` with `task_success: not_evaluated`.
- Verified both the walking and all-collisions backflip model lanes load with
  the locked 14-actuator order and timestep.
- Added fail-closed ONNX shape validation, a CLI, focused tests, documentation,
  and default runner reachability. With no `BAM_REPO`, the focused runner emits
  an explicit authority-unavailable skip rather than substituting actuator
  math.

## Validation receipts

```text
evaluator core verified: two byte-identical 40-step reports,
10 CPU ONNX calls, 40 pinned BAM updates
```

The BAM-enabled full runner completed with `tous les tests passent`; `git diff
--check` passed. The retained trajectory digest is
`sha256:2b58cb2130ea03cc6dda9ccde937fde6c5061b49e2fbbb5373772bd84fff11d4`.

## Evidence boundary

This is deterministic evaluator plumbing only. It does not implement the full
M2 report bundle or M3 task classifiers and does not establish walking,
backflip, held-out, cross-backend, transfer, or physical success. No final
candidate was inspected. No training, paid compute, credentials, publication,
or hardware operation occurred.
