# Executor Session 044 - M5 seventh-pilot reliability proposal

**Date:** 2026-09-04

## Baseline And Authority

- Reviewer 043 accepted exact sixth-pilot handoff `a70af4e` only as a
  terminal-negative provisioning/connectivity receipt.
- Manager authority 012 is consumed and cannot be reused.
- This slice is local and non-authorizing. No Brev create, upload, remote
  execution, training, smoke, or export is permitted.

## Reliability Diagnosis And Feedback

The retained fourth/fifth/sixth timelines show a repeated control-plane
readiness failure:

- The fourth type stayed BUILDING / NOT READY / UNHEALTHY for 615 seconds
  before terminal declaration.
- The fifth create command reported Ready while inventory stayed or regressed
  to BUILDING / NOT READY / UNHEALTHY; one SSH path exhausted 20 attempts.
- The sixth create command reported Ready at 104 seconds, inventory briefly
  reported health only, then regressed. Thirty polls and seven SSH readiness
  attempts failed. Shell READY appeared only after terminal declaration and
  the exact-ID deletion request.

A concise nonsecret `brev feedback` report was sent successfully. It asks Brev
to reconcile create/inventory readiness and gate Ready on consecutive healthy
polls plus a successful no-op shell connection.

## Catalog Selection

- At `2026-09-04T07:30:58Z`, authenticated inventory was empty.
- The fresh catalog exposed previously unused direct Crusoe type
  `a100-80gb.1x`: x86_64, one A100 80 GB, 12 vCPUs, 120 GiB RAM, fixed
  128 GB disk, flexible ports, stoppable, non-rebootable, 420-second advertised
  boot estimate, at exactly `$1.98/hour`.
- This is a different exact type and direct provider from all three failed
  pilots. Its fixed 128 GB disk is materially more practical than the sixth
  pilot's 10 GB target, while stoppability and flexible ports retain recovery
  indicators.
- The exact immutable-container command returned only the Crusoe type under
  `--dry-run`; no workspace was created and inventory remained empty.

## Deterministic Inputs And Readiness Protocol

All three sources were bundled twice from isolated exact-commit clones with
unique `refs/m5-pilot7/*` refs, `pack.threads=1`, and
`pack.windowMemory=64m`. Each pair was byte-identical and passed bundle
verification:

- Genesis `7bc61d5`:
  `8469272fd8b6ce522df294ef2ad0ee7f0929af4053d0fb523dc697e23fa2123a`.
- Official walking `109e06d`:
  `9ac470615728680934ab68293b474371b4d66df03925f46195397d954e3c7118`.
- Official backflip `8bde27e`:
  `aa893ba80f3b162fff094ef5151e66b9f963ad1dc8f2c49cf92bd47ae2ddaae0`.

The readiness protocol treats the 420-second catalog boot time only as an
estimate. A future separately authorized execution instead has a 900-second
create-to-probe-success window and requires:

1. Three consecutive authenticated exact-ID polls at least 15 seconds apart,
   each `RUNNING / COMPLETED / READY / HEALTHY`.
2. Any regression resets the count.
3. A successful retained no-op shell probe after the third poll.
4. A separate retained 8 GiB free-disk probe before any upload.
5. Window expiry is terminal; a later READY signal cannot reopen execution.

The global create-to-delete ceiling remains 7,200 seconds. The harness remains
suite-first and independently repeats the 8 GiB disk gate before install.

## Proposal And Validation

- Opening commit: `2d9451d`; implementation commit: `e22e7e2`.
- Proposal byte SHA-256:
  `d92a9f8c507762d15b66bb1ff70f2227697985f3967610bd8323b69ae8f9df24`.
- Proposal semantic SHA-256:
  `e22529422a7d13957363b78365db0579f10cd13de920c09790ab7c0c4d1265e2`.
- Schema SHA-256:
  `2a4ae12487cb8d616d2b26647ecb4c694539a95a5ad3fc7834930d96375bd3a9`.
- Seventh harness SHA-256:
  `c185bf79846f3b406e53776071e82461352407b9166d99102077c1e0577c521e`.
- Exact rate and ceilings: `$1.98/hour`, 4,800-second inner harness,
  7,200-second create-to-delete, and `$3.96`, inside the inactive `$210`
  planning envelope.
- Mutation tests reject 219 scalar mutations, 258 deletions, extra fields,
  explicit compute authority, seventh retry, every prior type, historical
  rates, readiness-window/poll-count/poll-interval weakening, early upload,
  disk-threshold weakening, and prior harness aliases.
- Full authority-enabled local suite: pass, including both environment smokes.
- Static CUDA, artifact, Python compilation, Bash, shellcheck, diff, branch
  hygiene, manifest, receipt immutability, and workflow gates: pass.
- Branch hygiene from `7d1eba9`: eleven manifests and 68 immutable logs.
- Closing authenticated Brev inventory: `{"workspaces": null}`.
- No Brev create/start/exec/copy/stop/delete, upload, training, smoke, or export
  occurred in this slice.

## Evidence And Authority Boundary

The feedback acknowledgement proves only that a nonsecret report was sent.
The proposal remains `compute_authorized=false`; no Manager authority exists.
Catalog properties and stronger readiness gates do not prove that a future
shell will work or establish CUDA, M5, task, policy, candidate, held-out,
publication, activation, transfer, or physical success.

## Step-9 Flags For Reviewer

- Reconcile all three terminal timelines and verify the feedback report was
  nonsecret and limited to the readiness race.
- Recompute proposal/schema/harness/input/source hashes and exact accepted
  sixth-terminal chain.
- Verify the fresh Crusoe row, dry run, and previously-unused classification.
- Exercise the 900-second window, exact qualifying state, three-poll/15-second
  sequence, regression reset, no-op shell, 8 GiB disk, pre-upload, late-READY,
  no-retry, and receipt/teardown bindings.
- Re-run all local suites and confirm the stop sentinel and empty inventory.
- Do not create a Manager record or paid workspace.
