# Executor Session 038 - M5 fifth-pilot replacement-provider proposal

**Date:** 2026-09-04

## Baseline And Authority

- Reviewer-accepted base: `957499a` and Reviewer 037.
- The fourth pilot remains a terminal provisioning-health negative; Manager
  authorization 010 is consumed and cannot be reused.
- This is proposal-only local work. No paid resource or training authority is
  active.

## Live Proposal Evidence

- At `2026-09-04T05:07:30Z`, authenticated `brev ls --json` returned
  `{"workspaces": null}`.
- A fresh read-only catalog returned exact type
  `massedcompute_A100_sxm4_80G_DGX`: shadeform/massedcompute, x86_64, one A100
  80 GB, 16 vCPUs, 160 GiB RAM, non-stoppable, non-rebootable, 390-second boot
  listing, at `$1.656/hour`.
- The exact proposed `brev create` command with container mode, immutable CUDA
  digest, one instance, parallelism one, and `--dry-run` exited successfully
  and returned only `massedcompute_A100_sxm4_80G_DGX`.
- No Brev mutation occurred.

## Work In Progress

## Deterministic Source-Bundle Freeze

Each exact source was bundled twice using the proposal's unique
`refs/m5-pilot5/*` ref, `pack.threads=1`, and `pack.windowMemory=64m`. Both
generations were byte-identical and passed `git bundle verify`:

- Genesis `7bc61d5`:
  `399b03e878002aeaf1aaa0bdf56efafedaebf337b88d78ba80aaf5af50d97eba`.
- Official walking `109e06d`:
  `9937de2c47bbfaa8dee1a21e99728102164b416fa174ec0d107fee77c42fd4a6`.
- Official backflip `8bde27e`:
  `98e4642fd75b4b3f670391e679f788f8c722bc49d8c7ab27418d68efba8a207e`.

The hashes differ from the fourth-pilot bundle bytes because the unique bundle
ref names are part of the files. All temporary refs were removed. No bundle was
uploaded.

## Proposal And Validator

- Opening commit: `e4539b8`; proposal implementation commit: `111ddf7`.
- Proposal: `experiments/m5/fifth-pilot-proposal-v1.json`, byte SHA-256
  `7cec37d6fe17788eb3097103548e4afc019ed0bbe5b91993515940695811d918`.
- Semantic SHA-256:
  `ce93bd16450b184a4032ff2dff6dee5d5bb7d5322198cbdd303e6db340b45601`.
- Schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- The exact replacement row, immutable image, dry-run command, full accepted
  fourth-pilot chain and terminal receipt, source/input hashes, workspace,
  cost/time bounds, suite-first order, four 64x5 smokes, named normalized ONNX
  outputs, receipt/teardown behavior, prohibitions, and authority state are
  semantically locked.
- Negative tests reject 153 scalar mutations, 182 deletions, an extra field,
  and explicit `compute_authorized=true`.
- `hyperstack_A100_80G_retry` is explicitly prohibited. No fallback or
  substitution path is present.

## Validation

- Exact proposal validator and mutation suite: pass.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- M5 immutable experiment, CUDA runtime static validation,
  artifact-attestation, Python compilation, and diff checks: pass.
- `scripts/check_branch_hygiene.sh 957499a`: pass with nine manifests and 68
  immutable receipt logs.
- All nine tracked receipt manifests revalidated and
  `git diff --quiet 957499a -- receipts` passes.
- Autonomous workflow audit: clean.
- Closing authenticated Brev inventory: `{"workspaces": null}`.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export, or
  accepted-receipt mutation occurred.

## Evidence And Authority Boundary

This is a proposal only. `compute_authorized=false`; no Manager authority is
present. At most a later separately authorized pilot could prove CUDA pipeline
compatibility. Candidate, held-out, full CUDA matrix, publication, activation,
transfer, physical work, H100, multi-GPU, second workspace, fallback,
substitution, and overspend remain prohibited.

## Step-9 Flags For Reviewer

- Recompute proposal/schema/input/source-bundle hashes and accepted chain.
- Confirm the exact DGX catalog row and immutable-digest container dry run,
  including the exact `$1.656/hour` and `$3.312` ceiling.
- Exercise every mutation test and explicit `compute_authorized=true` failure.
- Confirm the fourth pilot remains terminal negative and cannot be retried.
- Re-run the full local authority suite, all manifests, branch hygiene from
  `957499a`, and workflow audit.
- Retain the stop sentinel and create no Manager authority or workspace.
