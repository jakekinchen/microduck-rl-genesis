# Executor log 023 - M5 immutable experiment contract

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/023-m5-immutable-experiment-contract.md`

## Implemented

- Added the blocked preregistration contract and schema for walking/backflip
  Genesis Metal/MPS versus official mjlab/CUDA.
- Bound exact Genesis `93cd5f2`, official walking `109e06d`, official backflip
  `8bde27e`, and BAM `62bd8ce` authorities plus task, model, interface,
  reward/DR source, exporter, environment, evaluator, suite, classifier, and
  unrealized held-out hashes.
- Froze the complete actor/critic/PPO configuration, 3 public development and
  5 candidate-comparison seeds per task, transition-equal budgets, seven
  predetermined checkpoint/export transitions, metrics, non-inferiority,
  variance, abort, artifact, checksum, and resume rules.
- Added a 32-row non-executing matrix and fail-closed validator with external
  exact-git-blob verification.
- Added a proposal-only single A100 estimate from the 2026-09-03 Brev search:
  stoppable `a100-80gb.1x` at a $1.98/hour snapshot, two-hour pilot ceiling
  ($3.96), and 104-hour full CUDA ceiling ($205.92). Price must be requeried;
  this is not provisioning authority.

## Verification

- Positive contract validation passed against both exact external repositories.
- Dry-run generated exactly 32 `planned_not_executed` rows, no held-out seeds,
  and `resource_authorized: false`.
- Negative probes rejected source drift, development/candidate seed overlap,
  unequal transition budgets, late checkpoint mutation, missing evaluator
  binding, and compute authorization mutation.
- Python compilation, JSON parsing, and `git diff --check` passed.

## Evidence boundary

Experiment infrastructure only. No task code was imported by the dry-run; no
policy, development seed, candidate seed, held-out seed, training, evaluation,
Brev provisioning, credential use, publication, activation, or hardware action
occurred. `official_policy_authority_missing`, immutable CUDA container digest,
and explicit compute authorization remain blocking.
