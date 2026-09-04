# Executor log 050 - M6 local provenance validator correction

**Date:** 2026-09-04

**Brief:** `docs/briefs/050-m6-local-provenance-validator-correction.md`

## Reviewer NUDGE Addressed

Reviewer 049 substantiated the archaeology but demonstrated that rehashed
mutations to central license, remote, and media claims passed the v1 validator.
It also found that the receipt's 153-commit count included unnamed transient
Codex refs. This correction preserves the rejected v1 receipt and adds
`20260904-local-provenance-archaeology-v2`.

## Stable History Scope

The v2 history scope is exact ancestry of accepted commit
`321f0a9396b7596e62a0834d79c167a9fe8ce32a`: 150 commits, also 150 along its
first-parent chain. Dynamic refs are explicitly excluded; live public branches
remain separately enumerated. Each of the five target paths still resolves to
only root commit `8659972...` in that fixed ancestry.

## Exact Semantic Bindings

- The ball license chain now binds upstream declaration commit
  `fc1697699c478ed4f67373808a23caccc6bed785`, tree `86e21fa...`, parent,
  README blob/digest, exact `3D model files` scope, and the contemporaneous
  unchanged `42c3278...` ball blob. Source -> license declaration -> later
  `priority="1"` change ancestry is checked from the official Git objects.
- Media evidence is an exact whole-record comparison, including both file
  digests and every inert metadata/non-authority field.
- Remote evidence is an exact whole-record comparison: all three repositories,
  every branch/head, empty tags/releases/artifacts, root-only path history,
  the separate meniuniu policy path and SHA `ece00bc...`, its distinct-lineage
  disposition, and the original-policy positive-control statement.
- Search outcomes, action boundaries, target blockers, source exclusions,
  checkpoint paths/dispositions, and evidence maps require exact coverage.

## Negative Tests

Mutation probes now reject every Reviewer 049 counterexample after updating the
mutated payload's manifest entry: license README digest, license scope, branch
map removal, root-only history inversion, positive-control claim replacement,
separate-policy SHA replacement, both media evidence classes, and transient
history scope/count promotion. Earlier result/action/source/history/remote
promotion probes remain.

## Receipt

- `receipts/m6/provenance/20260904-local-provenance-archaeology-v2/`
- Seven payloads, exact coverage, all payload hashes verified.
- `SHA256SUMS` SHA-256:
  `48a400724c942e723c2dbbe78a71480e9261cd764fc56207245a86df99854207`.

## Validation

- Focused v2 receipt validator with exact official checkout: pass.
- All strengthened negative mutation probes: pass.
- File-provenance validation: pass at working 65 complete / 0 partial / 5
  missing, `fully_resolved=false`.
- Full `tests/run_all.py` authority suite with the pinned BAM checkout, exact
  official MicroDuck checkout, official MJLab Python, and Apple zero-copy gate:
  pass, ending `tous les tests passent`.
- Receipt manifest: seven payloads pass; manifest SHA-256 is
  `48a400724c942e723c2dbbe78a71480e9261cd764fc56207245a86df99854207`.
- Branch hygiene from Reviewer base `18e79c6...`: pass with 15 manifests and
  71 immutable logs. Workflow audit and staged/unstaged diff checks: clean.
- `brev ls`: no instances in org `NCA-09be-32030`.

## Evidence Boundary

Deterministic receipt-gate correction only. The underlying working archaeology
result is unchanged and remains pending independent acceptance. No target
policy was downloaded, parsed, loaded, executed, evaluated, approved, or
activated; no training, publication, credential, hardware, or compute action
occurred. M6 remains open and M5 remains externally blocked.
