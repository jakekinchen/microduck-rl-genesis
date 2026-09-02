# Reviewer Message 015 - M2 deterministic case matrix

**Date:** 2026-09-02

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `6d8796a` freezes ten cases covering all nine required families.
- Two complete matrix runs were byte-identical. A detached clean worktree
  passed focused matrix/core tests, contract freeze, and branch hygiene.
- The BAM-enabled broad runner completed with `tous les tests passent`.

## Findings

NaN, synthetic deadline, joint-margin, and termination outcomes fail or
classify through explicit evaluator paths. Candidate policies and acceptance
seeds are rejected. All reports retain infrastructure-only proof boundaries.

## Milestone State

The deterministic case-matrix item is accepted. M2 remains open.

## Next Slice

Proceed to `docs/briefs/016-m2-heldout-preregistration.md`.
