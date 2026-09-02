# Reviewer Message 009 - M1 backflip task semantics

**Date:** 2026-09-02

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commits `8a5ad9c` and `e238f81` contain the exact-authority
  generator, generated semantic file and lock, schema, focused validator,
  default-runner integration, and corrected Executor log.
- A detached clean worktree regenerated the contract byte-for-byte from clean
  backflip commit `8bde27eb...` and BAM commit `62bd8ce1...` using the locked
  optional mjlab runtime.
- Contract freeze and branch hygiene passed. The detached review tree remained
  clean.
- Negative Reviewer probes attempted to enable virtual torque, mark candidate
  inspection, reduce coverage, and substitute a specialist variant. The
  validator rejected all four mutations.
- The BAM-enabled broad suite passed with the exact-authority check reachable
  from `tests/run_all.py`.

## Findings

The contract is correctly limited to the effective base-flat factory. It binds
the shared 61D actor, 14D action, 50 Hz loop, BAM delay, full-collision model,
backflip state machine, reverse-curriculum populations, and virtual-spotter
schedule without claiming trajectory identity.

The inventory preserves material differences: official 74D versus Genesis 90D
critic state, sampled near-zero versus fixed-zero twist, no clip versus the
Genesis input guard, named geom sensors versus link-contact classification,
the inherited official reward set, mass-plus-inertia versus mass-only
randomization, and backend RNG/lifecycle/solver behavior.

The acceptance battery was frozen without candidate inspection. Its 20 cases
start only from ordinary standing HOME at full action authority with no
spotter, injected flight/recovery state, reference state, pedestal, mat, cube,
or correction. Every case requires a collision-free airborne backward
revolution, feet-only first recontact, margins, finite execution, and a
continuous 0.5-second stable hold. Reward is not the success definition.

## Milestone State

Backflip semantics are closed. M1 remains open only for the explicit
upstream-submission or versioned-divergence decision.

## Next Slice

Proceed to `docs/briefs/010-m1-versioned-divergence-decision.md`. Produce a
machine-readable local decision that binds both task contracts and every open
divergence. Do not publish or submit upstream under the current no-publication
constraint.
