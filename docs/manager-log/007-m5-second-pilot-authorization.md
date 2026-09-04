# Manager Log 007 - M5 second-pilot authorization

**Date:** 2026-09-03

## Decision

**AUTHORIZED / BOUNDED** - the user's standing 2026-09-03 instruction to keep
the work going and authorize what is needed, together with the guardian's
explicit bounded-compute mandate, is accepted as fresh Manager authorization
for exactly the independently reviewed M5 second-pilot proposal below.

This authorization becomes usable only after this record is committed. It does
not amend the proposal, reuse the consumed first-pilot authorization, or grant
authority beyond the named smoke pilot.

## Immutable Inputs

- Reviewed repository state: `764d923` (Reviewer 030), accepting Executor
  implementation `ba319ee`.
- Proposal: `experiments/m5/second-pilot-proposal-v1.json`.
- Proposal SHA-256:
  `f020df3f1cfb29b160ec86765a06e184a696af940fe62d690fda371653aa536e`.
- Runtime contract SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- CUDA requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Container:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`
  on `linux/amd64`.

## Exact Resource Envelope

- Immediately before creation, authenticated `brev ls --json` must report
  `{"workspaces": null}`.
- A fresh catalog row must exactly match `type=hyperstack_A100_80G`,
  `provider=shadeform`, `cloud=hyperstack`, `arch=x86_64`, one A100 with 80 GB
  VRAM, non-stoppable, non-rebootable, and price no greater than `$1.62/hour`.
- Create exactly one no-fallback workspace named
  `microduck-m5-pilot2-20260903`; no second workspace or substitute type.
- Hard ceiling: two hours create-to-delete and `$3.24`; inner harness timeout
  at most 4,800 seconds.

## Authorized Execution

- Copy and verify the exact reviewed source bundles and harness.
- Run the full applicable repository suite inside the bound CUDA runtime.
- Only after that suite passes, run the frozen public-development smoke inputs:
  walking and backflip at 64 environments for five iterations on each bound
  backend, with the predetermined public seeds already named by the harness.
- Record runtime identities, configs, checkpoints, normalized ONNX exports,
  logs, elapsed time, cost bounds, terminal status, and evidence boundary.

## Mandatory Failure And Teardown Behavior

- On drift, preflight failure, suite failure, smoke failure, timeout, or receipt
  failure, stop execution and preserve a terminal-negative receipt.
- Generate remote `SHA256SUMS` even on failure, recover the complete run-scoped
  receipt, independently regenerate the sorted local manifest, and require
  exact remote/local equality before deletion.
- Delete the exact non-stoppable workspace after verified recovery and poll
  authenticated `brev ls --json` until inventory is empty. A remaining paid
  workspace is a blocking failure and must be cleaned up proactively.

## Explicitly Not Authorized

Candidate or held-out seeds, the 32-row/full CUDA matrix, the 104-hour/$210
envelope, any additional or substitute workspace, publication, policy
activation, transfer, physical operation, or promotion from smoke output to
task success or physical authority. A successful pilot still requires an
independent Reviewer decision before any later compute may be considered.
