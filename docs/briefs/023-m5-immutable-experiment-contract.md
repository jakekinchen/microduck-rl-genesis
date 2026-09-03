# Slice Brief 023 - M5 immutable experiment contract

**Date:** 2026-09-03

## Objective

Freeze a machine-validated, non-executing cross-backend experiment contract for
walking and backflip before any development or candidate seed runs.

## Acceptance Criteria

- Bind exact Genesis, official walking, official backflip, BAM, task, model,
  interface, reward/DR source, exporter, environment, evaluator, development
  suite, case matrix, and unrealized held-out protocol authorities.
- Freeze the complete actor/critic/PPO configuration, public development and
  candidate-comparison seeds, equal per-backend transition budgets,
  predetermined transition checkpoints, normalized ONNX export schedule,
  metrics, non-inferiority/variance rules, failures, artifact layout,
  resumability, and evidence boundary.
- Include a current bounded single-A100 Brev estimate and teardown/recovery
  proposal that is explicitly not provisioning authority.
- Deterministic validation rejects drift, seed overlap, unequal transition
  budgets, missing/late checkpoints, and unbound evaluator inputs.
- A dry-run emits the complete execution matrix without importing task code,
  training, evaluating, realizing held-out seeds, or creating compute.

## Stop Conditions

- Do not execute any policy, development seed, candidate seed, or held-out case.
- Do not provision Brev, use credentials, publish, push, activate a policy, or
  operate hardware.
- Preserve `official_policy_authority_missing` as a blocking candidate-admission
  gate; do not substitute a Genesis or structurally compatible artifact.

## Evidence Boundary

Preregistered experiment infrastructure only. No performance, task-success,
held-out, transfer, publication, activation, or physical evidence.
