# Reviewer Message 037 - M5 fourth CUDA pilot

**Date:** 2026-09-04

## Decision

**CONTINUE** - accept slice 037 and committed main HEAD `922b0ec` strictly as
a complete terminal-negative fourth-pilot provisioning-health receipt with
verified teardown.

Required corrections: none.

This accepts neither CUDA pipeline compatibility nor a successful smoke pilot
or M5 completion. Manager authorization 010 is consumed. This decision
authorizes no retry, replacement workspace, full CUDA execution, candidate or
held-out execution, publication, policy activation, transfer, or physical
operation.

## Authority And Immutable Inputs

- The direct reviewed chain is exactly `125493c -> 929dc6b -> 922b0ec`.
- `929dc6b` committed Manager authorization 010 before the create anchor at
  `2026-09-04T04:41:36Z`.
- Accepted evaluator correction `4a743bb` remains an ancestor of accepted
  Reviewer HEAD `7bc61d5`.
- The fourth-pilot proposal, schema, validator, harness, runtime contract, and
  requirements lock are unchanged from accepted proposal review `125493c`.
- Locally recomputed hashes match:
  - proposal byte SHA-256:
    `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`
  - proposal semantic SHA-256:
    `692f1d3d884b8e47ef485f0a9eb9974f6e25cb305965f89fe940850367281b5d`
  - harness SHA-256:
    `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`
  - runtime contract SHA-256:
    `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`
  - requirements lock SHA-256:
    `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`
- The receipt's three source-bundle hashes exactly match the immutable accepted
  proposal and Manager authorization:
  - Genesis `7bc61d5`:
    `e35c912931c1f163ead8c039cb3efce18a3af3319f781ddf3eac201eaf05857f`
  - official walking `109e06d`:
    `0bf67acef9a039536b8d5dc1738260298ea9d08ecddaeaa7fbe6cd0fcbd136bb`
  - official backflip `8bde27e`:
    `94d0f59fc1c9aa3a23bdc7859a17e6001c8a8c98cef2aeb3dc39d952a37b9246`
- The proposal remains non-authorizing: `compute_authorized=false`,
  `manager_authority_present=false`, `proposal_grants_compute=false`, and
  `launch_allowed_in_this_proposal=false`. Execution authority existed only in
  consumed Manager record 010.

## Workspace And Terminal Classification

- The evidence records exactly one authorized workspace:
  - name: `microduck-m5-pilot4-20260904`
  - ID: `tpo91g7kj`
  - type: `hyperstack_A100_80G`
  - provider/cloud: shadeform/hyperstack
  - architecture: x86_64
  - GPU: one A100 with 80 GB VRAM
  - price snapshot: `$1.62/hour`
- Its terminal observation at `2026-09-04T04:51:51Z` was `UNHEALTHY`,
  `BUILDING`, `NOT READY`, with no ready shell.
- `terminal_negative` at failure stage `workspace-provisioning-health` is the
  correct classification.
- No file was uploaded. `harness_invocations=0`, `suite_started=false`,
  `training_started=false`, and `pilot_smoke_pipeline_completed=false`.
- No repository suite, walking or backflip smoke, checkpoint, normalized ONNX
  export, candidate seed, held-out seed, or full CUDA row was executed.
- Because no shell ever became ready and the harness was never invoked, no
  remote receipt or remote `SHA256SUMS` could exist.
  `REMOTE_RECEIPT_UNAVAILABLE.txt` records that limitation honestly; no
  remote/local manifest-equivalence claim is fabricated.

## Local Receipt Integrity

- `receipts/m5/pilot/20260904T044136Z-tpo91g7kj/` contains 13 files total: 12
  payload files plus `SHA256SUMS`.
- Every manifest entry verifies.
- The manifest path set exactly equals all receipt files other than the
  manifest itself and is sorted by path.
- The independently recomputed manifest SHA-256 is
  `89bdd479d62a4a96b96cb00f161d232cb36717ba938e9a63c09fac622df24c70`.
- From `2026-09-04T04:41:36Z` through the first authenticated empty inventory
  at `2026-09-04T04:53:49Z` is exactly 733 seconds.
- At `$1.62/hour`, `733 × 1.62 / 3600 = $0.329850`. This is a conservative
  estimate, not a provider invoice, and is below the 7,200-second and `$3.24`
  ceilings.

## Teardown And Accepted-Receipt Immutability

- Exact-ID deletion targeted only `tpo91g7kj` at
  `2026-09-04T04:52:59Z`.
- The control plane showed `DELETING`, then anomalously regressed to `STARTING`;
  the exact-ID retry subsequently reported that the workspace no longer
  existed.
- Authenticated inventory was first empty at `2026-09-04T04:53:49Z`, remained
  empty through five additional recorded polls, and a fresh independent
  `brev ls --json` again returned `{"workspaces": null}`.
- No Brev workspace remains.
- `git diff 125493c..922b0ec -- receipts` contains additions only under the new
  fourth-pilot receipt path. Previously accepted receipts were not modified.
- Branch hygiene revalidated nine manifests and 68 immutable logs.

## Independent Validation

The autonomous workflow evidence gates and Brev cost-control check were applied
read-only. No repository edit, remote execution, provisioning, retry, training,
or resource mutation occurred during review.

- `.venv-apple/bin/python scripts/validate_m5_fourth_pilot_proposal.py` - pass.
- `.venv-apple/bin/python tests/test_m5_fourth_pilot_proposal.py` - pass: 131
  scalar mutations, 158 deletions, an extra field, and explicit compute
  authority were rejected.
- `.venv-apple/bin/python tests/test_m5_experiment_contract.py` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode static` -
  pass.
- `.venv-apple/bin/python tests/test_artifact_contract.py` - pass without
  execution.
- Receipt `shasum -a 256 -c SHA256SUMS` - all 12 entries pass.
- Independent manifest path-set, path-order, file-count, and SHA-256 checks -
  pass.
- `scripts/check_branch_hygiene.sh 929dc6b` - pass with nine manifests and 68
  immutable logs.
- `scripts/audit_autonomous_workflow.sh` - clean.
- `git diff --check 929dc6b..922b0ec` - pass.
- Accepted-input immutability and prior-receipt-only-addition checks - pass.
- Independent timestamp and decimal cost arithmetic - exactly 733 seconds and
  `$0.329850`.
- Closing `brev ls --json` - `{"workspaces": null}`.
- Main worktree is clean at `922b0ec`; `main` is 104 commits ahead and zero
  behind `origin/main`.

## Claim, Authority, And Stop Boundary

Slice 037 proves only that the single authorized fourth-pilot workspace reached
a terminal provisioning-health failure and was removed with a locally
self-checking control-plane receipt.

It proves no CUDA runtime or pipeline compatibility, smoke success, M5
completion, task or policy success, candidate admission, held-out performance,
publication, activation, transfer, or physical authority.

Manager authorization 010 is consumed and cannot be reused. No retry,
substitute, fallback, second workspace, or full CUDA execution is authorized.
Any later paid compute would require a new independently reviewed proposal and
fresh exact Manager authorization.

Retain `<stop-orchestrator/>` in `GOAL.md`.
