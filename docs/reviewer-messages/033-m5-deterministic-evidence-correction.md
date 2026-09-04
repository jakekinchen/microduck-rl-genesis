# Reviewer Message 033 - M5 deterministic evidence correction re-review

**Date:** 2026-09-03

## Decision

**CONTINUE** - accept implementation `d741e60` against correction baseline
`7a79735` as the bounded resolution of Reviewer 032 and accept slice 032 at the
local deterministic-evidence class only.

This decision makes the draft third-pilot card eligible for later Manager
consideration. It does not authorize a third pilot, Brev provisioning, full
CUDA, candidate or held-out work, publication, policy activation, transfer, or
physical operation. Retain `<stop-orchestrator/>` at this separate Manager
authority boundary.

## Reviewer 032 Finding Closure

- `canonical_compiled_manifest()` deep-copies its input and applies fourteen-
  significant-digit canonicalization only while traversing
  `bodies[*].inertia_kg_m2`. No other manifest path is transformed.
- Reviewer 032's exact one-ULP `mass_kg` probe from
  `0.12345678901234567` to `0.12345678901234568` now remains unequal after the
  semantic projection. Independent companion probes confirmed the same for an
  inertial-position element and joint damping.
- The measured Darwin/Linux mesh-inertia pairs still converge. A `1e-9`
  inertia change remains unequal, and the eleven-decimal trajectory digest
  still detects a `1e-8` state change.
- Every retained raw compiled manifest and its frozen per-variant digest remain
  authenticated before the scoped semantic comparison. The correction did not
  rebaseline a manifest or existing fixture.

## Preserved Deterministic Gates

- The evaluator report retains truthful runtime provenance and raw trajectory
  SHA-256 while its cross-host comparison separately binds the eleven-decimal
  canonical row digest `25d48827...46e6`.
- Development bundle generation remains byte-identical for all five files
  across distinct output paths, Linux/x86-64 metadata, deliberate 25 ms versus
  1 ms measured inference timings, fixed zero synthetic latency, and one-sample
  offscreen rendering.
- The original A100 receipt retains the three terminal-negative failures. Its
  temporary repeated bundles and individual artifact hashes were discarded, so
  exact A100 artifact attribution remains unavailable and no A100 rerun is
  claimed.

## Immutability And Authority Review

- `evaluator/core.py`, evaluator config and development suite, frozen M5
  contract/lock/schema/matrix, task contracts, 61D observation, 14D action,
  50 Hz control, BAM lock, and evaluator thresholds are unchanged from
  `60a642a`.
- Pilot 028 manifest SHA-256 remains `1e8d4948...566b`; its accepted receipt
  tree is `6fe74588...04b` at both `0a0c2c9` and HEAD. The separate
  Manager-reconciliation blob remains `fd8531d7...90bc`.
- Pilot 031 manifest SHA-256 remains `90cbb024...3078`; its accepted receipt
  tree is `388858a5...d8d` at both `60a642a` and HEAD. Every entry in both
  manifests revalidated.
- The third-pilot proposal remains `compute_authorized=false`, and M5
  validation reports 32 planned rows with no candidate or held-out execution
  authority.

## Independent Validation

- Exact Reviewer-032 mass probe plus independent inertial-position and joint-
  damping probes - pass; all non-inertia changes remain visible.
- Measured inertia convergence, `1e-9` inertia rejection, and `1e-8` trajectory
  rejection - pass.
- Four focused tests with clean pinned BAM `62bd8ce` - pass: model
  reconciliation, evaluator core, evaluator bundle, and cross-platform
  determinism.
- Full authority-enabled local `tests/run_all.py` suite with exact BAM and the
  locked official MJLab Python - pass with no failures.
- Exact official MJLab adapter verification - pass; both BAM fixtures consumed
  with MJLab 1.3.0, MuJoCo 3.10.0, Warp 1.12.0, and MuJoCo Warp 3.8.1.
- M5 contract test and matrix validation - pass; 32 rows remain planned and
  unauthorized.
- `scripts/check_branch_hygiene.sh 60a642a` - pass; seven manifests and 53
  immutable logs.
- Both receipt manifests, workflow audit, and `git diff --check
  7a79735..7c7dabd` - pass.

## Next Authority Boundary

Slice 032 is closed only as local deterministic producer compatibility. M5
remains open. A Manager may separately consider the non-authorizing draft card,
but only a new durable Manager decision binding exact implementation, runtime,
resource, time, cost, and teardown terms could authorize one later pilot.
