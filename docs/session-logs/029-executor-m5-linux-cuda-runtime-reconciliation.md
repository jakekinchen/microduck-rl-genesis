# Executor Session 029 - m5 linux cuda runtime reconciliation

**Date:** 2026-09-03

## Slice

Reconcile terminal pilot 028's frozen-source/Genesis 1.2.2 API mismatch using
only local work. Refreeze an exact linux/amd64 CUDA dependency/runtime contract,
make the pilot fail closed with terminal receipts, generalize receipt hygiene,
and end at a proposal-only second-pilot boundary.

## Files Changed

- Added `environments/cuda/` input, 2,461-line hash lock, schema, runtime
  contract, and operator notes for Python 3.12, Ubuntu 24.04/glibc 2.39, Torch
  cu128, Genesis World 1.3.3, MuJoCo 3.12.0, and RSL-RL 5.4.2.
- Added `scripts/validate_cuda_runtime.py` and
  `scripts/probe_genesis_runtime_wheels.py`; changed the pilot harness to
  require the reviewed commit, install the exact hash lock, preflight before
  the suite, select EGL headless mode, and finalize a receipt on every exit.
- Refroze the M5 contract/schema/lock/matrix with the runtime and second-pilot
  proposal inputs. `pilot_resource_authorized=false`; candidate and held-out
  work remain false.
- Generalized `.gitattributes` and `scripts/check_branch_hygiene.sh` from the
  Apple receipt family to every tracked manifest-bound receipt log, with tests.
- Added the proposal-only Manager card and machine-readable second-pilot schema
  and record; updated durable M5 and workflow documentation.

## Tests / Validation

- `scripts/probe_genesis_runtime_wheels.py --wheel-dir /tmp/microduck-genesis-wheel-probe` - pass for exact 1.2.2 and 1.3.3 wheels.
- `python3 tests/test_cuda_runtime_contract.py` - pass, including mutations and a deliberately failed bootstrap that produced `TERMINAL_STATUS.json`, `EVIDENCE_BOUNDARY.txt`, and `SHA256SUMS`.
- `python3 tests/test_m5_experiment_contract.py` - pass.
- `python3 tests/test_branch_hygiene.py` - pass.
- `scripts/check_branch_hygiene.sh 0a0c2c9` - pass: 6 manifests, 38 immutable logs.
- `python3 scripts/validate_cuda_runtime.py --mode static` - pass.
- `.venv-apple/bin/python scripts/validate_cuda_runtime.py --mode local` - pass: Python 3.12.12, Genesis 1.3.3, MuJoCo 3.12.0, RSL-RL 5.4.2, Torch 2.9.1, CUDA unavailable as expected.
- `.venv-apple/bin/python scripts/validate_m5_experiment.py --matrix-output /tmp/m5-slice-029-matrix.json` - pass: 32 planned, unexecuted rows.
- `bash -n scripts/run_m5_cuda_pilot.sh` and `shellcheck scripts/run_m5_cuda_pilot.sh` - pass.
- `GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py` - pass; five BAM-authority checks explicitly skipped because no BAM checkout was supplied.
- `scripts/audit_autonomous_workflow.sh` - pass.
- `brev ls --json` - `{"workspaces": null}` before handoff; no workspace created.

## Reachability

The pilot harness reaches the static runtime validator before dependency
installation, the CUDA-mode validator before the repository suite, and its EXIT
trap on an induced missing-input failure. The generic hygiene test discovers
the existing M5 manifest without an Apple-specific path.

## Evidence

- Genesis World 1.3.3 wheel SHA-256:
  `74fcece3f080d2de86a25da9c26c979c192ed4a115d556133e8103169f74b3bf`.
- Release source commit: `76f8f5b3457e7c6d6a078de2244066f9a8694c45`;
  embedded rigid solver SHA-256:
  `39e2af4ca559ece184ad4a12e8e59490f8127c89ced631299767a98ae58fd183`.
- Rejected 1.2.2 wheel SHA-256:
  `567d49f287e597b7118421a8d63ed3259875a5f3906c0a4b8585fc21a9a0fb9a`;
  embedded rigid solver SHA-256:
  `cf664fdc9bc7b7fda5560f12ef4bb56cd4837848d1449327891d2058b5117c7e`.
- CUDA lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Accepted pilot-028 manifest digest remains exactly
  `1e8d4948294b4a4c95a8a73c9e0a7c9ab0fcef4c354a2c11ac29f1eb4ce8566b`.
- Local linux/amd64 container execution was attempted only through Colima; it
  stopped before VM creation because `qemu-img` is unavailable. No QEMU package,
  VM, paid compute, candidate seed, held-out seed, or accepted receipt changed.

## Step-9 Flags For Reviewer

- Confirm the chosen 1.3.3 upstream/wheel/source identity genuinely supplies
  both frozen consumers without weakening source semantics.
- Re-run the contract, lock, failure-finalizer, generic receipt-hygiene, and
  full-suite checks; independently verify pilot-028 bytes remain unchanged.
- Treat the second-pilot card as a proposal, never inherited authorization.
- Preserve the explicit limitation: local source/import/resolver proof is not
  linux CUDA runtime or training proof.

## Next Suggested Slice

Only after Reviewer GO and a new durable Manager authorization naming the exact
proposal: one bounded second pilot with mandatory terminal receipt recovery and
deletion. Otherwise stop at the reviewed local refreeze.
