# Slice Brief 030 - M5 cu128 install source correction

**Date:** 2026-09-03

## Objective

Correct Reviewer 029's single blocking finding by making the paid-pilot
dependency installation explicitly select the frozen PyTorch cu128 source and
adding a pinned-uv linux/amd64 dry-run regression for that exact resolution
path. Refreeze every affected runtime, M5, and proposal digest locally.

## Acceptance Criteria

- The harness's `uv pip install` command includes `--torch-backend cu128` while
  retaining `--require-hashes`, `--strict`, and the exact CUDA lock.
- The runtime contract records and validates the install-source selection.
- A standalone regression executes `uv==0.8.19` against Python 3.12 and
  `x86_64-manylinux_2_39` in dry-run mode and resolves all 126 packages,
  including `torch==2.9.1+cu128`.
- Runtime, proposal, M5 bindings, and M5 lock digests are refrozen exactly.
- Focused tests, the full applicable suite, branch hygiene, workflow audit, and
  an independent Reviewer decision pass.
- No Brev workspace, GPU execution, candidate work, held-out realization, or
  accepted receipt mutation occurs. The second-pilot card remains unauthorized.

## Validation Commands

- `python3 tests/test_cuda_lock_resolution.py`
- `python3 tests/test_cuda_runtime_contract.py`
- `python3 tests/test_m5_experiment_contract.py`
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py`
- `scripts/check_branch_hygiene.sh 0a0c2c9`
- `scripts/audit_autonomous_workflow.sh`
- `brev ls --json`

## Stop Conditions

- Stop if the exact pinned-uv dry-run cannot resolve without weakening hashes,
  versions, platform, CUDA backend, or source identities.
- Stop before any paid provisioning; Reviewer GO and a separate new Manager
  authorization remain necessary but not sufficient for later execution.
