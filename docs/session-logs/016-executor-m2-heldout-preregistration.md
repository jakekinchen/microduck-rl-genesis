# Executor log 016 - M2 held-out preregistration

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/016-m2-heldout-preregistration.md`

## Implemented

- Bound the visible suites, public acceptance definition, evaluator, task,
  model, and BAM inputs into an unrealized held-out protocol.
- Explicitly marked the already-public acceptance seeds as not held-out.
- Defined post-candidate-freeze seed derivation from a future NIST Randomness
  Beacon value, including ordering, collision rejection, and initial-state
  derivation.
- Added synthetic tests for deterministic derivation and rejection of malformed
  or pre-freeze beacon values.

## Evidence boundary

No live beacon or final candidate was inspected. No held-out seed or case was
realized or executed, and task success remains unevaluated.
