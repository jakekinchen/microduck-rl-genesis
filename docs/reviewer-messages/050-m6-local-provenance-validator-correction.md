# Reviewer Message 050 - M6 local provenance validator correction

**Date:** 2026-09-04

## Decision

**CONTINUE** - accept exact Executor handoff
`263bbb7982284ba7ddcd1bb6b4c9bcdcd5beb545` from Reviewer base
`18e79c6a727d503cb03e30ff90c7708b95ab0b9c` strictly as the corrected local
provenance receipt and validator for the previously substantiated archaeology.

Required corrections: none.

This acceptance grants no policy-manifest completion, artifact import, policy
execution, evaluation, publication, approval, activation, transfer, hardware,
paid-compute, retry, replacement, or eighth-pilot authority.

## Receipt Preservation And Integrity

- The rejected v1 receipt at
  `receipts/m6/provenance/20260904-local-provenance-archaeology/` is unchanged
  byte-for-byte from Reviewer base. Its seven payloads still verify and its
  `SHA256SUMS` SHA-256 remains
  `21a4521adb629f88a3e2a28875904c9dc749a7d3d13f79c1ad25e38decc4bf87`.
- The versioned v2 receipt contains exactly seven manifest-covered payloads;
  every listed digest verifies. Its `SHA256SUMS` SHA-256 is exactly
  `48a400724c942e723c2dbbe78a71480e9261cd764fc56207245a86df99854207`.
- Independent reproduction from accepted history base
  `321f0a9396b7596e62a0834d79c167a9fe8ce32a` finds exactly 150 ancestry
  commits and 150 first-parent commits. Dynamic refs are excluded and public
  branches are audited separately. Each of the five target paths still has
  only parentless root commit `8659972...` in that fixed ancestry.

## Exact Semantic Bindings

- The license record binds declaration commit
  `fc1697699c478ed4f67373808a23caccc6bed785`, tree `86e21fa...`, parent
  `1e79c29...`, README blob `728e4c5...`, README SHA-256 `460bff8...`, exact
  `3D model files` scope, and contemporaneous ball blob `42c3278...`.
  Independent Git-object checks reproduce source -> declaration -> later
  `7831c514...` change ancestry and the exact later declared revision.
- Each media record is equality-bound to its file digest, container/codec,
  dimensions, duration, frame count, encoder tags, null attribution tags, and
  `authority=none`. Fresh hashes and `ffprobe` inspection reproduce both
  records without adding production or license authority.
- Each public repository record is equality-bound to its exact branch names
  and heads, empty tags/releases/Actions artifacts, and root-only target-path
  histories. A fresh anonymous GitHub audit reproduces all four branch heads
  and all 20 branch/path histories.
- The meniuniu record separately binds policy path
  `policies/microduck_walk_macos_scratch_seed1.onnx`, SHA-256
  `ece00bc0169e7daafe7d2071f1f42eb461c6a31e5614a798ae1a824d3a3a5388`,
  different-lineage disposition, and the README statement that the original
  policies are inference-only positive controls rather than outputs or
  evidence from the Mac run.
- The root-tree source-exclusion map is exact and keeps all eight authority
  fields false. The action map is exact and keeps download, credential,
  import/parse, load, execution, evaluation, training, publication,
  activation, and compute actions false.

## Adversarial And Full Validation

- Independent rehashed mutations of the v2 receipt reject upstream license
  digest and scope drift, removed branch coverage, inverted root-only history,
  false meniuniu positive-control wording, media digest drift, a 153-commit
  history count, dynamic-ref inclusion, separate-policy digest drift, missing
  source-exclusion coverage, and missing action coverage.
- Focused receipt validation, its strengthened mutation suite,
  file-provenance tests, provenance regeneration, and Python compilation pass.
  Inventory reproduces exactly 65 complete / 0 partial / 5 missing with
  `fully_resolved=false`.
- The full authority-enabled `tests/run_all.py` suite passes with the pinned
  BAM checkout, exact official MicroDuck checkout, official MJLab Python,
  Apple zero-copy gate, both environment smokes, and final
  `tous les tests passent`.
- Diff checks, branch hygiene from `18e79c6...`, and workflow audit pass.
  Branch hygiene reports 15 manifests and 71 immutable logs; earlier Reviewer,
  Manager, and v1 receipt records are unchanged.
- Closing authenticated `brev ls --json` reports `workspaces: null`; review
  created or mutated no Brev resource.

## Evidence And Authority Boundary

The accepted inventory is now 65 complete / 0 partial / 5 missing. The two
media files still lack production receipts, file-level media licenses, and
digest-bound depicted-asset attribution. The three original policies still
lack source checkpoints, training runs, exporter invocations, normalizer
provenance, and file-level policy licenses. These are terminal missing results,
not inferred successes. M6 remains open, M5 remains externally blocked, no
candidate or physical authority exists, and `<stop-orchestrator/>` remains in
`GOAL.md`.
