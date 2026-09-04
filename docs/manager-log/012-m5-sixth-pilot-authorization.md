# Manager Log 012 - M5 sixth-pilot authorization

**Date:** 2026-09-04

## Decision

**AUTHORIZED / BOUNDED** - the user's standing bounded-compute authorization,
relayed after Reviewer 042 acceptance, authorizes exactly one execution of the
independently accepted sixth-pilot proposal.

This one-use authority becomes usable only after this record is committed. The
proposal remains immutable and `compute_authorized=false`; execution authority
exists only in this Manager record. No prior authorization is reused.

## Accepted Chain And Immutable Inputs

- Accepted sixth-pilot corrected handoff:
  `eb52e63f5e3379cf20b30f42b2ac58e72c5a6604`.
- Reviewer 042 acceptance record commit:
  `f24f63ab19762e45633514ead2d91d4c2b72ee0a`.
- Proposal: `experiments/m5/sixth-pilot-proposal-v1.json`.
- Proposal byte SHA-256:
  `cca90ab98458df37668b1c8391705a196693d2ecddc4d9a349af848d37f052cc`.
- Proposal semantic SHA-256:
  `09f2277544dadef850fe9d3f7e71e00a7adc46f6d4aa8ed01bde3e0fede1050e`.
- Schema SHA-256:
  `dfc396e245013563814b0f908807042b9b430914cd5a7a84bf32953b75defdc2`.
- Sixth-pilot harness SHA-256:
  `7b6e2d324fd6d72fbf810daaafe48295b7a2b7dd96228a2a2975962eb818085f`.
- Runtime contract SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- CUDA requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Source bundles:
  - Genesis `7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`:
    `1754b718029721f13cd94a232d092720f62342e51f45f88a8cb11d02d2b7fb39`.
  - Official walking `109e06d4ce4921b635c5609e5304079fc30960ae`:
    `2e33c08e16fc6b5e3ef9eb41cb7c2d93d68b9ec08577417ebf8833f71c9ca719`.
  - Official backflip `8bde27eb141c8f14db05fc4370e536521203a98d`:
    `e43cf5d5c8faee37b64eb0a5594b37a4565a97e3a0e2686f27ae0777e09e1271`.
- Immutable linux/amd64 image:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.

## Exact Resource, Disk, And Cost Envelope

- Immediately before creation, authenticated `brev ls --json` must be empty.
- The fresh catalog row must exactly match
  `type=a2-highgpu-1g:nvidia-tesla-a100:1`, direct provider/cloud `gcp/gcp`,
  x86_64, one A100 with 40 GB VRAM, 12 vCPUs, 85 GiB RAM, 10 GB target disk,
  disk range 10-16,384 GB, disk price `$0.125/GB-month`, 420-second advertised
  boot, stoppable, non-rebootable, flexible ports, at exactly
  `$4.408062/hour`.
- The exact container-mode immutable-digest dry run must succeed immediately
  before creation.
- Create exactly one no-fallback workspace named
  `microduck-m5-pilot6-20260904`; no substitute type, retry, second
  workspace, prior failed type, H100, or multi-GPU resource.
- Hard ceilings: 4,800-second inner harness timeout; 7,200 seconds
  create-to-delete; `$8.816124` at the exact frozen rate.
- After shell readiness and before any upload, prove at least 8 GiB free at
  `/workspace`. Abort without upload if the gate fails. The harness must
  repeat the same gate before any package installation.

## Authorized Execution

- Recheck committed identities, hashes, isolated clean source clones,
  deterministic bundle equality, empty inventory, catalog row, and exact dry
  run immediately before creation; abort without provisioning on drift.
- Generate every exact source bundle twice with `pack.threads=1` and
  `pack.windowMemory=64m`; require byte equality and successful verification.
- Once the shell and pre-upload disk gate pass, copy one verified bundle set
  plus the exact sixth harness, verify every remote hash, and invoke the harness
  only once with
  `CONTRACT_COMMIT=7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`.
- Run the complete authority-enabled repository suite first inside the bound
  CUDA runtime.
- Only if the suite passes, run exactly the four frozen public-development
  smokes: Genesis and official MJLab walking/backflip, each at 64 environments
  for five iterations with frozen seeds, followed by four named normalized
  ONNX exports.
- Preserve runtime/source identities, disk preflight, configs, logs,
  checkpoints and exports if produced, elapsed time, conservative cost,
  terminal status, and evidence boundary.

## Mandatory Failure, Recovery, And Teardown

- Stop on every drift; provisioning, connectivity, disk, hardware, runtime,
  suite, smoke, export, receipt, checksum, timeout, overspend, or
  second-workspace failure; preserve an honest terminal receipt.
- Never replay the harness after its single invocation.
- If a shell exists, require remote sorted `SHA256SUMS`, recover the complete
  run-scoped receipt locally, independently regenerate the sorted local
  manifest, and require exact remote/local equality before deletion.
- If no shell ever exists, record remote-receipt unavailability explicitly and
  preserve complete local control-plane evidence.
- Delete only the exact workspace ID after verified recovery and poll
  authenticated `brev ls --json` until inventory is empty.
- Stoppability is a recovery option, not permission to leave paid compute
  allocated; exact-ID deletion and empty inventory remain mandatory.

## Explicitly Not Authorized

Fallback, substitution, retry, a second workspace, either previously failed
type, H100, multi-GPU, automatic overspend, candidate or held-out seeds, full
or 32-row CUDA matrix, publication, policy activation, transfer, or physical
operation. A successful smoke cannot promote itself to M5, task, policy,
transfer, or physical success. Every terminal result requires independent
Reviewer judgment.
