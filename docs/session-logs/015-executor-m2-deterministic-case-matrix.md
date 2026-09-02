# Executor log 015 - M2 deterministic case matrix

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/015-m2-deterministic-case-matrix.md`

## Implemented

- Froze ten visible cases spanning all nine required infrastructure families.
- Extended the evaluator with deterministic initial joint offsets, geometry
  friction scaling, body-wrench schedules, joint-margin measurement, fail-closed
  non-finite rejection, synthetic deadline-path injection, and root-height
  termination.
- Added matrix validation that forbids candidate policies and acceptance-seed
  overlap and requires exactly one expected outcome per case.

## Evidence boundary

Every run uses the retained zero-output policy and remains
`infrastructure_only`, `held_out: false`, and `task_success: not_evaluated`.

## Validation

Two complete matrix runs produced byte-identical reports across ten cases. Core
and bundle regression tests passed. The retained core report changed only in
its self-binding evaluator-source digest; its trajectory and classification did
not change. The BAM-enabled broad runner completed with `tous les tests
passent`; contract freeze and `git diff --check` passed.
