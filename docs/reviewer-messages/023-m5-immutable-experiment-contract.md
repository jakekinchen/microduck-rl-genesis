# Reviewer Message 023 - M5 immutable experiment contract

**Date:** 2026-09-03

## Decision

`CONTINUE`

## Evidence Reviewed

- Commit `b2a1ab6` adds a digest-locked M5 contract, schema, 32-row dry-run
  matrix, external exact-git-blob validation, six negative probes, and Executor
  log.
- Exact local and external authorities validate at Genesis `93cd5f2`, walking
  `109e06d`, backflip `8bde27e`, and BAM `62bd8ce`.
- The dry-run includes no held-out seed, reports every row
  `planned_not_executed`, and reports `resource_authorized: false`.
- The full local suite, contract freeze, branch hygiene, and workflow audit
  pass. Authority-dependent BAM tests retain explicit skips.

## Findings

The contract freezes full network/PPO configuration, seed sets, equal transition
budgets, checkpoint/export schedule, evaluator inputs, task metrics, decision
rules, terminal failures, artifact layout, and resumability. The current Brev
price/runtime estimate is bounded and explicitly proposal-only.

`official_policy_authority_missing`, the absent immutable CUDA container digest,
and explicit CUDA-spend authorization remain blocking. No policy or seed was
executed and no resource was created.

## Milestone State

The M5 contract/preflight sub-gate is accepted. M5 execution remains blocked.
Proceed only with M6 foundations that use synthetic fixtures and do not depend
on trained candidates, publication, credentials, or activation.

## Next Slice

Proceed to `docs/briefs/024-m6-manifest-attestation-schemas.md`.
