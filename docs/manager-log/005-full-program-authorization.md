# Manager authorization 005 - bounded M5 through physical program

**Date:** 2026-09-03

## Authority received

The user explicitly authorizes the Manager to continue the frozen program from
commit `9b64c57`, including bounded paid CUDA/Brev compute, authenticated
artifact retrieval and required reviewed publication, candidate execution and
evaluation, and staged physical validation only after all preceding evaluator,
artifact, deployment, and safety gates pass.

This dated authorization replaces the stale no-authority constraints and stop
sentinel formerly present in `GOAL.md`. It does not waive proof gates, promote
missing provenance, realize held-out data early, approve a policy, or authorize
unsafe physical operation.

## Compute envelope

- One workspace only.
- Requery Brev price and availability immediately before creation.
- Prefer `hyperstack_A100_80G`: one A100 80 GB, $1.62/hour snapshot,
  non-stoppable.
- Pilot ceiling: 2 hours and $3.24.
- Full frozen CUDA seed envelope: only after an independent Reviewer accepts
  the pilot; 104 GPU-hours and $210 total ceiling.
- No H100, multi-GPU, second workspace, or automatic extension/overspend.

Because the preferred workspace is non-stoppable, teardown means deletion.
Before deletion, recover every unique checkpoint, normalized ONNX, normalizer,
training/evaluator output, log, manifest, and `SHA256SUMS`; verify remote and
local checksums independently; then delete and confirm `brev ls --json` shows no
paid workspace.

## Ordered authority gates

1. Amend and independently review the M5 contract with an immutable
   linux/amd64 CUDA image digest and exact pilot/full resource envelope.
2. Run one bounded paid pilot covering hardware/CUDA/Warp/MuJoCo smoke checks,
   the applicable suite, and frozen 64-environment x 5-iteration walking and
   backflip smokes with retained artifacts and exact cost receipts.
3. Independently review the pilot before starting full candidate compute.
4. Close official-mjlab walking-policy provenance from a frozen project source,
   checkpoint, exporter, normalizer, and immutable manifest before designating
   or executing it as the official reference.
5. Preserve the preregistered M5 transition budgets, seeds, checkpoints,
   evaluator, and held-out timing. Candidate compute authority does not permit
   early held-out realization.
6. Admit and publish only independently reviewed M6/M7 artifacts. Proceed to
   physical validation only through explicit prerequisite, deployment, safety,
   and receipt gates.

## Required durable evidence per slice

Each slice requires an updated `GOAL.md`/`TRAINING_ACTUALIZATION.md` state, an
Executor log, a scoped commit, an independent Reviewer decision, verification
commands, cost/proof receipts where applicable, and a terminal boundary that
does not overclaim task success, transfer, publication, activation, or physical
acceptance.
