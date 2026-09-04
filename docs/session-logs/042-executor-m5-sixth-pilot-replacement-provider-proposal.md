# Executor Session 042 - M5 sixth-pilot replacement-provider proposal

**Date:** 2026-09-04

## Baseline And Boundary

- Reviewer 041 accepted the fifth pilot only as terminal-negative provisioning/
  connectivity evidence at commit `49f1177`.
- Manager authority 011 is consumed and cannot be reused.
- This slice is local and non-authorizing. No Brev creation, paid compute,
  upload, remote execution, or training is permitted.

## Live Catalog And Selection Evidence

- At `2026-09-04T06:27:44Z`, authenticated `brev ls --json` returned
  `{"workspaces": null}`.
- The unused exact type `a2-highgpu-1g:nvidia-tesla-a100:1` was present as a
  direct GCP/GCP x86_64 row: one A100 40 GB, 12 vCPUs, 85 GiB RAM, flexible
  ports, stoppable, non-rebootable, 420-second advertised boot time, 10 GB
  target disk, and `$4.408062/hour`.
- No unused A100-class row advertised a faster boot time than both previously
  failed 390-second rows. The selection therefore claims only materially
  better catalog-visible connectivity/recovery indicators: direct provider,
  flexible ports, and stoppability. It does not claim proven shell readiness.
- The exact immutable-container command returned the selected type under
  `--dry-run`; no workspace was created. The proposed unique workspace is
  `microduck-m5-pilot6-20260904`, strict one-instance/one-GPU with no fallback,
  substitution, retry, or second workspace.

## Deterministic Source-Bundle Freeze

Each source was bundled twice from isolated clones using the proposal's unique
`refs/m5-pilot6/*` ref, `pack.threads=1`, and `pack.windowMemory=64m`. Each pair
was byte-identical and each first bundle passed `git bundle verify`:

- Genesis `7bc61d5`:
  `1754b718029721f13cd94a232d092720f62342e51f45f88a8cb11d02d2b7fb39`.
- Official walking `109e06d`:
  `2e33c08e16fc6b5e3ef9eb41cb7c2d93d68b9ec08577417ebf8833f71c9ca719`.
- Official backflip `8bde27e`:
  `e43cf5d5c8faee37b64eb0a5594b37a4565a97e3a0e2686f27ae0777e09e1271`.

No bundle was uploaded.

## Proposal And Guards

- Opening commit: `e10a68d`; proposal implementation commit: `ae3729f`.
- Reviewer NUDGE on handoff `c0fe5ab` found that the machine-readable workspace
  did not independently prohibit retrying the proposed sixth pilot. Correction
  commit `fd19eac` adds `workspace.retry_allowed=false`, explicit
  `sixth_pilot_retry` prohibition, semantic validation, and direct mutation
  probes.
- Proposal byte SHA-256:
  `cca90ab98458df37668b1c8391705a196693d2ecddc4d9a349af848d37f052cc`.
- Proposal semantic SHA-256:
  `09f2277544dadef850fe9d3f7e71e00a7adc46f6d4aa8ed01bde3e0fede1050e`.
- Schema SHA-256:
  `dfc396e245013563814b0f908807042b9b430914cd5a7a84bf32953b75defdc2`.
- Sixth-specific harness SHA-256:
  `7b6e2d324fd6d72fbf810daaafe48295b7a2b7dd96228a2a2975962eb818085f`.
- The proposal binds the accepted fifth-pilot terminal chain and receipt,
  immutable image and inputs, suite-first order, four public-development 64x5
  smokes, named normalized ONNX retention, exact-ID teardown, two-hour cap,
  and exact `$8.816124` ceiling inside the `$210` total planning envelope.
- Both `hyperstack_A100_80G` and
  `massedcompute_A100_sxm4_80G_DGX` retries are prohibited.
- Retrying the proposed sixth pilot is independently prohibited in both the
  workspace block and the prohibition set.
- The 10 GB catalog target-disk risk is explicit. A future authorized operator
  must prove at least 8 GiB free before any upload; the sixth-specific harness
  independently repeats the same gate before package installation and retains
  `disk-preflight.json` on every terminal path.

## Validation

- Exact proposal validator and mutation suite: pass with 175 scalar mutations,
  205 deletions, extra-field and explicit authority rejection, sixth-pilot
  retry rejection, both prior type rejections, both historical-rate rejections,
  disk-threshold weakening rejection, prior-alias rejection, and native-name
  receipt attestation.
- Full authority-enabled `.venv-apple/bin/python tests/run_all.py`: pass with
  clean BAM `62bd8ce`, official walking `109e06d`, locked official MJLab
  Python, and `GS_ENABLE_ZEROCOPY=1`; both environment smokes pass.
- Static CUDA runtime, artifact contract, Python compilation, Bash syntax,
  shellcheck, and diff checks: pass.
- `scripts/check_branch_hygiene.sh 49f1177`: pass with ten manifests and 68
  immutable receipt logs.
- All tracked receipt manifests revalidated and
  `git diff --quiet 49f1177 -- receipts` passes.
- Autonomous workflow audit: clean.
- Closing authenticated Brev inventory: `{"workspaces": null}`.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export, or
  accepted-receipt mutation occurred.

## Evidence And Authority Boundary

This slice proves only a locally reproducible non-authorizing proposal.
`compute_authorized=false`; no Manager authority exists. Catalog properties and
dry-run acceptance do not prove shell readiness, CUDA compatibility, M5, task,
policy, candidate, held-out, publication, activation, transfer, or physical
success.

## Reviewer Outcome

The independent Reviewer first returned NUDGE on `c0fe5ab`, then returned
CONTINUE on corrected handoff `eb52e63`. Reviewer Message 042 records the exact
accepted hashes and confirms the full suite, live catalog, receipt integrity,
workflow, stop sentinel, and empty Brev inventory. The program stops here at a
fresh Manager boundary; Reviewer acceptance grants no compute authority.

## Step-9 Flags For Reviewer

- Recompute proposal/schema/harness/input/source-bundle hashes and the accepted
  fifth-pilot terminal authority chain.
- Confirm direct GCP selection and all live catalog fields, while rejecting any
  claim that the 420-second row has proven shell readiness or faster boot.
- Exercise every mutation/deletion probe, both failed-type prohibitions,
  explicit sixth-pilot retry prohibition, historical-rate rejection,
  native-name receipt attestation, and the 8 GiB disk gate before install.
- Re-run the full authority suite, receipt manifests, branch hygiene from
  `49f1177`, accepted-receipt immutability, workflow audit, and empty inventory.
- Retain the stop sentinel. Do not create a Manager record or Brev workspace.
