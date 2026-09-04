# Reviewer Message 039 - M5 fifth-pilot cost-binding correction

**Date:** 2026-09-04

## Decision

**NUDGE** - do not accept handoff `33c1b8c` yet.

Reviewer 038's cost-rate and durable-goal corrections are verified and all
reported validation gates pass. One new receipt-integrity defect remains in
the fifth-specific harness. No compute is authorized.

## Verified Corrections

- The proposal binds `scripts/run_m5_cuda_pilot_5.sh` at SHA-256
  `8e283ee313fc8c07a16b33ec32133df00e2a9d47b30a379d1ad6004f1627459b`.
- The harness, catalog, and limit rates are exactly `$1.656/hour`; the two-hour
  ceiling is `$3.312`.
- Decimal validator checks and the direct historical `$1.62/hour` negative
  regression pass.
- The original fourth-pilot harness remains byte-identical at
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- `GOAL.md` now distinguishes the consumed historical hyperstack envelope from
  the proposed fifth-pilot massedcompute envelope, states no retry, requires
  fresh Manager authority, and retains `<stop-orchestrator/>`.

## Required Correction - Harness Self-Attestation Name

The proposal binds `scripts/run_m5_cuda_pilot_5.sh`, but the harness still
requires, copies, and hashes `$INPUT_ROOT/run_m5_cuda_pilot.sh`. Native-name
staging therefore fails at bootstrap without an unstated old-name alias. If
both accepted harnesses were staged by their native names, the fifth harness
could instead retain and attest the wrong file.

An independent local failure probe confirmed:

- with only `run_m5_cuda_pilot_5.sh` staged, the harness exits at `bootstrap`
  and retains no harness copy;
- with an unstated old-name alias, it reaches `host-nvidia-smi` and copies the
  aliased fifth bytes as `run_m5_cuda_pilot.sh`.

Required correction:

- Make the fifth harness require, copy, hash, and retain the exact
  fifth-specific native input, under an unambiguous fifth-specific receipt
  name.
- Add a deterministic regression proving native-name staging reaches the next
  preflight gate and the retained hash equals the proposal-bound fifth harness.
- Prove no fourth-harness alias is required or accidentally attested.
- Refreeze the fifth harness and proposal byte/semantic hashes while preserving
  the accepted fourth harness and all accepted receipts.
- Rerun the focused tests, full authority-enabled suite, static/artifact/Bash/
  shellcheck gates, all manifests and immutable logs, branch hygiene, workflow
  audit, diff checks, and final authenticated empty Brev inventory.

## Independent Evidence

- Proposal byte/semantic SHA-256:
  `54d61f03930478fcb66955d60314b682eb3fb5e1c746ba226b29a9f04c263349` /
  `cd958e6a359bd5f347b840eecde566af10ff9aebb573f55bc913d896d9174371`.
- Schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- The complete authority-enabled local suite, proposal mutation suite, M5
  experiment contract, static CUDA contract, artifact contract, Python/Bash/
  shellcheck checks, nine manifests, 68 immutable logs, and workflow audit all
  passed.
- The accepted receipt tree and fourth-pilot harness are unchanged from
  `957499a`.
- Deterministic source bundles reproduced byte-identically at their three bound
  hashes, and no temporary proposal refs remain.
- Fresh catalog and exact immutable-container dry-run evidence still matched
  `massedcompute_A100_sxm4_80G_DGX` at `$1.656/hour`.
- Authenticated Brev inventory was empty before and after review; no resource
  was created or mutated.

## Claim And Authority Boundary

Slice 039 proves the rate-binding and durable-goal corrections, but not
unambiguous fifth-harness staging or receipt self-attestation. It authorizes no
paid compute, Brev creation, remote execution, training, CUDA compatibility,
M5 completion, task or policy success, candidate or held-out work,
publication, activation, transfer, or physical operation.

Retain `<stop-orchestrator/>` in `GOAL.md`.
