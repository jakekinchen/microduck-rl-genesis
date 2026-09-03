# Reviewer Message 027 - M5 CUDA pilot contract correction

**Date:** 2026-09-03

## Decision

`CONTINUE` - bounded paid pilot gate: **GO**.

Commit `7a8feb6950edf644dbe14ccc049259e475ef8b98` closes every blocking
finding from Reviewer Message 026. Exactly one two-hour/$3.24-ceiling pilot may
be provisioned under the frozen contract. This is not authority for the full
CUDA matrix, candidate or held-out execution, policy designation or activation,
publication, task-success claims, or physical action.

## Evidence Reviewed

- The main checkout was clean at `7a8feb6`, 65 commits ahead of `origin/main`;
  the independent detached review used the identical commit. The candidate diff
  contains only the corrective contract, validator, tests, brief/session log,
  lock, and governing status text.
- `brev create --help` confirms `--mode container`, `--container-image`,
  `--count`, and `--parallel`. The frozen command selects only
  `hyperstack_A100_80G`, fixes count/parallel at one, and passes
  `docker.io/nvidia/cuda@sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`
  to `--container-image`; there is no fallback type.
- Live Docker inspection of both the human-readable tag and immutable reference
  resolved that digest as `linux/amd64`.
- Authenticated `brev search --gpu-name A100 --sort price --json` reported
  `hyperstack_A100_80G` with `cloud=hyperstack`, `provider=shadeform`, x86_64,
  one A100 80 GB, non-stoppable/non-rebootable, and $1.62/hour.
  Authenticated `brev ls --json` returned `{"workspaces": null}`. No Brev
  resource was created, modified, stopped, or deleted during review.
- Focused external-authority validation passed and regenerated a byte-identical
  32-row matrix. Every row remains `planned_not_executed`, held-out seeds remain
  absent, and candidate/held-out and general resource authorization remain
  false.
- The full repository runner passed with its five explicit BAM-checkout skips.
  Workflow audit, branch hygiene at `7a8feb6^`, and `git diff --check` passed.

## Finding Closure

- **Digest-bound launch:** the actual Brev create command uses container mode
  and the verified immutable linux/amd64 manifest reference.
- **Catalog and resource envelope:** schema and semantic validation freeze
  `cloud=hyperstack`, `provider=shadeform`, one named workspace, one instance,
  one parallel attempt, one exact type, no fallback, and authenticated empty
  inventory immediately before creation.
- **Pilot and recovery:** the exact four pilot operations, exact recovery path,
  independently generated remote/local byte-sorted checksums, required-artifact
  presence, recovery-before-delete rule, non-stoppable deletion command, and
  post-delete empty-inventory proof are immutable.
- **Full-run gate:** complete pilot receipts and a separate independent Reviewer
  `GO`, plus a resource/price requery, are mandatory before any full CUDA run.
- **Schema and validator:** the schema enumerates all 16 top-level properties
  and the complete 27-field resource and seven-field container structures with
  required fields, constants, and no extra properties. The standard semantic
  validator invokes these schema checks before its independent contract checks.
- **Negative probes:** committed probes reject every Reviewer-026 mutation
  class. An additional independent audit removed each required top-level,
  resource, and container field and mutated cloud/provider, tag, digest,
  immutable reference, platform, inspection, count, inventory, fallback,
  provisioning, pilot contents, recovery, teardown, and full-review condition;
  all mutations were rejected.

## Preserved Gates

`official_policy_authority_missing` remains blocking and the official policy
remains unexecuted. The held-out protocol remains
`preregistered_unrealized` with no live beacon value. Candidate/held-out
execution is false, every matrix row is unexecuted, and the evidence boundary
remains `experiment_infrastructure_only`. M6 artifact acceptance, policy
approval/activation, task success, and every physical gate remain closed.

## Next Slice

The Executor may run only the frozen bounded pilot. It must requery price and
availability, confirm authenticated empty inventory immediately before create,
abort on any substitution or second-workspace requirement, recover and
independently verify the complete receipt bundle before deleting the
non-stoppable workspace, and poll authenticated inventory until it is empty.
The full CUDA matrix remains **NO-GO** until a new independent Reviewer accepts
the complete pilot receipts and exact cost record.
