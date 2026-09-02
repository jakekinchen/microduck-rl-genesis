# Executor log 014 - M2 pinned BAM materializer

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/014-m2-pinned-bam-materializer.md`

## Implemented

- Added one repo-owned BAM materializer that reads the exact repository and
  commit from the frozen contract, fetches the commit directly, detaches at it,
  and verifies origin, HEAD, and cleanliness.
- Existing dirty or wrong-origin destinations fail closed.
- Replaced current branch-clone guidance in README, test documentation, and the
  official-mjlab setup handoff.
- Added a local-git regression that materializes a commit, moves the branch,
  materializes again, and proves HEAD and content remain at the original commit.

## Evidence boundary

No fixture or evaluator artifact was regenerated or repinned. No policy,
candidate, credential, paid compute, publication, activation, or hardware
action was used.

## Validation

- Moved-branch regression passed.
- Fresh materialization resolved exactly
  `62bd8ce12154340be97e06f7f41a0ca8f116d967` with a clean worktree.
- Evaluator core and deterministic bundle tests passed against that checkout.
- Contract freeze and `git diff --check` passed.
