# Executor Session 030 - M5 cu128 install source correction

**Date:** 2026-09-03

## Slice

Correct Reviewer 029's only blocking finding without paid compute: make the
exact harness install select the cu128 PyTorch source, execute a pinned-uv
linux/amd64 resolution regression, and refreeze all affected bindings.

## Files Changed

- `scripts/run_m5_cuda_pilot.sh` adds `--torch-backend cu128` to the exact
  `uv pip install` path while preserving strict hashes and the frozen lock.
- `tests/test_cuda_lock_resolution.py` executes the harness-pinned
  `uv==0.8.19` against Python 3.12 and `x86_64-manylinux_2_39`, requiring all
  126 packages plus exact Genesis and Torch versions.
- The CUDA runtime JSON/schema now records and validates
  `install_torch_backend=cu128`.
- The second-pilot proposal, M5 contract/schema/lock, semantic validator, and
  operator/Manager/milestone documents carry the corrected hashes and slice-030
  review prerequisite. The new regression is itself an M5-bound input.

## Tests / Validation

- `python3 tests/test_cuda_lock_resolution.py` - pass: pinned uv 0.8.19,
  126 packages, `genesis-world==1.3.3`, `torch==2.9.1+cu128`.
- `python3 tests/test_cuda_runtime_contract.py` - pass.
- `python3 tests/test_m5_experiment_contract.py` - pass.
- `python3 tests/test_branch_hygiene.py` - pass.
- `python3 scripts/validate_cuda_runtime.py --mode static` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local` -
  pass at Python 3.12.12 with the expected local non-CUDA boundary.
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output
  /tmp/m5-slice-030-matrix.json` - pass: 32 planned, unexecuted rows; second
  pilot proposed but unauthorized.
- `bash -n scripts/run_m5_cuda_pilot.sh` and `shellcheck` - pass.
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py` - pass; five
  explicit BAM-authority skips because no BAM checkout was supplied.
- `scripts/check_branch_hygiene.sh 0a0c2c9` - pass: six manifests and 38
  immutable logs.
- `scripts/audit_autonomous_workflow.sh` - pass with review-required state and
  stop sentinel.
- `brev ls --json` - `{"workspaces": null}`; no Brev resource was created or
  modified.

## Evidence

- CUDA requirements lock remains byte-identical at
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Runtime contract SHA-256 is
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- Runtime schema SHA-256 is
  `abed882a229a67293feb3e4fb0ab22765fabd2617c2c974bceca0a225c675206`.
- Corrected harness SHA-256 is
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Pinned-uv resolution regression SHA-256 is
  `713176c12fd3366abc30c291ba0cdf8011945ccf1f7d991844cdc2dc11fd7df8`.
- Proposal SHA-256 is
  `f020df3f1cfb29b160ec86765a06e184a696af940fe62d690fda371653aa536e`.
- Pilot-028 accepted receipt manifest remains byte-identical at
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`.

## Step-9 Flags For Reviewer

- Replay the exact pinned-uv regression independently and confirm removing only
  `--torch-backend cu128` reproduces Reviewer 029's failure.
- Confirm actual harness flag placement matches the passing dry-run semantics,
  not merely a text assertion.
- Revalidate every cascading runtime/proposal/M5 digest and unchanged receipts.
- Keep local resolver success distinct from Linux CUDA import or training proof,
  and keep the second-pilot card unauthorized.

## Next Suggested Slice

Stop at reviewed local refreeze. Only a later new Manager authorization naming
the exact proposal could open one bounded second pilot; full CUDA and
candidate/held-out work remain separately gated.
