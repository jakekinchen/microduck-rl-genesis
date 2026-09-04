# Reviewer Message 032 - M5 deterministic evidence correction

**Date:** 2026-09-03

## Decision

**NUDGE** - evidence anchor `100`.

Do not accept implementation `bac0375` or mark slice 032 complete yet. The
evaluator-report and development-bundle corrections satisfy their bounded local
determinism gates, but the compiled-model correction canonicalizes every float
in the manifest rather than only the measured MuJoCo mesh-inertia tails. That
is broader than the slice brief and can mask unapproved non-inertia drift.

This decision grants no Brev provisioning, third pilot, full CUDA, candidate,
held-out, publication, activation, transfer, or physical authority. The draft
third-pilot card remains `compute_authorized=false` and is not yet eligible for
Manager consideration.

## Blocking Finding

`scripts/reconcile_models.py:50-65` recursively rounds every float to fourteen
significant digits before the current compiled manifest is compared with the
retained manifest. Consequently body mass, inertial position, joint ranges,
armature, damping, friction loss, actuator ranges, and keyframe values receive
the same tolerance as the measured mesh-inertia fields.

An independent negative probe changed only `bodies[*].mass_kg` from
`0.12345678901234567` to `0.12345678901234568`. The raw manifests were unequal,
but `canonical_compiled_manifest()` made them equal. The checked-in regression
uses only an `inertia_kg_m2` example and therefore does not catch this scope
expansion.

`tests/test_model_reconciliation.py:54-57` does continue to authenticate every
retained raw manifest and its frozen per-variant digest before performing the
semantic comparison. Preserve that raw authentication. Narrow only the
semantic projection so fourteen-significant-digit canonicalization applies to
the measured `bodies[*].inertia_kg_m2` values; require exact equality everywhere
else. Add a negative regression proving a floating-tail change in at least one
non-inertia field remains visible, then rerun the same focused and full
authority gates.

## Accepted Local Evidence

- All four focused tests passed with clean BAM authority `62bd8ce`: model
  reconciliation, evaluator core, evaluator bundle, and cross-platform
  determinism.
- The full local authority suite passed with exact BAM and the locked official
  MJLab environment. The separate official adapter check consumed both pinned
  BAM fixtures using MJLab 1.3.0, MuJoCo 3.10.0, Warp 1.12.0, and MuJoCo Warp
  3.8.1.
- The evaluator report retains truthful runtime provenance and the raw
  trajectory digest. Its cross-host check separately binds the eleven-decimal
  canonical row digest `25d48827...46e6`, and a `1e-8` state change remains
  detectable.
- Development bundle generation produced identical hashes for all five files
  across different output paths with Linux/x86-64 metadata, deliberate 25 ms
  versus 1 ms measured inference timings, fixed zero synthetic latency, and
  one-sample offscreen rendering.
- `evaluator/core.py`, evaluator config and development suite, the frozen M5
  contract/lock/schema/matrix, task contracts, 61D observation, 14D action,
  50 Hz control, and BAM lock/threshold inputs are unchanged from `60a642a`.
  The only fixture change is the addition of
  `cross-platform-determinism-v1.json`; no existing fixture was rebaselined.
- Both accepted pilot manifests validate in full. Pilot 028 retains manifest
  SHA-256 `1e8d4948...566b` and tree `6fe74588...04b`; pilot 031 retains manifest
  SHA-256 `90cbb024...3078` and tree `388858a5...d8d`. Each tree matches its
  accepted commit, and the separate pilot-028 Manager-reconciliation blob
  remains `fd8531d7...90bc`.
- M5 contract validation passed with 32 planned rows and no candidate or
  held-out execution authority. Branch hygiene from `60a642a` passed with seven
  manifests and 53 immutable logs. Workflow audit and `git diff --check
  60a642a..0a5db72` passed.

## Evidence Boundary And Limitation

The preserved A100 log proves the original three failures but the repeated
development bundles and their individual first/second artifact hashes were
discarded. The exact failing A100 artifact cannot be attributed after the fact,
and no A100 rerun occurred. The passing evidence here is local deterministic
producer compatibility only.

Retain `<stop-orchestrator/>`. After the bounded compiled-manifest scope fix,
an independent Reviewer must decide again before the non-authorizing proposal
can become eligible for a separate Manager decision.
