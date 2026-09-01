# Reviewer Message 005 - M1 official mjlab fixture consumer

**Date:** 2026-09-01

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `c62f675` contains the fail-closed consumer, explicit wrapper,
  generated runtime lock, README reachability, and Executor evidence.
- The consumer refuses the wrong or dirty BAM checkout, verifies the imported
  actuator source path and authority digests, and enforces the exact locked
  official runtime versions before physics execution.
- All 29 open-loop rows execute through pinned official sources with exact
  voltage, torque, deployed friction, and reset results.
- The 14-servo run instantiates the real pinned `bam.mjlab.BamActuator` through
  mjlab `Scene`/`Simulation` and MuJoCo Warp on Apple CPU. It writes and verifies
  the declared initial state, then reports every joint's worst timestep.
- The full BAM-enabled Genesis suite still passes without a BAM skip.

## Findings

The initial prototype exposed a harness error rather than a backend failure:
`scene.reset()` left the model at its zero keyframe. The final consumer writes
the exact fixture root and joint state and verifies it before the first step.
No action assistance or backend modification was introduced.

The installed task-entrypoint circular-import warning is non-fatal and the task
package is not registered. Source-path and version checks prove the accepted
actuator came from the exact pinned BAM checkout. No remaining Slice 005
blocker was found.

## Milestone State

The third M1 implementation item is closed: the pinned official
mjlab/MuJoCo Warp adapter consumes the approved open-loop and closed-loop
fixtures on a recorded CPU runtime. M1 remains open because model variants are
not reconciled, walking/backflip semantics are not frozen, and no
upstream-or-divergence decision is versioned.

## Next Slice

Proceed to `docs/briefs/006-m1-model-reconciliation.md`. Produce a
machine-readable, commit-bound comparison of canonical and variant models
before changing any model source.
