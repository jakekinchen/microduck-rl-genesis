# Slice Brief 044 - M5 seventh-pilot reliability proposal

**Date:** 2026-09-04

## Objective

Diagnose the fourth/fifth/sixth Brev readiness failures, report the
nonsecret control-plane race to Brev, and freeze one local-only seventh-pilot
proposal using a previously unused single-A100 provider/type with a stronger
readiness protocol. Do not create paid compute.

## Selection Boundary

- Preserve the sixth pilot as terminal negative; do not retry
  `hyperstack_A100_80G`, `massedcompute_A100_sxm4_80G_DGX`, or
  `a2-highgpu-1g:nvidia-tesla-a100:1`.
- Select one previously unused x86_64, single-GPU, non-H100 type from a
  different provider with practical disk and stoppability where available.
- Require an exact immutable-container dry run and empty authenticated
  inventory. Do not create a workspace.

## Readiness Protocol

- Treat catalog boot time as an estimate only, never a shell-ready deadline.
- Bind an explicit 900-second create-to-shell-readiness window inside the
  global 7,200-second create-to-delete ceiling.
- Require three consecutive authenticated polls, at least 15 seconds apart,
  each reporting the exact workspace with build `COMPLETED`, shell `READY`,
  health `HEALTHY`, and a running state.
- After the three polls, require a successful no-op remote shell command and a
  separate successful free-disk probe showing at least 8 GiB before upload.
- Any regression resets the consecutive-poll count. Failure to close every
  readiness gate within 900 seconds is a terminal provisioning/connectivity
  negative, followed by receipt recovery and exact-ID teardown.

## Acceptance Criteria

- Machine-readable schema, semantic validator, and mutation tests bind the
  accepted terminal chain, exact catalog row/rate/image/inputs, source bundles,
  readiness state machine, suite-first harness, limits, prohibitions, receipt,
  and teardown behavior.
- Full local validation, mutation, manifest, immutable-log, branch, workflow,
  and final empty-inventory gates pass.
- Executor commits the proposal and independent Reviewer records a decision.
- Restore `<stop-orchestrator/>` at a fresh Manager boundary.

## Evidence Boundary

This slice proves only a local non-authorizing proposal and a sent reliability
report. It proves no future shell readiness, CUDA compatibility, task or policy
success, candidate or held-out result, publication, activation, transfer, or
physical authority.
