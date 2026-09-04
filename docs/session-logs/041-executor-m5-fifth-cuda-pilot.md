# Executor Session 041 - M5 fifth CUDA pilot

**Date:** 2026-09-04

## Baseline And Authority

- Accepted fifth-pilot handoff: `9af3634`.
- Reviewer 040 acceptance record: `89d8a65`.
- Manager authority 011 is committed with this execution brief before any paid
  action.
- This authority permits exactly one bounded workspace and one harness
  invocation. No previous Manager authorization may be reused.

## Pre-Create Gates

- Manager authority 011 was committed at `1e835c5` before the create anchor.
- Proposal, schema, fifth harness, runtime, lock, image, accepted handoff, and
  Reviewer acceptance hashes all matched Manager authority 011.
- Each source bundle was generated twice from isolated exact-commit clones
  using `pack.threads=1` and `pack.windowMemory=64m`; each pair was
  byte-identical, verified, and matched its accepted proposal hash.
- Immediately before creation, authenticated inventory was empty, the exact
  massedcompute catalog row matched every frozen field at `$1.656/hour`, and
  the exact container-mode immutable-digest dry run returned only the accepted
  type.

## Workspace And Terminal Result

- Create-to-delete billing anchor: `2026-09-04T05:57:49Z`.
- Exactly one workspace was created: `microduck-m5-pilot5-20260904`, exact ID
  `i1bsb56r7`, type `massedcompute_A100_sxm4_80G_DGX`.
- The create command briefly reported `Ready`, but authenticated inventory
  remained or regressed to `UNHEALTHY / BUILDING / NOT READY`.
- The single SSH attempt exhausted 20 retries, ending with a timeout to exact
  control-plane endpoint `154.54.100.242:2222`; no shell was obtained.
- At `2026-09-04T06:04:33Z`, 404 seconds after creation and beyond the
  catalog's 390-second boot listing, the workspace was still
  `UNHEALTHY / BUILDING / NOT READY`. The pilot was declared
  **terminal negative** at `workspace-provisioning-connectivity`.
- Zero files were uploaded. The harness was invoked zero times; the suite,
  all four smokes, and normalized ONNX exports never started.

## Receipt And Teardown

- Local control-plane receipt:
  `receipts/m5/pilot/20260904T055749Z-i1bsb56r7/`.
- Because no shell ever existed, no remote receipt or remote `SHA256SUMS`
  could exist. The local receipt records this limitation explicitly.
- Thirteen payload files are bound by a sorted local `SHA256SUMS`; all verify.
  Manifest SHA-256:
  `ab14168c73f6829a2168cfe34710e3d380b1c1b5e331967d6233382f09b6b1c3`.
- Exact-ID deletion was requested at `2026-09-04T06:05:44Z`. Inventory showed
  `DELETING`, then became empty at `2026-09-04T06:06:13Z` and remained empty
  through five additional polls ending at `2026-09-04T06:06:52Z`.
- Conservative create-to-empty elapsed time is 504 seconds. At the exact
  `$1.656/hour` rate, estimated cost is `$0.231840`, below the 7,200-second /
  `$3.312` ceilings. This is not a provider invoice.

## Evidence Boundary

Provisioning/connectivity evidence only. This terminal result proves no CUDA
runtime or pipeline compatibility, smoke success, M5 completion, task or
policy success, candidate admission, held-out evidence, publication,
activation, transfer, or physical authority. Manager authority 011 is consumed
and cannot be reused.

## Step-9 Flags For Reviewer

- Revalidate the exact Manager/proposal/Reviewer chain and immutable hashes.
- Verify the local receipt manifest and honest no-shell/no-remote-receipt
  boundary.
- Confirm the one workspace identity, 20-attempt SSH failure, zero uploads,
  zero harness invocations, elapsed/cost arithmetic, exact-ID teardown, and
  repeated authenticated empty inventory.
- Confirm accepted receipts are unchanged and only the new fifth receipt was
  added.
- Keep the stop sentinel and do not authorize retry or replacement compute.
