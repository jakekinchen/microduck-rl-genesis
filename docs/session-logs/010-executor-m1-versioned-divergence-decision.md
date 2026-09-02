# Executor log 010 - M1 versioned divergence decision

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/010-m1-versioned-divergence-decision.md`

## Implemented

- Added a deterministic local decision generated directly from the frozen
  walking and backflip semantic inventories.
- Bound both task paths, SHA-256 digests, official commits, and inventory
  counts.
- Disposed all 45 non-exact fields: 25 accepted semantic equivalences, four
  deferred implementation reconciliations, three evaluator normalizations,
  eight independent-evaluator boundaries, and five training-only
  non-equivalences.
- Added explicit failure for a new unclassified versioned divergence or a stale
  mapping after a divergence disappears.
- Recorded the chosen path as `versioned_local_divergence` with status
  `recorded_local_not_submitted`. Both upstream submission and publication are
  false, matching the active authority boundary.
- Added the decision schema, generated lock, focused validator, and default
  runner entry.

## Validation receipts

```text
Divergence decision verified: 45 non-exact fields.
versioned divergence decision verified: 45 non-exact fields,
local and not submitted
Contract snapshots verified.
```

The BAM-enabled full runner completed with `tous les tests passent` and `git
diff --check` passed.

## Evidence boundary

No upstream submission, push, publication, training, candidate evaluation,
hardware operation, paid compute, or credential use occurred. The decision
documents compatibility scope; it is not task success, held-out evidence,
transfer evidence, or physical authority.
