# Reviewer Message 026 - M5 CUDA pilot contract amendment

**Date:** 2026-09-03

## Decision

`REDIRECT` - pilot gate: **NO-GO**.

Paid pilot provisioning is **not allowed** from commit `beab439`. No Brev
workspace may be created until a corrected amendment receives a new independent
Reviewer `GO`.

## Evidence Reviewed

- Commit `beab4398fbc521ca104ab10855c7455e1d791e0f` is cleanly isolated in the
  detached Reviewer worktree; the main checkout is clean at the same commit and
  is 63 commits ahead of `origin/main`.
- Live registry inspection with
  `docker manifest inspect --verbose nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04`
  reports linux/amd64 digest
  `sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.
  This exactly matches the contract. The separate linux/arm64 digest is
  `sha256:896404f46031d244ea5ac1d82990e524c978ee62117510cef23ecdb037ace516`.
- Authenticated `brev search --gpu-name A100 --sort price --json` currently
  reports `hyperstack_A100_80G` as x86_64, one A100 80 GB, non-stoppable, and
  $1.62/hour. Therefore the frozen 2-hour pilot arithmetic is exactly $3.24;
  104 hours at this snapshot is $168.48 and remains below the separate $210
  full-run ceiling.
- Authenticated `brev ls --json` returned `{"workspaces": null}`. No Brev
  resource was created, changed, stopped, or deleted during review.
- Focused external-authority contract validation passed and regenerated a
  byte-identical 32-row matrix. Every row remains `planned_not_executed`;
  candidate/held-out execution remains false.
- The full repository runner passed. It displayed five explicit BAM-dependent
  skips because `BAM_REPO` was not supplied; held-out preregistration,
  success-classifier fixtures, terminal official-policy absence, Apple runtime
  checks, and the remaining suites passed.
- `scripts/audit_autonomous_workflow.sh` was clean. Branch hygiene passed at
  base `beab439^` with one receipt manifest and eight immutable raw logs.
  `git diff --check beab439^...beab439` passed.

## Blocking Findings

- `100` - the frozen provisioning command does not use the immutable container.
  It is only
  `brev create microduck-m5-pilot-20260903 --type hyperstack_A100_80G`.
  `brev create --help` confirms container execution requires container mode and
  `--container-image`; neither the digest reference nor an exact digest-pull/run
  startup path is present. The verified digest is therefore descriptive, not
  the execution identity of the paid pilot.
- `100` - the frozen Brev provider binding disagrees with the authenticated
  catalog. The live row reports `cloud: hyperstack` and `provider: shadeform`,
  while the contract asserts `provider: hyperstack`. The type, GPU, architecture,
  stoppability, and price match, but the field claimed as provider does not.
- `100` - the operational safety envelope is not fail-closed in the semantic
  validator. Independent mutation probes were accepted after removing all
  recovery/checksum rules, removing all pilot contents, replacing provisioning
  with `true`, removing the one-workspace requirements, removing the independent
  full-run review condition, replacing registry inspection with `true`, and
  changing the human-readable image tag to `latest`. Platform and teardown
  mutations were rejected, so the failure is specific and reproducible.
- `75` - the JSON Schema does not define the resource/container amendment and no
  schema validator is invoked by the repository checks. The lock detects an
  unreviewed byte change to the current files, but it does not provide semantic
  protection when a future amendment and its lock are regenerated together.
  The committed negative tests also omit recovery, one-workspace, launch,
  full-run condition, inspection-command, tag, platform, and teardown probes.

## Preserved Gates

The amendment continues to bind `official_policy_authority_missing`, the
unrealized held-out protocol, false candidate/held-out authority, all 32
unexecuted experiment rows, and the infrastructure-only evidence boundary.
Nothing reviewed establishes task success, accepts an M6 artifact, approves or
activates a policy, grants held-out access, or grants physical authority.

## Required Correction

The next Executor slice should bind an exact linux/amd64 container launch path
to the immutable digest; reconcile Brev `cloud` versus `provider`; encode an
empty-inventory/single-workspace precondition with no fallback; freeze exact
pilot, recovery, independent checksum, deletion, and full-run-review semantics;
and make those semantics schema- and validator-enforced with negative probes.
The corrected commit must rerun the focused contract check, full suite, workflow
audit, branch hygiene, live registry inspection, and authenticated read-only
Brev inventory/catalog checks before independent review.

## Terminal Boundary

The image digest, A100 type, non-stoppable behavior, $1.62/hour snapshot,
2-hour/$3.24 pilot ceiling, conditional 104-hour/$210 full ceiling, empty live
inventory, and preserved policy/held-out/physical gates are verified. The paid
pilot remains **NO-GO** because the execution path is not digest-bound and the
one-workspace/recovery/full-review rules can be removed without semantic
validation failure.
