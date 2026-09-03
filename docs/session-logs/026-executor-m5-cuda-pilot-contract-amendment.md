# Executor log 026 - M5 CUDA pilot contract amendment

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/026-m5-cuda-pilot-contract-amendment.md`

## Implemented

- Removed the stale stop sentinel and replaced the old no-spend/no-publication
  boundary with dated Manager authorization while retaining every evaluator,
  provenance, held-out, deployment, safety, and physical gate.
- Resolved the official NVIDIA CUDA 12.8.1 cuDNN development Ubuntu 24.04 image
  tag to the linux/amd64 manifest digest
  `sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.
- Amended the immutable M5 contract for a pilot only: one non-stoppable Brev
  `hyperstack_A100_80G`, $1.62/hour snapshot, two-hour/$3.24 ceiling, and exact
  recovery/checksum/deletion requirements.
- Preserved all 32 development/candidate rows as `planned_not_executed` and
  explicitly kept candidate and held-out execution unauthorized.
- Added fail-closed checks for image digest/platform, Manager authority,
  Reviewer precondition, resource type/provider/GPU, non-stoppable semantics,
  pilot/full cost ceilings, candidate authority, workspace identity, and
  teardown behavior.

## Immutable image evidence

The local Docker registry inspection command was:

```bash
docker manifest inspect --verbose \
  nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04
```

It returned separate linux/arm64 and linux/amd64 descriptors. The contract
binds the linux/amd64 descriptor only; its digest is the value above. The
human-readable tag is retained for audit readability but is never the execution
identity.

## Verification

```bash
.venv-apple/bin/python scripts/validate_m5_experiment.py \
  --matrix-output /tmp/microduck-m5-matrix-026.json
cmp -s /tmp/microduck-m5-matrix-026.json \
  experiments/m5/execution-matrix-v1.json
.venv-apple/bin/python tests/test_m5_experiment_contract.py
.venv-apple/bin/python -m json.tool experiments/m5/contract-v1.json
.venv-apple/bin/python -m json.tool experiments/m5/contract-v1.schema.json
.venv-apple/bin/python -m json.tool experiments/m5/contract-v1.lock.json
.venv-apple/bin/python tests/run_all.py
bash scripts/audit_autonomous_workflow.sh
bash scripts/check_branch_hygiene.sh
brev ls --json
git diff --check
```

All focused checks passed. The generated dry-run remained byte-identical to the
committed 32-row matrix. The full repository runner passed; its four explicit
BAM/evaluator skips are the expected consequence of the optional BAM checkout
not being supplied to this local command, not silent passes. Workflow and branch
hygiene passed. Authenticated Brev inventory returned `{"workspaces": null}`.

## Evidence boundary and spend

This slice created no Brev workspace and incurred no paid compute. It provides
immutable pilot infrastructure authority only. An independent Reviewer `GO` on
the committed amendment is still required before provisioning. No candidate,
held-out input, real policy, task-success result, publication, activation, or
physical action was executed or promoted.
