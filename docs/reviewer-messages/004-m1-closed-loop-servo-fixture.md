# Reviewer Message 004 - M1 closed-loop 14-servo fixture

**Date:** 2026-09-01

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `ed244b0` contains only the generator, retained trajectory, Genesis
  consumer, generated lock binding, runner wiring, contract note, and Executor
  evidence for Slice 004.
- The retained fixture is bound to the exact BAM authority commit and tree. Its
  BAM model and servo-parameter digests cross-check the approved open-loop
  authority fixture before generation.
- Independent regeneration is byte-identical. The retained fixture SHA-256
  equals the digest in the generated BAM actuator lock.
- The focused Genesis consumer reports per-joint worst error with exact time
  and retains the full 120-step trajectory for failure inspection.
- The full BAM-enabled runner passes from the pinned checkout without a BAM
  skip; the absent trained ONNX remains explicitly non-applicable.

## Findings

The first implementation passed numerically but only recorded the open-loop
authority provenance and collapsed a future failure to scalar assertions. The
final commit actively cross-checks authority digests and identifies the
offending joint or base-height timestep. No remaining Slice 004 blocker was
found.

The standing trajectory remains a narrow, unstable 0.6-second case. Its
agreement does not prove walking, backflip, official deployed-mjlab parity,
task success, held-out performance, or physical authority.

## Milestone State

The second M1 implementation item is closed: a deterministic official-MuJoCo
plus BAM-core 14-servo trajectory is retained and consumed by Genesis. M1
remains open because the official mjlab/MuJoCo Warp adapter has not consumed
the fixtures, model variants are not reconciled, task semantics are not
frozen, and no upstream-or-divergence decision is versioned.

## Next Slice

Proceed to `docs/briefs/005-m1-official-mjlab-fixture-consumer.md`. Exercise the
exact pinned deployed adapter through its real mjlab/MuJoCo Warp path and keep
its documented no-gate profile distinct from BAM core.
