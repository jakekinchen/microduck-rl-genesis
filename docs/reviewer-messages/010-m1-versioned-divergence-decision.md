# Reviewer Message 010 - M1 versioned divergence decision

**Date:** 2026-09-02

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `635324c` contains the generated decision, schema, lock, generator,
  focused validator, default-runner integration, and Executor log.
- A detached clean worktree regenerated the decision from the two task
  contracts, verified all generated locks, and passed branch hygiene.
- The decision covers all 45 non-exact inventory rows and has no duplicate or
  unbound entries.
- Negative Reviewer probes attempted to claim an upstream submission, erase an
  entry, claim training-trajectory equivalence, and change a disposition. The
  validator rejected all four mutations.
- The BAM-enabled broad suite passed with the new decision check reachable
  from `tests/run_all.py`.

## Findings

The selected path is an explicit local versioned divergence, not an implied
upstream submission. The decision binds both frozen task digests and separates
accepted semantic equivalences, evaluator-owned normalization/boundaries,
deferred implementation reconciliation, and training-only non-equivalence.

The exact deployed actor/action/control interface, thresholded BAM fixtures,
and model conformance remain valid. The decision correctly keeps training
trajectory equivalence, task success, held-out evidence, transfer, and physical
authority false.

## Milestone State

M1 is closed. Genesis and official mjlab consume the pinned interface/BAM/model
fixtures, both task semantics are frozen, and every non-exact field has a
versioned disposition.

## Next Slice

Proceed to `docs/briefs/011-m2-c-mujoco-evaluator-core.md`. Build only the
deterministic CPU evaluator core and synthetic/known-fixture proof first; do not
inspect or classify a final candidate policy.
