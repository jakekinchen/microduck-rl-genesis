# Reviewer Message 003 - M1 authoritative BAM golden vectors

**Date:** 2026-09-01

## Decision

`CONTINUE`

## Evidence Reviewed

- Commits `9dcf032` and `3841121` contain the generator, 29-vector fixture,
  production-path refactor, fixture consumer, generated lock binding, and
  strengthened provenance.
- The fixture authority commit matches the official Microduck lock and the
  checked-out BAM source. All recorded BAM source, tree, parameter, license,
  runtime, fixture, and lock digests verify.
- Independent regeneration is byte-identical.
- The focused consumer matches voltage, torque, BAM-core friction, and
  deployed-mjlab friction at float64 tolerances and executes reset delegation.
- The existing 2,000-case authority comparison and 0.6 s Genesis versus
  MuJoCo+BAM loop pass from the exact pinned checkout.
- The BAM-enabled full runner passes with no BAM skip.

## Findings

The fixture correctly preserves, rather than erases, the 1.52% maximum
documented difference between BAM core's quadratic sign gate and the deployed
mjlab profile. The equal-magnitude edge defect found in the optional core mode
was fixed without changing the deployed default.

The initial fixture omitted the mjlab/Torch runtime and did not exercise base
delay reset. The follow-up binds both runtime versions, hashes the XL330/registry
sources, and executes a reset probe. No remaining slice blocker was found.

## Milestone State

The first M1 implementation item is closed: authoritative open-loop and reset
fixtures exist and Genesis consumes them. M1 remains open because no retained
14-servo trajectory fixture or official mjlab fixture consumer exists, model
variants are not reconciled, task semantics are not frozen, and no
upstream-or-divergence decision is versioned.

## Next Slice

Proceed to `docs/briefs/004-m1-closed-loop-servo-fixture.md`. Generate the
reference trajectory only from the same pinned BAM commit and official MuJoCo;
keep BAM-core and deployed-mjlab profiles explicit.
