# Executor log 009 - M1 backflip task semantics

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/009-m1-backflip-task-semantics.md`

## Authority inspected

- Clean source checkout: `/Users/kelly/Developer/microduck-backflip`
- Commit: `8bde27eb141c8f14db05fc4370e536521203a98d`
- Tree: `bfd9f2d3913da0ccf2156d4bff07c2aed407212d`
- Effective entrypoint: `make_microduck_backflip_env_cfg(play=False)`
- BAM commit: `62bd8ce12154340be97e06f7f41a0ca8f116d967`
- Source was materialized with `git archive` before import so the sparse
  working-tree layout could not omit authority files.

## Implemented

- Added a pinned-authority generator and a generated base-flat backflip
  contract with source and local digests.
- Bound the 61D actor, 14D action, 50 Hz control, BAM delay, full-collision
  model, reset populations, spotter, curricula, rewards, flight/landing state,
  termination, and success latches.
- Classified 32 semantic fields. In particular, the 74D versus 90D critic,
  near-zero sampled versus fixed-zero twist, input clipping, contact sensing,
  inherited reward set, mass/inertia operation, RNG, lifecycle, and physics
  differences remain explicit divergences rather than equivalence claims.
- Preregistered 20 ordinary-standing HOME episodes. All virtual force/torque,
  constrained residual authority, reverse-curriculum starts, reference states,
  and environmental supports are disabled. Every episode must complete one
  uninterrupted collision-free backward revolution, recontact feet first,
  remain within joint/torque/integrity limits, and hold the stable state for
  0.5 seconds.
- Added the generated task lock, focused validator, and default runner entry.

## Validation receipts

```text
Backflip semantics verified against pinned authorities.
backflip semantics verified: 61D/14D/50Hz, 32 classified fields,
20 zero-assistance cases
Contract snapshots verified.
```

The BAM-enabled full runner completed with `tous les tests passent`, including
the exact-authority regeneration inside the new focused validator. `git diff
--check` also passed.

## Evidence boundary

No training, policy replay, checkpoint inspection, candidate outcome review,
hardware operation, paid compute, credential use, or publication occurred.
This slice freezes declarations and a future classifier battery; it does not
show a successful backflip, held-out performance, transfer, or physical
authority.
