# Executor Session 039 - M5 fifth-pilot cost-binding correction

**Date:** 2026-09-04

## Baseline And Authority

- Accepted terminal-negative fourth-pilot Reviewer HEAD: `957499a`.
- Fifth-pilot proposal implementation/handoff: `111ddf7` / `86da0ef`.
- Reviewer 038 NUDGE record: `44134bc`.
- Correction opening commit: `25d19bb`.
- This slice is local and non-authorizing. No Brev provisioning, remote
  execution, training, smoke, or export was permitted or performed.

## Correction

- Preserved the accepted fourth-pilot harness
  `scripts/run_m5_cuda_pilot.sh` byte-for-byte at SHA-256
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Added `scripts/run_m5_cuda_pilot_5.sh`, differing from that harness only in
  `PRICE_USD_PER_HOUR=1.656`, at SHA-256
  `8e283ee313fc8c07a16b33ec32133df00e2a9d47b30a379d1ad6004f1627459b`.
- Rebound the fifth-pilot proposal to the fifth-specific harness.
- Added fail-closed extraction of the single numeric harness rate and exact
  decimal equality checks against both catalog and limit rates.
- Added a direct negative regression proving that the historical `$1.62` rate
  is rejected for the fifth-pilot harness.
- Reclassified the hyperstack `$1.62/hour` / `$3.24` constraint in `GOAL.md`
  as historical and consumed; recorded the no-retry boundary and the proposed
  exact massedcompute `$1.656/hour` / `$3.312` limits.

## Frozen Hashes

- Corrected proposal byte SHA-256:
  `54d61f03930478fcb66955d60314b682eb3fb5e1c746ba226b29a9f04c263349`.
- Corrected proposal semantic SHA-256:
  `cd958e6a359bd5f347b840eecde566af10ff9aebb573f55bc913d896d9174371`.
- Unchanged schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- Fifth-specific harness SHA-256:
  `8e283ee313fc8c07a16b33ec32133df00e2a9d47b30a379d1ad6004f1627459b`.

## Validation

- Dedicated fifth-pilot validator: pass with `compute_authorized=false`.
- Fifth-pilot fail-closed tests: pass with 153 scalar mutations, 182
  deletions, an extra field, explicit compute-authority rejection, and direct
  historical harness-rate rejection.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, the locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- Static CUDA runtime contract, artifact contract, and Python compilation:
  pass.
- All nine tracked manifests and 68 immutable logs: pass.
- Branch hygiene from `957499a`, `git diff --check`, accepted-receipt
  immutability, and fourth-pilot harness immutability: pass.
- Autonomous workflow audit: clean.
- Closing authenticated `brev ls --json`: `{"workspaces": null}`.

## Evidence And Authority Boundary

The corrected proposal remains `compute_authorized=false`. No Brev resource
was created or mutated. No CUDA smoke, M5, task, policy, candidate, held-out,
publication, activation, transfer, or physical success is claimed. A future
pilot requires independent Reviewer acceptance of the exact corrected proposal
and then a fresh committed Manager authorization. The stop sentinel is restored
for that boundary.

## Step-9 Flags For Reviewer

- Recompute all four frozen hashes and confirm the fourth-pilot harness is
  unchanged while the fifth-specific harness differs only by the price line.
- Exercise the old-rate negative regression and the complete mutation suite.
- Confirm exact proposal/catalog/limit/harness rate agreement, suite-first
  ordering, no fallback, exact-ID teardown, and non-authorizing state.
- Re-run the full authority-enabled suite, receipt manifests, branch hygiene
  from `957499a`, accepted-receipt immutability, and workflow audit.
- Confirm authenticated Brev inventory remains empty. Do not create a Manager
  authorization or a Brev workspace.
