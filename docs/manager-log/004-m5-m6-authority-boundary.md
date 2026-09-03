# Manager escalation 004 - M5/M6 authority boundary

**Date:** 2026-09-03

## Classification

`missing_input` + `cost_or_permission`, evidence anchor `100`.

## Exact remaining gates

1. Obtain an upstream/project-owned immutable manifest or reproducible
   checkpoint/export chain resolving every item in
   `official_policy_authority_missing`; do not execute the current structurally
   compatible walking ONNX as an official reference.
2. Amend and re-review the M5 contract with an immutable CUDA container digest.
3. Obtain explicit user authority immediately before any paid CUDA/Brev action.
4. For real M6 intake, bind ONNX, normalizer, checkpoint, exporter, model, BAM,
   task, evaluator, evidence, and file-level license bytes. Resolve or retain
   terminal negatives for the three existing weights, two media files,
   `ball.xml`, and the actuator parameter source path.
5. Publication, policy approval/activation, held-out realization, and physical
   operation each require their own later authority boundary.

## Current acceptance commands

```bash
.venv-apple/bin/python scripts/validate_m5_experiment.py \
  --matrix-output /tmp/microduck-m5-matrix.json
.venv-apple/bin/python scripts/generate_provenance_inventory.py --check
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/official --source-class official
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/community --source-class community
.venv-apple/bin/python tests/run_all.py
bash scripts/audit_autonomous_workflow.sh
bash scripts/check_branch_hygiene.sh
```

These commands validate only the frozen contract and synthetic/local evidence.
They do not authorize a seed run, real artifact acceptance, held-out realization,
publication, activation, or hardware.

## Proposed CUDA resource envelope - not authorized

- Requery: `brev search --gpu-name A100 --sort price --json`.
- Current snapshot: stoppable Crusoe `a100-80gb.1x`, one A100 80 GB, $1.98/hour
  on 2026-09-03.
- Pilot ceiling after authority: 2 hours / $3.96.
- Full official CUDA seed envelope after pilot review: 104 hours / $205.92.
- One workspace only. Stop at any runtime/cost, integrity, receipt, or contract
  gate; no automatic extension.

## Recovery and teardown

Before shutdown, copy checkpoint, normalized ONNX, normalizer, training metrics,
evaluator outputs, logs, manifests, and `SHA256SUMS` to the local run-scoped
receipt. Verify remote and local manifests independently. Then:

```bash
brev stop <workspace>
brev delete <workspace>
brev ls --json
```

Delete only after verified recovery and only when no unique remote state
remains. The final inventory must show no paid workspace.
