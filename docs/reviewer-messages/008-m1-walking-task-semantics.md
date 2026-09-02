# Reviewer Message 008 - M1 walking task semantics

**Date:** 2026-09-02

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `2ed4ef4` contains the exact-authority generator, retained semantic
  file and task lock, formal schema, default/authority validator, runner
  integration, contract documentation, and Executor evidence.
- A detached clean worktree regenerated the walking contract byte-for-byte
  against official Microduck commit `109e06d4...` and clean BAM commit
  `62bd8ce1...` using the repo-owned optional environment.
- Generated contract snapshots and the full branch-hygiene gate passed.
- A negative reviewer probe enabled an external push in the acceptance
  assistance block; the validator rejected it.
- The final BAM-enabled broad suite passed with the new default walking check
  reachable from `tests/run_all.py`.

## Findings

The 61D deployed actor, 14D action, 50 Hz loop, commands, and comparable
training declarations are bound and checked. The contract correctly refuses a
training-trajectory-equivalence claim.

The effective official import exposed a shared-config mutation: the registered
rough training terrain is 5x5 with curriculum disabled after the play config is
constructed, although the source declares 10x20. The contract also preserves
the 76D-versus-90D critic split, mass-plus-inertia versus mass-only
randomization, sensor/terrain/lifecycle differences, action guard, and reset
yaw difference. These are findings for the later versioned divergence decision,
not reasons to inflate or reject the exact deployed interface claim.

The acceptance suite was frozen before candidate inspection and requires 230
command/start/seed cells with no assistance. Reward is explicitly excluded as
a success definition.

## Milestone State

Walking semantics are closed. M1 remains open because backflip semantics and
the final upstream-or-versioned-divergence decision remain unfinished.

## Next Slice

Proceed to `docs/briefs/009-m1-backflip-task-semantics.md` against the clean
`Lulzx/microduck-backflip` authority. Keep reverse-curriculum, phase cues, and
the virtual spotter visible as training-only state, and require an ordinary
standing, zero-assistance acceptance start.
