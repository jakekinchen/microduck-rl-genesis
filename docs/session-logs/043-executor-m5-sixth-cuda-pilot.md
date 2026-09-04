# Executor Session 043 - M5 sixth CUDA pilot

**Date:** 2026-09-04

## Baseline And Authority

- Accepted corrected sixth-pilot handoff: `eb52e63`.
- Reviewer 042 acceptance record: `f24f63a`.
- Manager authority 012 is committed with this execution brief before any paid
  action.
- This authority permits exactly one bounded workspace and at most one harness
  invocation. No previous Manager authorization may be reused.

## Pre-Create Gates

- Manager authority 012 was committed at `7437dd6` before the create anchor.
- Proposal, schema, sixth harness, runtime, lock, image, accepted handoff, and
  Reviewer acceptance hashes all matched Manager authority 012.
- Each source bundle was regenerated twice from isolated exact-commit clones
  with `pack.threads=1` and `pack.windowMemory=64m`; every pair was
  byte-identical, passed bundle verification, and matched its accepted hash.
- Immediately before creation, authenticated inventory was empty, the exact
  direct-GCP catalog row matched every frozen field at `$4.408062/hour`, and
  the exact immutable-container dry run returned only the accepted type.

## Workspace And Terminal Result

- Create-to-delete billing anchor: `2026-09-04T07:01:21Z`.
- Exactly one workspace was created: `microduck-m5-pilot6-20260904`, exact ID
  `urmhasks7`, type `a2-highgpu-1g:nvidia-tesla-a100:1`.
- The create command reported Ready at `07:03:05Z`, while authenticated
  inventory reported `RUNNING / BUILDING / NOT READY`. Health briefly became
  `HEALTHY` at `07:03:27Z`, then regressed to `UNHEALTHY` at `07:03:38Z`.
- Thirty authenticated polls through `07:08:46Z`, beyond the 420-second
  advertised boot window, never reported shell readiness.
- The bounded pre-upload disk command began at `07:09:04Z`. Initial SSH failed
  at name resolution and Brev reported seven failed readiness attempts before
  the wait was stopped. No shell or disk proof was obtained.
- At `07:09:51Z`, 510 seconds after creation, the pilot was declared
  **terminal negative** at `workspace-provisioning-connectivity`.
- Zero files were uploaded. The harness was invoked zero times; the suite,
  disk gate inside the harness, all smokes, and all ONNX exports never started.

## Receipt And Teardown

- Local control-plane receipt:
  `receipts/m5/pilot/20260904T070121Z-urmhasks7/`.
- Because no usable shell existed before the terminal decision, no remote
  receipt or remote `SHA256SUMS` could exist. The local receipt explicitly
  records the limitation.
- Thirteen payload files are bound by a sorted local `SHA256SUMS`; all verify.
  Manifest SHA-256:
  `b1fa2d7eb2e4f6c574b7c70f292e4ef9708ce516c6618e0fa62442c3f0ce886e`.
- Exact-ID deletion was requested at `07:11:00Z`. The first teardown poll at
  `07:11:02Z` belatedly reported `COMPLETED / READY / HEALTHY`, after both the
  terminal decision and delete request. The no-retry boundary was preserved:
  execution was not reopened, no upload occurred, and the harness remained at
  zero invocations.
- Inventory transitioned through deletion/stopping and became empty at
  `07:12:31Z`; five additional authenticated polls remained empty through
  `07:14:08Z`.
- Conservative create-to-empty elapsed time is 670 seconds. At the exact
  `$4.408062/hour` rate, estimated cost is `$0.820389`, below the 7,200-second /
  `$8.816124` ceilings. This is not a provider invoice.

## Evidence Boundary

Provisioning/connectivity evidence only. This terminal result proves no usable
pre-terminal shell, disk capacity, CUDA runtime or pipeline compatibility,
smoke success, M5 completion, task or policy success, candidate admission,
held-out evidence, publication, activation, transfer, or physical authority.
Manager authority 012 is consumed and cannot be reused.

## Local Validation And Cleanup

- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- Exact proposal validation, static CUDA, artifact contract, Python compile,
  Bash syntax, shellcheck, diff, and workflow audits: pass.
- Branch hygiene from `f24f63a`: pass with eleven manifests and 68 immutable
  logs. Every previously accepted receipt is unchanged; the only new receipt
  path is the exact sixth-pilot control-plane receipt.
- Authenticated Brev inventory remained empty at final Executor closure.
- The two exact temporary bundle-generation directories created for proposal
  and execution verification, totaling approximately 1.18 GiB, were removed
  after their hashes were captured. No user artifact was removed.

## Step-9 Flags For Reviewer

- Revalidate exact Manager/proposal/Reviewer identities and immutable hashes.
- Verify the 30 readiness polls, failed bounded pre-upload connection, zero
  uploads, zero harness invocations, and honest disk-gate-not-run boundary.
- Confirm the belated READY poll occurred only after terminal declaration and
  exact-ID deletion request, and that execution was not reopened.
- Verify the 13-file local manifest, elapsed/cost arithmetic, exact-ID teardown,
  first empty inventory, and five subsequent empty polls.
- Confirm previously accepted receipts are unchanged and only this receipt was
  added. Restore the stop sentinel and authorize no retry or replacement.
