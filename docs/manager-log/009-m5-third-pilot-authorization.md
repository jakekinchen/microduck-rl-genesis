# Manager Log 009 - M5 third-pilot authorization

**Date:** 2026-09-03

## Decision

**AUTHORIZED / BOUNDED** - the user's standing instruction to continue the
durable Executor/Reviewer loop and take on the latest agent's tasks, together
with the guardian's explicit bounded-compute mandate, is accepted as fresh
Manager authorization for exactly the independently reviewed M5 third smoke
pilot below.

This authorization becomes usable only after this record is committed. The
historical proposal card remains `compute_authorized=false`; it is a
non-authorizing input, and authority for this one execution lives only in this
Manager record. No prior pilot authorization is reused.

## Immutable Inputs

- Reviewed implementation: `d741e60`.
- Reviewer/contract HEAD: `2376821` (Reviewer 033).
- Proposal: `experiments/m5/third-pilot-proposal-card.md`.
- Proposal SHA-256:
  `5ab9cfa4ddd3015483abcae8d3fc015fbd91a0934691c4f2dc886723d52ee4f9`.
- Pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Runtime contract SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- CUDA requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Immutable linux/amd64 container:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.

## Exact Resource Envelope

- Immediately before creation, authenticated `brev ls --json` must report
  `{"workspaces": null}`.
- A fresh catalog row must exactly match `type=hyperstack_A100_80G`,
  `provider=shadeform`, `cloud=hyperstack`, `arch=x86_64`, one A100 with 80 GB
  VRAM, non-stoppable, non-rebootable, and price no greater than `$1.62/hour`.
- Create exactly one no-fallback workspace named
  `microduck-m5-pilot3-20260904`; no second workspace or substitute type.
- Hard ceiling: two hours create-to-delete and `$3.24`; inner harness timeout
  at most 4,800 seconds.

## Authorized Execution

- Recheck clean source state, exact hashes, empty inventory, and the exact
  catalog row immediately before creation; abort without provisioning on drift.
- Copy and verify the exact reviewed source bundles and byte-identical harness.
- Run the complete applicable repository suite inside the bound CUDA runtime.
- Only if that suite passes, run the frozen four public-development smokes:
  walking and backflip at 64 environments for five iterations on each bound
  backend, followed by normalized ONNX exports.
- Record runtime identities, exact inputs, configs, logs, checkpoints and
  exports if produced, elapsed time, conservative cost, terminal status, and
  the evidence boundary.

## Mandatory Failure And Teardown Behavior

- On source, hash, image, catalog, hardware, or runtime drift; preflight, suite,
  smoke, export, receipt, or checksum failure; timeout; overspend; or any need
  for a second workspace, stop and preserve a terminal-negative receipt.
- Prevent reconnects from launching the harness more than once for the bound
  receipt ID.
- Generate the remote sorted `SHA256SUMS` on every terminal path, recover the
  complete run-scoped receipt, independently regenerate the sorted local
  manifest, and require exact equality before deletion.
- Delete the exact non-stoppable workspace after verified recovery and poll
  authenticated `brev ls --json` until inventory is empty. Cleanup remains
  mandatory and requires no further confirmation.

## Explicitly Not Authorized

Candidate or held-out seeds, any full or 32-row CUDA matrix, publication,
policy activation, transfer, physical operation, H100, multi-GPU, fallback,
substitute or additional workspaces, a fourth pilot, or promotion from smoke
output to M5, task, policy, transfer, or physical success. Every outcome still
requires an independent Reviewer decision.
