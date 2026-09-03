# Executor log 027 - M5 CUDA pilot contract correction

**Date:** 2026-09-03

**Role:** Executor

**Brief:** `docs/briefs/027-m5-cuda-pilot-contract-correction.md`

## Corrected findings

- The exact Brev create command now uses `--mode container` and
  `--container-image` with the immutable linux/amd64 NVIDIA CUDA digest. Count
  and parallelism are each fixed at one, and the sole resource type is the
  preferred `hyperstack_A100_80G`.
- The catalog identity is corrected to `cloud=hyperstack` and
  `provider=shadeform`.
- The contract now requires authenticated empty inventory immediately before
  creation, workspace count one, and no fallback.
- Exact pilot contents, four-step remote/local recovery and independent
  checksum requirements, non-stoppable deletion, post-delete empty inventory,
  and conditional full-run Reviewer acceptance are immutable values.
- The JSON Schema now enumerates every top-level property and the full nested
  resource/container structure. The standard-library contract validator invokes
  the schema on every positive and negative validation, so no new runtime or
  network dependency was introduced.
- Negative tests now cover the Reviewer 026 mutations: cloud/provider, tag,
  digest, platform, inspection, count, inventory, fallback, provisioning,
  pilot contents, recovery/checksum, full-run condition, teardown, and extra
  unreviewed fields.

## Live read-only evidence

On 2026-09-03, authenticated
`brev search --gpu-name A100 --sort price --json` reported the preferred row as
`hyperstack_A100_80G`, `cloud=hyperstack`, `provider=shadeform`, x86_64, one
A100 80 GB, 28 vCPU, 120 GiB RAM, 850 GB disk, non-stoppable/non-rebootable,
and $1.62/hour. `brev ls --json` remained empty. No resource was created or
modified.

Docker registry inspection continued to return linux/amd64 manifest digest
`sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`
for the human-readable `12.8.1-cudnn-devel-ubuntu24.04` tag.

## Verification

```bash
.venv-apple/bin/python scripts/validate_m5_experiment.py \
  --matrix-output /tmp/microduck-m5-matrix-027.json
cmp -s /tmp/microduck-m5-matrix-027.json \
  experiments/m5/execution-matrix-v1.json
.venv-apple/bin/python tests/test_m5_experiment_contract.py
.venv-apple/bin/python tests/run_all.py
bash scripts/audit_autonomous_workflow.sh
bash scripts/check_branch_hygiene.sh
docker manifest inspect --verbose \
  nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04
brev search --gpu-name A100 --sort price --json
brev ls --json
git diff --check
```

Focused contract/schema/negative-mutation checks pass and the generated 32-row
matrix remains byte-identical, unexecuted, and candidate/held-out unauthorized.
The full repository runner passed with its five explicit BAM-dependent skips;
workflow audit, branch hygiene, and diff checks passed. Live Docker, Brev
catalog, and authenticated empty-inventory results matched the corrected
contract exactly.

## Evidence boundary and spend

Correction only. Spend remains $0 for slices 026-027, and authenticated Brev
inventory is empty. No candidate, held-out input, policy evaluation,
publication, activation, task-success claim, or physical action occurred. A new
independent Reviewer `GO` is mandatory before the paid pilot.
