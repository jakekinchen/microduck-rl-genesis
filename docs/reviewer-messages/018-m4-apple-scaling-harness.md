# Reviewer Message 018 - M4 Apple scaling harness

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commit `05c05e3` adds the Metal/MPS one-size worker, stable JSON
  schema, five-row assembler, SHA-256 manifest writer, and deterministic tests.
- Focused schema/default tests pass from the Apple environment.
- Branch hygiene passes and the post-commit worktree is clean.

## Findings

The worker measures a real PPO collection and learner update rather than only
physics throughput. It binds every completed row to a clean commit and records
the required memory proxy, thermal method limitations, finiteness, devices,
packages, and non-serial machine identity. The implementation does not select
an everyday default and makes no task-success claim.

## Milestone State

M4 remains active. The harness implementation is accepted; the clean-commit
five-size sweep, sustained slice, and CPU+MPS fallback characterization remain.

## Next Slice

Proceed to `docs/briefs/019-m4-apple-scaling-sweep.md`.
