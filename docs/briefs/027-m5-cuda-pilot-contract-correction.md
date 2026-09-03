# Slice Brief 027 - M5 CUDA pilot contract correction

**Date:** 2026-09-03

## Objective

Correct every `100` and `75` finding in Reviewer Message 026 so the bounded paid
pilot is mechanically digest-bound and its cost, inventory, recovery, teardown,
and later full-run conditions fail closed.

## Acceptance Criteria

- The exact Brev create command uses container mode and the immutable
  linux/amd64 NVIDIA CUDA manifest reference, with count/parallel fixed at one
  and no fallback type.
- Record the authenticated catalog correctly as `cloud=hyperstack` and
  `provider=shadeform`.
- Require an empty authenticated inventory immediately before creation and
  prohibit a second workspace or alternate GPU/type.
- Freeze exact pilot contents, recovery paths, independent remote/local
  checksum comparison, non-stoppable deletion, and post-delete empty inventory.
- Keep full CUDA compute conditioned on an independent pilot-receipt Reviewer
  `GO`; keep candidate/held-out execution false in this amendment.
- Expand the JSON Schema to cover every top-level field and the complete
  resource/container structure; invoke it from the standard validator without
  adding a network/runtime dependency.
- Add negative probes for cloud/provider, image tag/digest/platform/inspection,
  count/inventory/no-fallback, provisioning, pilot contents, recovery/checksum,
  teardown, and full-review conditions.
- Rerun all slice-026 verification plus live registry/catalog/inventory checks,
  then obtain a new independent Reviewer decision before provisioning.

## Evidence Boundary

Contract correction only. No Brev workspace creation, candidate/held-out
execution, policy designation or evaluation, task-success claim, publication,
activation, or physical action.
