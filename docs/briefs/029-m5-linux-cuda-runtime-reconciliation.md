# Slice Brief 029 - m5 linux cuda runtime reconciliation

**Date:** 2026-09-03

## Objective

Reconcile the frozen Genesis Linux source/runtime incompatibility exposed by
terminal pilot 028, refreeze a reproducible linux/amd64 CUDA environment and
preflight contract, and make receipt hygiene generic without altering accepted
receipt bytes. End with independent review and, only if local gates pass, a
proposal-only second-pilot card.

## Product / Project Value

Prevents another paid run from discovering a dependency/API mismatch after
provisioning and makes CUDA runtime identity a first-class immutable input.
Preserves negative evidence while turning it into a deterministic preflight.

## Acceptance Criteria

- Record primary upstream evidence for the selected Genesis release, exact
  wheel digest, release source commit, and required `RigidSolver.dyn_state`
  surface; prove the terminal 1.2.2 mismatch without weakening consumers.
- Add a hash-locked Python 3.12 linux/amd64 CUDA dependency lane using Torch
  cu128, Genesis 1.3.3, MuJoCo 3.12.0, RSL-RL 5.4.2, and the existing evaluator
  dependencies.
- Add a schema-bound runtime contract and validator with negative probes for
  platform, container digest, package versions/digests, required API surface,
  lock digest, CUDA visibility, and headless MuJoCo EGL selection.
- Make the paid-pilot harness consume only the refrozen CUDA lock and fail
  before the repository suite unless the runtime contract passes. Always emit
  a terminal checksum receipt on preflight/suite failure.
- Generalize branch hygiene to every tracked `receipts/**/SHA256SUMS` root and
  exempt only tracked, manifest-bound raw logs from whitespace diagnostics.
  Preserve pilot-028 receipt bytes and manifest digest exactly.
- Run focused tests, a local linux/amd64 CPU-safe container/static-wheel probe
  where available, the full applicable local suite, contract/manifest checks,
  and the autonomous workflow audit.
- Commit an Executor result and obtain an independent Reviewer decision. A
  second-pilot card may be exact and current but remains `proposed_not_authorized`.

## Expected Files

- `environments/cuda/{README.md,requirements.in,requirements.lock,runtime-v1.json,runtime-v1.schema.json}`
- `scripts/{validate_cuda_runtime.py,run_m5_cuda_pilot.sh,check_branch_hygiene.sh}`
- `.gitattributes`
- `tests/test_cuda_runtime_contract.py`
- `experiments/m5/{contract-v1.json,contract-v1.lock.json,contract-v1.schema.json}`
- `docs/autonomous-workflow/05-devops-and-session-ops.md`
- `docs/manager-log/006-m5-second-pilot-proposal.md`
- `GOAL.md`, `TRAINING_ACTUALIZATION.md`, and this slice's Executor/Reviewer records

## Test Plan

1. Write negative runtime-contract and generic receipt-hygiene probes first.
2. Generate the linux/amd64 hash lock with an explicit cu128 Torch backend.
3. Download and hash exact 1.2.2/1.3.3 wheels; inspect their tagged source API.
4. Run the refrozen 1.3.3 lane locally and, when the local container engine can
   be started safely, perform a bounded linux/amd64 CPU-only source/import probe.
5. Verify pilot-028 `SHA256SUMS` and manifest digest are byte-identical.

## Validation Commands

- `python3 tests/test_cuda_runtime_contract.py`
- `python3 tests/test_branch_hygiene.py`
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local`
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output /tmp/m5-slice-029-matrix.json`
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py`
- `scripts/check_branch_hygiene.sh 0a0c2c9`
- `scripts/audit_autonomous_workflow.sh`
- `brev ls --json`

## Evidence To Record

Exact upstream URLs/commit/wheel hashes, generated lock digest, API probe output,
local/container runtime versions, negative-probe results, unchanged pilot-028
manifest digest, current Brev catalog snapshot used by the proposal, empty
inventory, and every validation result.

## Reachability / Demo Proof

The next pilot harness must invoke the runtime validator before the repository
suite or training. Branch hygiene must discover the existing M5 receipt without
an Apple-specific path.

## Cross-Doc Impact

Update M5 state and bindings without changing task semantics, seeds, transition
budgets, evaluator, evidence classes, official-policy blocker, or held-out state.

## Out Of Scope

Paid compute, another Brev workspace, GPU proof, pilot success, training,
candidate admission, held-out realization, publication, activation, transfer,
physical operation, or rewriting any accepted receipt payload.

## Stop Conditions

- Stop if the selected version lacks an exact upstream wheel/source identity or
  the required API cannot be shown without source changes.
- Stop if linux/amd64 resolution is not hash-locked or requires weakening the
  suite, task contract, evaluator, or source identity.
- Stop before any paid provisioning; only a later independent decision plus a
  separate durable authorization may reopen compute.
