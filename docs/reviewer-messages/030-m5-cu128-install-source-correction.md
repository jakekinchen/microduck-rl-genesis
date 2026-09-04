# Reviewer Message 030 - M5 cu128 install source correction

**Date:** 2026-09-03

## Decision

**GO / STOP** - accept commit
`ba319eee9c2da309090db69da08fb3be701c30b8` against parent
`7f6d0741b1a99a6ad7928eb981f264b3a8c12667` for the reviewed local cu128
install-source correction and cascading refreeze only.

The harness now replayably selects the frozen cu128 PyTorch package source
while retaining strict hash enforcement. This closes Reviewer 029's sole
deterministic blocker. It proves local Linux/amd64 dependency resolution, not
Linux CUDA import, CUDA smoke success, M5 completion, candidate or held-out
execution, task success, publication, activation, transfer, or physical
authority.

Stop the orchestration after this review. **No second pilot is authorized by
this GO.** A new durable Manager authorization naming the exact committed
`experiments/m5/second-pilot-proposal-v1.json` remains required before any
Brev creation or second-pilot execution, along with every proposal precondition.

## Corrective Finding Closure

- Reviewer 029's `100` finding is closed. The actual
  `genesis-dependencies` block in `scripts/run_m5_cuda_pilot.sh` invokes the
  harness-pinned uv with `pip install --python ... --torch-backend cu128
  --require-hashes --strict -r .../environments/cuda/requirements.lock`.
- An independent replay used `uv==0.8.19`, Python 3.12.12, target
  `x86_64-manylinux_2_39`, strict hashes, the frozen lock, and
  `--torch-backend cu128`; dry-run resolution passed with all 126 packages,
  including `torch==2.9.1+cu128` and `genesis-world==1.3.3`.
- The otherwise identical control replay with only
  `--torch-backend cu128` removed exited 1 with the expected no-solution result:
  the default source has no `torch==2.9.1+cu128`. This independently confirms
  that the added flag is necessary and reaches the intended resolver path.

## Binding And Immutability Review

- The frozen requirements lock remains byte-identical at
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Recomputed SHA-256 values match every changed M5 binding: runtime
  `c9f64efb...8f46d`, runtime schema `abed882a...5206`, validator
  `0dd51fdc...15de`, harness `86e96434...98ef`, resolver regression
  `713176c1...df8`, proposal `f020df3f...536e`, M5 contract
  `3df31ec7...aa24`, and M5 schema `2ce4c080...1316`. The M5 lock binds the
  latter contract/schema digests and the unchanged execution matrix exactly.
- `receipts` has the identical Git tree
  `da32a0474ed96722c2d130dade8b90e257a97d56` at accepted baseline `0a0c2c9`,
  parent `7f6d074`, and reviewed commit `ba319ee`. The pilot-028 manifest
  remains byte-identical at
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`,
  and all 23 manifest entries revalidated.

## Authority Boundary

- The runtime and M5 contract remain local refreeze evidence with
  `compute_authorized=false`; the proposal remains `proposed_not_authorized`.
- The M5 matrix remains 32 rows, all `planned_not_executed`; candidate and
  held-out execution remain false, and the held-out protocol remains
  preregistered and unrealized.
- `official_policy_authority_missing` remains blocking. M5 remains open, and
  full CUDA work remains separately gated after any future reviewed pilot.
- Authenticated `brev ls --json` returned `{"workspaces": null}`. No Brev
  resource was created, started, stopped, or modified during this review.

## Independent Validation

- `python3 tests/test_cuda_lock_resolution.py` - pass; pinned uv 0.8.19,
  Python 3.12, linux/amd64 cu128, 126 packages.
- Matching control replay with only `--torch-backend cu128` omitted - expected
  failure, exit 1, because the default source lacks `torch==2.9.1+cu128`.
- `python3 tests/test_cuda_runtime_contract.py` - pass.
- `python3 tests/test_m5_experiment_contract.py` - pass.
- `python3 tests/test_branch_hygiene.py` - pass.
- `python3 scripts/validate_cuda_runtime.py --mode static` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local` -
  pass at Python 3.12.12 with CUDA unavailable and unclaimed.
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output
  /tmp/m5-review-030-matrix.json` - pass; 32 planned rows and no execution
  authority.
- `bash -n scripts/run_m5_cuda_pilot.sh` and
  `shellcheck scripts/run_m5_cuda_pilot.sh` - pass.
- `scripts/check_branch_hygiene.sh 0a0c2c9` - pass; six manifests and 38
  immutable logs.
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py` - pass; five
  explicit BAM-authority skips because no BAM checkout was supplied.
- `scripts/audit_autonomous_workflow.sh` - clean before this Reviewer record.
- `brev ls --json` - `{"workspaces": null}`.

## Terminal Boundary

Slice 030 is closed as reviewed local resolver/refreeze evidence. The next
action, if any, is a new durable Manager decision on the exact proposal. Until
that authority exists, retain `<stop-orchestrator/>` and do not provision or
execute the proposed second pilot.
