# Executor Session 037 - M5 fourth CUDA pilot

**Date:** 2026-09-03

## Baseline And Authority

- Accepted proposal review HEAD: `125493c`.
- Manager authorization 010 is being committed with this execution brief.
- No prior Manager authorization may be reused.

## Work In Progress

## Pre-Create Gates

- Manager authorization 010 was committed at `929dc6b` before any paid action.
- The exact proposal remained byte-identical at
  `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`;
  the semantic hash, harness, runtime, lock, image, and source identities all
  matched the authorization.
- Clean exact source checkouts generated each of the three source bundles twice
  using `pack.threads=1` and `pack.windowMemory=64m`. Each pair was
  byte-identical, each bundle verified, and the final hashes exactly matched the
  proposal. All temporary refs were deleted.
- Immediately before creation, authenticated inventory was empty and the fresh
  catalog exactly matched `hyperstack_A100_80G`, shadeform/hyperstack, x86_64,
  one A100 with 80 GB VRAM, non-stoppable, non-rebootable, at `$1.62/hour`.

## Workspace And Terminal Result

- Create-to-delete billing anchor: `2026-09-04T04:41:36Z`.
- Exactly one workspace was created: `microduck-m5-pilot4-20260904`, exact ID
  `tpo91g7kj`, with the authorized type and immutable linux/amd64 image.
- The workspace remained `STARTING/BUILDING/NOT READY/UNHEALTHY`, then
  `UNHEALTHY/BUILDING/NOT READY/UNHEALTHY`, through
  `2026-09-04T04:51:51Z`, beyond the catalog's listed 390-second boot time.
- It never exposed a ready shell. The pilot was therefore declared
  **terminal negative** at stage `workspace-provisioning-health`.
- No file was uploaded. The harness was invoked zero times; the full suite,
  all four smokes, and all normalized ONNX exports were never started.

## Receipt And Teardown

- Local control-plane receipt:
  `receipts/m5/pilot/20260904T044136Z-tpo91g7kj/`.
- Because the workspace never had a shell and no harness ran, no remote receipt
  or remote `SHA256SUMS` could exist. The receipt states that limitation rather
  than fabricating remote-manifest equality.
- Thirteen files are bound by a sorted local `SHA256SUMS`; every entry verifies
  and the manifest SHA-256 is
  `89bdd479d62a4a96b96cb00f161d232cb36717ba938e9a63c09fac622df24c70`.
- Exact-ID deletion was requested at `2026-09-04T04:52:59Z`. The control plane
  briefly showed `DELETING`, regressed to `STARTING`, and then removed the
  workspace. An exact-ID retry reported it no longer existed.
- Authenticated inventory first returned empty at `2026-09-04T04:53:49Z` and
  remained empty through five additional polls ending at
  `2026-09-04T04:54:20Z`.
- Conservative create-to-empty elapsed time is 733 seconds, or `$0.329850` at
  `$1.62/hour`, below the 7,200-second / `$3.24` ceilings. This arithmetic is
  not a provider invoice.

## Evidence Boundary

Provisioning-health evidence only. This terminal result proves no CUDA runtime
or pipeline compatibility, smoke success, M5 completion, task or policy
success, candidate admission, held-out evidence, publication, activation,
transfer, or physical authority. Manager authorization 010 is consumed and
cannot be reused.

## Step-9 Flags For Reviewer

- Revalidate the exact Manager/proposal chain and immutable input hashes.
- Verify the local receipt manifest and the honest remote-receipt-unavailable
  boundary.
- Confirm the single workspace identity, zero harness invocations, elapsed/cost
  arithmetic, exact-ID teardown, and authenticated empty inventory.
- Confirm no smoke/export/candidate/held-out/full-matrix/publication/activation/
  transfer/physical action occurred.
- Keep the stop sentinel in place and do not authorize a retry.
