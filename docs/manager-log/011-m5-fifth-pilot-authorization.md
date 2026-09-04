# Manager Log 011 - M5 fifth-pilot authorization

**Date:** 2026-09-04

## Decision

**AUTHORIZED / BOUNDED** - the user's explicit paid-compute authorization,
relayed in the guardian handoff after Reviewer 040 acceptance, authorizes
exactly one execution of the independently accepted fifth-pilot proposal.

This one-use authority becomes usable only after this record is committed. The
proposal itself remains immutable and `compute_authorized=false`; execution
authority exists only in this Manager record. No prior authorization is reused.

## Accepted Chain And Immutable Inputs

- Accepted fifth-pilot proposal handoff: `9af3634`.
- Reviewer 040 acceptance record commit: `89d8a65`.
- Proposal: `experiments/m5/fifth-pilot-proposal-v1.json`.
- Proposal byte SHA-256:
  `1d27fd55dee168fcf4f54f38432b2bad65a067aef8f821c4e1746a2afaeca4b1`.
- Proposal semantic SHA-256:
  `dd62db31aa5e1dd6b35d1213b744342a17d1a1099008d5764b399dbcfbdb6d57`.
- Proposal schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- Fifth-pilot harness SHA-256:
  `2856fce10b8e829f9f290975621cbf900821b7f946fca02239cda79a41df5b29`.
- Runtime contract SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- CUDA requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Source bundles:
  - Genesis `7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`:
    `399b03e878002aeaf1aaa0bdf56efafedaebf337b88d78ba80aaf5af50d97eba`.
  - Official walking `109e06d4ce4921b635c5609e5304079fc30960ae`:
    `9937de2c47bbfaa8dee1a21e99728102164b416fa174ec0d107fee77c42fd4a6`.
  - Official backflip `8bde27eb141c8f14db05fc4370e536521203a98d`:
    `98e4642fd75b4b3f670391e679f788f8c722bc49d8c7ab27418d68efba8a207e`.
- Immutable linux/amd64 image:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.

## Exact Resource And Cost Envelope

- Immediately before creation, authenticated `brev ls --json` must be empty.
- A fresh catalog row must exactly match
  `type=massedcompute_A100_sxm4_80G_DGX`, provider `shadeform`, cloud
  `massedcompute`, x86_64, one A100 with 80 GB VRAM, 16 vCPUs, 160 GiB RAM,
  1,000 GB disk, non-stoppable, non-rebootable, at exactly `$1.656/hour`.
- The exact container-mode immutable-digest dry run must succeed immediately
  before creation.
- Create exactly one no-fallback workspace named
  `microduck-m5-pilot5-20260904`; no substitute type, second workspace,
  hyperstack retry, H100, or multi-GPU resource.
- Hard ceilings: 4,800-second inner harness timeout; 7,200 seconds
  create-to-delete; `$3.312` at the exact frozen rate.

## Authorized Execution

- Recheck committed identities, hashes, isolated clean source clones,
  deterministic bundle equality, empty inventory, catalog row, and exact dry
  run immediately before creation; abort without provisioning on drift.
- Generate every exact source bundle twice with `pack.threads=1` and
  `pack.windowMemory=64m`; require byte equality and successful verification.
- Copy one verified set plus the exact fifth harness, verify every remote hash,
  and invoke the harness only once with
  `CONTRACT_COMMIT=7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`.
- Run the complete authority-enabled repository suite first inside the bound
  CUDA runtime.
- Only if the suite passes, run exactly the four frozen public-development
  smokes: Genesis and official MJLab walking/backflip, each at 64 environments
  for five iterations with the frozen seeds, followed by the four named
  normalized ONNX exports.
- Preserve runtime/source identities, configs, logs, checkpoints and exports
  if produced, elapsed time, conservative cost, terminal status, and evidence
  boundary.

## Mandatory Failure, Recovery, And Teardown

- On every terminal path, stop on drift; provisioning, hardware, runtime,
  suite, smoke, export, receipt, checksum, timeout, overspend, or
  second-workspace failure; and preserve an honest terminal receipt.
- Never replay the harness after its single invocation.
- If a shell exists, require remote sorted `SHA256SUMS`, recover the complete
  run-scoped receipt locally, independently regenerate the sorted local
  manifest, and require exact remote/local equality before deletion.
- If no shell ever exists, record remote-receipt unavailability explicitly and
  preserve the complete local control-plane evidence instead.
- Delete only the exact workspace ID after verified recovery and poll
  authenticated `brev ls --json` until inventory is empty. This resource is
  non-stoppable and must never be left running.

## Explicitly Not Authorized

Fallback, substitution, a second workspace, hyperstack retry, H100, multi-GPU,
automatic overspend, candidate or held-out seeds, full or 32-row CUDA matrix,
publication, policy activation, transfer, or physical operation. A successful
smoke cannot promote itself to M5, task, policy, transfer, or physical success.
Every terminal result requires independent Reviewer judgment.
