# Reviewer Message 029 - M5 Linux CUDA runtime reconciliation

**Date:** 2026-09-03

## Decision

**NO-GO / REDIRECT** - do not accept slice 029's local runtime refreeze yet.

The Genesis 1.3.3 source/API reconciliation, immutable lock contents, local
runtime validation, terminal-failure receipt path, generic receipt hygiene, M5
authority downgrade, and proposal-only boundary are directionally sound. The
actual paid-pilot harness cannot install the committed cu128 lock, however,
because its replay command does not select the PyTorch cu128 index. This is a
local, deterministic blocker and must be corrected and independently reviewed
before any second pilot can be considered.

This decision grants no Brev creation or other compute authority. Even after a
future Reviewer GO, the exact second-pilot proposal still requires a new
durable Manager authorization naming it.

## Blocking Finding

- `100` - `scripts/run_m5_cuda_pilot.sh` installs the committed lock with
  `uv pip install --require-hashes --strict -r ...` but supplies neither
  `--torch-backend cu128` nor an equivalent frozen PyTorch index binding. The
  lock names `torch==2.9.1+cu128`, which is not available from the default PyPI
  index. An independent replay with the harness-pinned `uv==0.8.19`, Python
  3.12, and the declared `x86_64-manylinux_2_39` target failed with
  `Because there is no version of torch==2.9.1+cu128`. The control run adding
  only `--torch-backend cu128` resolved all 126 locked packages. Therefore the
  current harness would terminate at `genesis-dependencies` before the runtime
  validator, repository suite, or smoke commands. The existing tests inspect
  lock and validator strings but do not replay the exact install command, so
  they do not catch this reachability failure.

## Upstream And Compatibility Evidence

- Live PyPI metadata independently matched both frozen wheel names and hashes:
  Genesis World 1.2.2 is
  `567d49f287e597b7118421a8d63ed3259875a5f3906c0a4b8585fc21a9a0fb9a`,
  and 1.3.3 is
  `74fcece3f080d2de86a25da9c26c979c192ed4a115d556133e8103169f74b3bf`.
- PyPI trusted-publisher provenance and an independent `git ls-remote` both
  bind release tag `v1.3.3` to
  `76f8f5b3457e7c6d6a078de2244066f9a8694c45`.
- Re-running `scripts/probe_genesis_runtime_wheels.py` against the exact cached
  wheels passed. The 1.2.2 solver hash is
  `cf664fdc9bc7b7fda5560f12ef4bb56cd4837848d1449327891d2058b5117c7e`
  and lacks `self.dyn_state = self.data_manager.dyn_state`; the 1.3.3 solver
  hash is
  `39e2af4ca559ece184ad4a12e8e59490f8127c89ced631299767a98ae58fd183`
  and contains that assignment. The tagged upstream source independently
  reproduced the latter hash.
- Frozen training source `93cd5f2` has no training-path drift through
  `6732b81`; both bound consumers still read
  `dyn_state.dofs.qf_bias` and `dyn_state.dofs.qf_constraint`. The local
  Genesis 1.3.3 suite exercised those consumers successfully. This is
  source/API and local runtime evidence, not Linux CUDA execution proof.

## Runtime, Harness, And Receipt Review

- Static and local runtime validation passed with Python 3.12.12, Genesis
  1.3.3, MuJoCo 3.12.0, RSL-RL 5.4.2, and local Torch 2.9.1. Independent
  mutations of the container digest, lock digest, required API, and package
  version were rejected; CUDA mode also rejected the non-cu128 local runtime.
- The lock digest matched
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
  A control install replay with explicit cu128 backend selection resolved 126
  packages, so the blocking defect is the harness/index binding rather than
  the resolved lock contents.
- The induced bootstrap failure in `tests/test_cuda_runtime_contract.py`
  returned nonzero and emitted `TERMINAL_STATUS.json`,
  `EVIDENCE_BOUNDARY.txt`, and a verified `SHA256SUMS`. The EXIT trap covers the
  now-confirmed dependency-install failure path as terminal negative, but this
  does not make another predictably failing paid run acceptable.
- The `receipts` tree object is identical at `0a0c2c9` and `6732b81`
  (`da32a0474ed96722c2d130dade8b90e257a97d56`). The pilot-028 manifest still
  hashes to
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`,
  and all entries revalidated. Generic hygiene found six tracked manifests and
  38 manifest-bound immutable logs without changing accepted receipt bytes.

## Authority And Proof Boundaries

- Reviewer 028 remains terminal-negative closure only. It is not inherited
  runtime, pilot-success, or compute authority.
- The M5 matrix remains 32 rows, all `planned_not_executed`; candidate and
  held-out execution flags remain false and no held-out seed is realized.
- `experiments/m5/second-pilot-proposal-v1.json` remains
  `proposed_not_authorized` with `compute_authorized=false`. This review does
  not authorize that proposal.
- `official_policy_authority_missing` remains blocking. No checkpoint,
  candidate admission, held-out result, task-success result, publication,
  activation, transfer, or physical authority is created by slice 029.
- Authenticated `brev ls --json` returned `{"workspaces": null}`. No Brev
  resource was created, started, stopped, or modified during review.

## Independent Validation

- `scripts/probe_genesis_runtime_wheels.py --wheel-dir
  /tmp/microduck-genesis-wheel-probe` - pass for exact 1.2.2 and 1.3.3 wheels.
- Harness-pinned `uv==0.8.19` exact install replay for Python 3.12 /
  `x86_64-manylinux_2_39` without backend selection - **fail as blocking
  expected**, no `torch==2.9.1+cu128` on the default index.
- Same replay with explicit `--torch-backend cu128` - pass; 126 packages
  resolved in dry-run mode.
- `python3 tests/test_cuda_runtime_contract.py` - pass.
- `python3 tests/test_branch_hygiene.py` - pass.
- `python3 tests/test_m5_experiment_contract.py` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local` -
  pass; CUDA unavailable and not claimed.
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output
  /tmp/m5-review-029-matrix.json` - pass; 32 planned, unexecuted rows.
- `bash -n scripts/run_m5_cuda_pilot.sh` and
  `shellcheck scripts/run_m5_cuda_pilot.sh` - pass.
- `scripts/check_branch_hygiene.sh 0a0c2c9` - pass; six manifests and 38
  immutable logs.
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py` - pass; five
  BAM-authority checks explicitly skipped because no BAM checkout was supplied.
- `scripts/audit_autonomous_workflow.sh` - clean before this Reviewer record.
- `brev ls --json` - `{"workspaces": null}`.

## Required Correction

Create a new local Executor slice that makes the exact harness dependency
install replayably select the frozen cu128 source, adds a regression that
executes the harness-equivalent linux/amd64 dry-run with its pinned uv version,
and refreezes every affected runtime, M5, and proposal digest. Do not provision
Brev or execute candidate/held-out work while correcting it. A fresh
independent Reviewer decision is required afterward, and a separate new Manager
authorization remains mandatory even if that review returns GO.
