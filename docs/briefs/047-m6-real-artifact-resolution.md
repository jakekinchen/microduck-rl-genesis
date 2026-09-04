# Slice Brief 047 - M6 real artifact resolution

**Date:** 2026-09-04

## Objective

Record the durable external M5 provisioning blocker, then perform the smallest
network-read-only M6 slice: retrieve one official and one community policy
candidate by immutable revision, bind every attributable policy-manifest-v2
role by SHA-256, and retain exact missing roles without executing upstream
code or policies.

## Acceptance Criteria

- Treat the fourth through seventh pilots as four consecutive, independently
  reviewed provider/type provisioning failures. Do not propose or create an
  eighth workspace; leave authenticated Brev inventory empty.
- Retrieve only full-revision URLs for the official Pollen Robotics
  `alpha_walking.onnx` distribution and one community MicroDuck policy with an
  explicit model-card license and source/run declaration.
- Preserve the downloaded bytes, exact URLs, revisions, paths, sizes, and
  SHA-256 digests. Never import downloaded Python, load a checkpoint, initialize
  ONNX Runtime, run a policy, or execute upstream repository code.
- Resolve exactly the ten v2 roles: normalized ONNX, normalizer, source
  checkpoint, exporter, model, BAM, task, evaluator, evidence, and license.
  A role is bound only when exact immutable bytes are attributable; otherwise
  it must carry a non-empty blocker.
- Do not weaken policy manifest v2. Incomplete candidates must remain distinct
  resolution reports, emit no formal `policy-manifest-v2.json`, hold no
  authority, and reject lifecycle promotion.
- Provide offline mutation tests plus an explicit fresh network re-fetch that
  compares all pinned remote bytes to the committed copies.

## Evidence Boundary

Immutable retrieval and attribution audit only. Validation does not grant
artifact acceptance, library import, evaluation, publication, approval,
activation, task success, transfer, or physical authority.
