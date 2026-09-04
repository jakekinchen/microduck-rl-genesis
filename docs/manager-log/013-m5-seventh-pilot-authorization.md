# Manager Log 013 - M5 seventh-pilot authorization

**Date:** 2026-09-04

## Decision

**AUTHORIZED / BOUNDED** - the user's standing bounded-compute authorization
authorizes exactly one execution of the independently accepted seventh-pilot
proposal. This authority becomes usable only after this record is committed.
The proposal remains `compute_authorized=false`; execution authority exists
only in this Manager record.

## Accepted Chain And Inputs

- Corrected handoff: `e3b9fb43e3509725c257c677b6dc307e12a663f9`.
- Reviewer 045 acceptance: `ad175f102fb8961dd7586ea2320acb5bdd497f19`.
- Proposal byte/semantic/schema SHA-256:
  `714da8cdd4e521e1ba0d088809ff568f29ec909b514d796a2d67c0a1c0564f53`,
  `604eb30d560cbb5045c551af5094dada621d23e0c92697defccccdc6532c8b4c`,
  `4d38202f7b97971b11af8d0e417fe0cef03ffa3a25b47d9aa1096104cfd970c7`.
- Harness/runtime/requirements SHA-256:
  `a960bfd3b88bf9bad74eb3a53c0460b2d96d42c372b01464d55bc2c103f60571`,
  `c9f64efb52d7ae0c220ff0f03c9b207af11a792251bd1eb69ef9357e1658f46d`,
  `e813cbdaec942ad2de23d70532b664286bed4f12965f5b933dd8c9ff342b749f`.
- Genesis/walking/backflip bundle SHA-256:
  `8469272fd8b6ce522df294ef2ad0ee7f0929af4053d0fb523dc697e23fa2123a`,
  `9ac470615728680934ab68293b474371b4d66df03925f46195397d954e3c7118`,
  `aa893ba80f3b162fff094ef5151e66b9f963ad1dc8f2c49cf92bd47ae2ddaae0`.
- Immutable image:
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`.

## Resource And Limits

Create exactly one `gpu_1x_a100_sxm4` Lambda Labs workspace named
`microduck-m5-pilot7-20260904`: x86_64, one A100 40 GB, 30 vCPUs,
200 GiB RAM, fixed 512 GB disk, 600-second advertised estimate,
non-stoppable, rebootable, no flexible ports, at exactly `$2.388/hour`.
No fallback, substitution, retry, second workspace, prior type, H100, or
multi-GPU. Hard create-to-delete ceiling: 7,200 seconds / `$4.776`.
Harness timeout: 4,800 seconds.

## Readiness And Execution

Recheck all hashes, clean sources, twice-reproduced bundles, exact live row,
immutable dry run, and empty inventory. Close readiness within 900 seconds only
after three consecutive authenticated exact-ID polls at least 15 seconds apart,
each `RUNNING / COMPLETED / READY / HEALTHY`, resetting on regression; then
retain a successful no-op shell and separate proof of at least 8 GiB free
before upload. A later READY after terminal cannot reopen execution.

Only after all readiness gates may one verified input set be uploaded and the
seventh harness invoked once with
`CONTRACT_COMMIT=7bc61d5b5b4c3275a9b2b0e5bfeb282b687ce55a`.
The harness runs the full suite first, then only the four frozen 64x5
public-development smokes and named normalized ONNX exports.

## Failure, Receipt, And Teardown

Any readiness-window, provisioning, shell, disk, checksum, runtime, suite,
smoke, export, receipt, timeout, or cost failure is terminal. Preserve primary
readiness/probe logs. Recover and independently verify the complete receipt
appropriate to whether a shell exists. Delete only the exact workspace ID and
poll authenticated inventory to empty on every terminal path. This
non-stoppable resource must never remain allocated.

## Not Authorized

Full CUDA matrix, candidate or held-out seeds, publication, activation,
transfer, physical operation, fallback, substitution, retry, second workspace,
H100, multi-GPU, or overspend. Every result requires independent Reviewer
judgment.
