# Manager Log 006 - M5 second-pilot proposal

**Date:** 2026-09-03

## Authority

This entry records a proposal only. `compute_authorized=false`; it grants no
Brev creation, training, candidate execution, held-out realization, or policy
action. A new durable Manager authorization is required after independent
Reviewer acceptance of slice 029.

## Runtime reconciliation

- Terminal pilot 028 paired frozen source `93cd5f2` with Genesis 1.2.2. The
  exact 1.2.2 wheel has SHA-256 `567d49f2...a0fb9a`; its rigid solver source has
  SHA-256 `cf664fdc...11c7e` and lacks the required `dyn_state` assignment.
- Genesis World 1.3.3 is published as the platform-independent wheel
  `genesis_world-1.3.3-py3-none-any.whl`, SHA-256
  `74fcece3...9f74b3bf`, with PyPI trusted-publishing provenance to release tag
  commit `76f8f5b3457e7c6d6a078de2244066f9a8694c45`.
- That tagged rigid solver source has SHA-256 `39e2af4c...58fd183` and assigns
  `self.dyn_state = self.data_manager.dyn_state`, matching both frozen source
  consumers without changing their semantics.
- Primary sources:
  `https://pypi.org/project/genesis-world/1.3.3/` and
  `https://github.com/Genesis-Embodied-AI/genesis-world/blob/76f8f5b3457e7c6d6a078de2244066f9a8694c45/genesis/engine/solvers/rigid/rigid_solver.py`.

## Local proof boundary

The exact 1.3.3 solver source hash matches the installed Apple environment,
whose full suite passes. Linux x86-64/Python 3.12/cu128 resolution produces a
126-package, hash-locked dependency set for the Ubuntu 24.04/glibc 2.39
container. A local x86-64 Colima probe could not start because QEMU is absent;
no VM was created and no dependency was installed to conceal that limitation.
This slice can prove source/API and resolver compatibility, not CUDA execution.

## Current proposal

At `2026-09-04T00:21:18Z`, the authenticated Brev catalog still listed one
`hyperstack_A100_80G` from `provider=shadeform`, `cloud=hyperstack`: one
x86-64 A100 80 GB, 28 vCPUs, 120 GiB RAM, non-stoppable/non-rebootable, at
`$1.62/hour`. The precise proposal is frozen in
`experiments/m5/second-pilot-proposal-v1.json`: one no-fallback workspace,
two hours / `$3.24` create-to-delete hard ceiling, 4,800-second inner harness
timeout, mandatory failure receipts, verified recovery, deletion, and empty
inventory. Availability and price must be requeried; this entry is not
authorization to run it.
