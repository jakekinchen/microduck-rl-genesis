# Manager Log 010 - M5 fourth-pilot authorization

**Date:** 2026-09-03

## Decision

**AUTHORIZED / BOUNDED** - the user's standing instruction to continue the
durable Executor/Reviewer loop, together with the guardian's explicit exact
fourth-pilot mandate, authorizes exactly the independently reviewed proposal
below.

This one-use authority becomes usable only after this record is committed. The
accepted proposal remains immutable and `compute_authorized=false`; authority
for one execution lives only in this Manager record. No prior authorization is
reused.

## Immutable Inputs

- Accepted evaluator implementation: `4a743bb`.
- Accepted evaluator Reviewer/HEAD: `7bc61d5`.
- Accepted proposal review commit/HEAD: `125493c` (Reviewer 036).
- Proposal: `experiments/m5/fourth-pilot-proposal-v1.json`.
- Proposal byte SHA-256:
  `0513d276aa6ca591e5a4232ffe914a5b9107910a7366b397a77e421df3a09ec2`.
- Proposal semantic SHA-256:
  `692f1d3d884b8e47ef485f0a9eb9974f6e25cb305965f89fe940850367281b5d`.
- Pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- Runtime contract SHA-256:
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`.
- CUDA requirements lock SHA-256:
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Source bundles:
  - Genesis `7bc61d5`:
    `e35c912931c1f163ead8c039cb3efce18a3af3319f781ddf3eac201eaf05857f`.
  - Official walking `109e06d`:
    `0bf67acef9a039536b8d5dc1738260298ea9d08ecddaeaa7fbe6cd0fcbd136bb`.
  - Official backflip `8bde27e`:
    `94d0f59fc1c9aa3a23bdc7859a17e6001c8a8c98cef2aeb3dc39d952a37b9246`.
- Immutable linux/amd64 image:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.

## Exact Resource Envelope

- Immediately before creation, authenticated `brev ls --json` must report
  `{"workspaces": null}`.
- A fresh catalog row must exactly match `type=hyperstack_A100_80G`,
  `provider=shadeform`, `cloud=hyperstack`, `arch=x86_64`, one A100 with 80 GB
  VRAM, non-stoppable, non-rebootable, at no more than `$1.62/hour`.
- Create exactly one no-fallback workspace named
  `microduck-m5-pilot4-20260904`; no substitute type, second workspace, H100,
  or multi-GPU resource.
- Hard ceilings: 4,800-second inner harness timeout, 7,200 seconds
  create-to-delete, and `$3.24` at the frozen maximum price.

## Authorized Execution

- Recheck clean source state, exact committed identities and hashes, exact
  proposal, empty inventory, and catalog row immediately before creation;
  abort without provisioning on drift.
- Generate each exact source bundle twice with the proposal's deterministic
  pack settings, require byte equality, verify the bundles, copy one set plus
  the exact harness, and verify all remote hashes before execution.
- Run the complete authority-enabled repository suite inside the immutable CUDA
  runtime with `CONTRACT_COMMIT=7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`.
- Only if the suite passes, run the four frozen public-development smokes:
  walking and backflip at 64 environments for five iterations on Genesis and
  official MJLab, followed by the four named normalized ONNX exports.
- Preserve source/runtime identities, configs, logs, checkpoints and exports if
  produced, elapsed time, conservative cost, terminal status, and evidence
  boundary.

## Mandatory Failure And Teardown Behavior

- On any input/image/catalog/hardware/runtime drift; preflight, suite, smoke,
  export, receipt, checksum, timeout, overspend, or second-workspace condition,
  stop and preserve a complete terminal-negative receipt.
- Invoke the harness only once for the bound receipt ID; do not allow a wrapper
  reconnect to replay it.
- Produce remote sorted `SHA256SUMS` on every terminal path, recover the entire
  run-scoped receipt locally, independently regenerate a sorted local manifest,
  and require exact remote/local equality before deletion.
- Delete only the exact workspace ID after verified recovery and poll
  authenticated `brev ls --json` until inventory is empty. This non-stoppable
  resource must not be left running; cleanup requires no further confirmation.

## Explicitly Not Authorized

Candidate or held-out seeds, a full or 32-row CUDA matrix, publication, policy
activation, transfer, physical operation, H100, multi-GPU, substitution,
fallback, a second workspace, automatic overspend, or promotion from a smoke
outcome to M5, task, policy, transfer, or physical success. Do not continue to
full CUDA in this slice, even if all four smokes pass. Every outcome requires
independent Reviewer judgment.
