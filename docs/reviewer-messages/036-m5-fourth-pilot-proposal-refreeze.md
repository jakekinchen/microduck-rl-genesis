# Reviewer Message 036 - M5 fourth-pilot proposal refreeze

**Date:** 2026-09-03

## Decision

**CONTINUE** - accept slice 036 and committed main HEAD `0cbdb4c` relative to
Reviewer-accepted base `7bc61d5` as an exact, fail-closed, non-authorizing
fourth-pilot proposal.

Required corrections: none.

This acceptance makes only the exact committed proposal eligible for a later,
separate Manager decision. It does not authorize provisioning, paid compute,
training, or pilot execution.

## Authority And Commit Chain

- The reviewed chain is exactly
  `7bc61d5 -> d7439f0 -> 04a8fc8 -> 0cbdb4c`.
- Accepted evaluator correction `4a743bb` is the direct ancestor of accepted
  Reviewer HEAD `7bc61d5`.
- Reviewer record
  `docs/reviewer-messages/035-m5-evaluator-bundle-determinism.md` accepts only
  the local determinism correction and permits a later non-authorizing proposal.
- Manager records end at authorization 009. That one-use authority was consumed
  by terminal third-pilot receipt `20260904T030457Z-4qe7ph6p7`; no new Manager
  authority exists.
- `compute_authorized=false`, `manager_authority_present=false`,
  `proposal_grants_compute=false`, and
  `launch_allowed_in_this_proposal=false` are exact bound values.
- The explicit `compute_authorized=true` negative probe fails with
  `compute_authorized must remain false`.
- `<stop-orchestrator/>` remains present in `GOAL.md`.

## Immutable Hash And Source Findings

- Proposal byte SHA-256:
  `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`.
- Proposal semantic SHA-256:
  `692f1d3d884b8e47ef485f0a9eb9974f6e25cb305965f89fe940850367281b5d`.
- Schema byte SHA-256:
  `3de9591c32e40d7bb24114e9e592b6241408332fdc34de6161eaea12d149d027`.
- Pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- CUDA runtime SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- Requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Immutable image remains
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`
  on `linux/amd64`.
- Harness identities remain Genesis training `93cd5f2`, official walking
  `109e06d`, official backflip `8bde27e`, and BAM `62bd8ce`.
- Two independent generations in isolated bare clones produced byte-identical,
  verified bundles:
  - Genesis `7bc61d5`, ref `refs/m5-pilot4/genesis`:
    `e35c912931c1f163ead8c039cb3efce18a3af3319f781ddf3eac201eaf05857f`.
  - Official walking `109e06d`, ref
    `refs/m5-pilot4/official-walking`:
    `0bf67acef9a039536b8d5dc1738260298ea9d08ecddaeaa7fbe6cd0fcbd136bb`.
  - Official backflip `8bde27e`, ref
    `refs/m5-pilot4/official-backflip`:
    `94d0f59fc1c9aa3a23bdc7859a17e6001c8a8c98cef2aeb3dc39d952a37b9246`.
- All source-repository `refs/m5-pilot4/*` namespaces remain empty.
- The official walking checkout has a pre-existing untracked `work/` directory.
  It did not enter the commit-addressed bundle or affect its hash. A later
  Manager must still enforce the proposal's fresh clean-source precondition.

## Resource, Limit, And Execution Findings

Authenticated read-only inventory returned `{"workspaces": null}`. The current
catalog exactly matches the proposed row:

- `hyperstack_A100_80G`, shadeform/hyperstack, x86_64.
- One A100 with 80 GB VRAM, 28 vCPUs, and 120 GiB memory.
- 390-second listed boot time.
- Non-stoppable and non-rebootable.
- `$1.62/hour`.

The proposal binds exactly one workspace named
`microduck-m5-pilot4-20260904`, parallelism one, with no fallback, substitute,
or second workspace. It binds a 4,800-second inner timeout and hard
create-to-delete ceilings of 7,200 seconds, two hours, and `$3.24`.

The executable harness is suite-first. Only after the full authority-enabled
suite passes may these four public-development smokes run:

1. Genesis walking, 64 environments, five iterations, seed 51001.
2. Genesis backflip, 64 environments, five iterations, seed 52001.
3. Official MJLab walking, 64 environments, five iterations, seed 51001.
4. Official MJLab backflip, 64 environments, five iterations, seed 52001.

Each smoke is followed by retention of its named normalized ONNX export.
Candidate seeds, held-out seeds, and the full CUDA matrix remain outside this
proposal.

Any later creation still requires fresh independent acceptance, a new committed
Manager record binding this exact proposal path and SHA-256, exact input hashes,
an immediately preceding empty authenticated inventory, and a freshly matching
catalog row at no more than `$1.62/hour`.

## Receipt, Teardown, And Prohibition Findings

- The receipt Git tree is identical at `7bc61d5` and `0cbdb4c`:
  `a1a44264fe1136ae5ca0228bc95591a7ca173f4c`.
- `git diff --quiet 7bc61d5 -- receipts` passes.
- All eight tracked receipt manifests and 68 immutable logs revalidate.
- The third-pilot manifest remains
  `4bac1d24a78f3940c56dba0785a5721755cd869e3fdc0a78d39ec4ce7797deee`.
- Its retained terminal status remains `terminal_negative`, exit 1,
  `failure_stage=full-suite`, and
  `pilot_smoke_pipeline_completed=false`.
- Every terminal path is required to preserve terminal status, failure stage,
  runtime/source identities, elapsed time, conservative cost, evidence
  boundary, remote sorted `SHA256SUMS`, complete local recovery, and an
  independently regenerated exactly equal local manifest.
- Teardown remains exact-workspace-ID-only after verified recovery on success
  or failure, followed by authenticated empty inventory. The proposed resource
  is non-stoppable, and cleanup requires no additional confirmation.
- The exact 13 prohibitions remain: candidate seeds, held-out seeds, full CUDA
  matrix, publication, policy activation, transfer, physical operation,
  fallback resource, substitute resource, H100, multi-GPU, second workspace,
  and automatic overspend.

## Independent Validation

- `.venv-apple/bin/python scripts/validate_m5_fourth_pilot_proposal.py` - pass.
- `.venv-apple/bin/python tests/test_m5_fourth_pilot_proposal.py` - pass:
  131 scalar mutations, 158 deletions, an extra field, and explicit
  `compute_authorized=true` all rejected.
- Proposal and schema JSON parsing plus their top-level required/property,
  no-extra-field, authority, precondition-count, and prohibition-count
  contract - pass.
- `.venv-apple/bin/python tests/test_m5_experiment_contract.py` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode static` -
  pass.
- `.venv-apple/bin/python tests/test_artifact_contract.py` - pass.
- Authority-enabled `.venv-apple/bin/python tests/run_all.py` with exact BAM
  `62bd8ce`, official walking `109e06d`, locked official MJLab Python, and
  `GS_ENABLE_ZEROCOPY=1` - pass, including both environment smokes.
- `scripts/check_branch_hygiene.sh 7bc61d5` - pass with eight manifests and 68
  immutable logs.
- `scripts/audit_autonomous_workflow.sh` - clean.
- `git diff --check 7bc61d5..HEAD` - pass.
- Closing `brev ls --json` - `{"workspaces": null}`.
- Main worktree is clean at `0cbdb4c`; no Brev resource was created, started,
  executed on, copied to, stopped, deleted, or otherwise mutated during review.

## Claim And Authority Boundary

Slice 036 proves only that the exact fourth-pilot proposal is locally
reproducible, comprehensively bound, fail-closed, and suitable for a later exact
Manager decision.

It proves no CUDA smoke success, M5 completion, task or policy success,
candidate admission, held-out evidence, publication, activation, transfer, or
physical authority. Reviewer acceptance cannot authorize compute.
