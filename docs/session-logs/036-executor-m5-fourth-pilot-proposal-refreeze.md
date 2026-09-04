# Executor Session 036 - M5 fourth-pilot proposal refreeze

**Date:** 2026-09-03

## Baseline And Authority

- Reviewer-accepted base: `7bc61d5`.
- Accepted evaluator-bundle correction: `4a743bb`.
- Reviewer 035 permits a later proposal slice only.
- This slice is local and non-authorizing. No Brev provisioning, training, or
  pilot execution is permitted.

## Live Proposal Evidence

- At `2026-09-04T04:08:56Z`, authenticated `brev ls --json` returned
  `{"workspaces": null}`.
- The fresh read-only A100 catalog query returned
  `hyperstack_A100_80G`, shadeform/hyperstack, x86_64, one A100 with 80 GB
  VRAM, non-stoppable, non-rebootable, at `$1.62/hour`.
- No Brev mutation was issued.

## Work In Progress

## Deterministic Source-Bundle Freeze

Ordinary default `git bundle create` was tested twice and produced different
bytes for the same Genesis and official-walking refs. The proposal therefore
binds `pack.threads=1`, `pack.windowMemory=64m`, a unique temporary ref for each
source, and deletion of only that ref after verified bundle creation.

Two independent generations were byte-identical and passed `git bundle
verify`:

- `genesis.bundle`, ref `refs/m5-pilot4/genesis`, source `7bc61d5`, SHA-256
  `e35c912931c1f163ead8c039cb3efce18a3af3319f781ddf3eac201eaf05857f`.
- `official-walking.bundle`, ref `refs/m5-pilot4/official-walking`, source
  `109e06d4`, SHA-256
  `0bf67acef9a039536b8d5dc1738260298ea9d08ecddaeaa7fbe6cd0fcbd136bb`.
- `official-backflip.bundle`, ref `refs/m5-pilot4/official-backflip`, source
  `8bde27e`, SHA-256
  `94d0f59fc1c9aa3a23bdc7859a17e6001c8a8c98cef2aeb3dc39d952a37b9246`.

All temporary refs were deleted after the check. Bundles remain local proposal
evidence only; nothing was copied to Brev.

## Proposal And Validator

- Proposal: `experiments/m5/fourth-pilot-proposal-v1.json`, byte SHA-256
  `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`.
- Executor implementation commit: `04a8fc8` (opening commit `d7439f0`).
- The semantic validator binds the entire proposal, its schema, exact local
  harness/runtime/lock bytes, accepted commits, suite-first harness order,
  resource/price/time/cost consistency, receipt behavior, teardown, and
  authority state.
- Negative probes reject 131 scalar mutations, 158 deletions, an extra field,
  and an explicit `compute_authorized=true` mutation.
- The proposal binds one unique `microduck-m5-pilot4-20260904` workspace, the
  exact A100 row, immutable image, a 4,800-second inner timeout, two-hour /
  `$3.24` create-to-delete ceilings, no fallback, all four public-development
  64x5 smokes only after the suite, normalized ONNX retention, terminal
  receipts, independent manifest equality, exact-ID deletion, and empty
  inventory.

## Validation

- Dedicated validator and all proposal negative probes: pass.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- M5 immutable experiment, CUDA runtime, artifact-attestation, Python
  compilation, and diff checks: pass.
- `scripts/check_branch_hygiene.sh 7bc61d5`: pass with eight manifests and 68
  immutable receipt logs.
- Every tracked receipt manifest revalidated, and `git diff --quiet 7bc61d5 --
  receipts` passes.
- Autonomous workflow audit: clean.
- No temporary `refs/m5-pilot4/*` remain.

## Evidence And Authority Boundary

This is a proposal only. `compute_authorized=false`; no Manager authority is
present, and no Brev create/start/exec/copy/stop/delete or training action
occurred. Candidate, held-out, full CUDA matrix, publication, activation,
transfer, and physical work remain prohibited. Independent Reviewer acceptance
may make the exact proposal eligible for a later Manager decision, but cannot
authorize the pilot.

## Step-9 Flags For Reviewer

- Recompute the proposal, schema, harness, runtime, and requirements hashes.
- Exercise the full mutation suite and confirm `compute_authorized=true` fails
  with the explicit authority error.
- Confirm every catalog/resource/limit/execution/receipt/teardown/prohibition
  field is exact and the bundle hashes are tied to deterministic generation.
- Re-run the full authority-enabled local suite, receipt manifests, branch
  hygiene from `7bc61d5`, and workflow audit.
- Leave the stop sentinel in place. Do not create a Manager authorization or a
  Brev workspace.
