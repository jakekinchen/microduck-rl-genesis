# Reviewer Message 049 - M6 local provenance archaeology

**Date:** 2026-09-04

## Decision

**NUDGE** - do not accept exact Executor handoff
`69c89263ee77655eebe17d0292d8c6eec4baa4f2` from accepted base
`321f0a9396b7596e62a0834d79c167a9fe8ce32a` yet.

Evidence anchor: **75**. The underlying public Git/object evidence supports the
ball source/license chain and the five terminal negatives, but the new
deterministic receipt validator permits material license, remote-coverage, and
media-evidence drift after the manifest is recomputed. The retained history
scope also counts transient `refs/codex/*` while describing only local heads,
remotes, and tags.

This NUDGE grants no policy, artifact, publication, activation, physical,
paid-compute, retry, replacement, or eighth-pilot authority.

## Independently Verified Evidence

- Public Genesis root commit
  `8659972a88cb6d6eab89ace269ef585bb172a581` is parentless with tree
  `313ea430f69061d643820288d1be988d5c5e729e`. It introduced local
  `ball.xml` as Git blob `42c3278eb5f5498e8204bc9696bf223c810e7d2e`,
  SHA-256
  `54a455bf454a9b6167655381df91593bbca86695d8d71e29fb6af69454c7c865`.
- Public official commit `84790795a6647f7dbd2353f53f7263229d7b7051`,
  tree `0b5d3766442f3c2bb1405c2a61dff75c6891eb40`, exposes the same
  path bytes, blob, size, and SHA-256 and is an ancestor of `109e06d...`.
- The only ball-path change between those official revisions is
  `7831c5142f93cc863327ae607bf0d262d127c767`. Its diff adds
  `priority="1"`, a comment, and line wrapping; mass, inertia, sphere size,
  color, and friction values are unchanged.
- Upstream commit `fc1697699c478ed4f67373808a23caccc6bed785`
  introduced the explicit `3D model files` CC-BY-SA-NC wording while the exact
  source ball blob was still `42c3278...`. The local license note and later
  declared upstream README hashes also match the receipt. The proposed
  partial-to-complete ball classification is therefore substantively valid.
- Across current reachable local refs and every live anonymous public branch,
  each demo file and original `backlash`, `rough`, and `velocity` policy path
  has exactly one path-history commit: the parentless Genesis root. No source
  checkpoint, run receipt, artifact-specific exporter invocation, separately
  attributable normalizer, evaluator, raw evidence, or file-level
  policy/media license resolves for those five files.
- Live anonymous GitHub API queries reproduced all branches and exact heads for
  `Macmachi`, `jakekinchen`, and `meniuniu`; all three repositories expose zero
  tags, releases, and retained Actions artifacts. Every target-path query on
  every branch returns only the root commit.
- The meniuniu `codex/macos-metal` branch's separate policy manifest declares
  output SHA-256 `ece00bc0169e7daafe7d2071f1f42eb461c6a31e5614a798ae1a824d3a3a5388`,
  distinct from the three original policies. Its README explicitly calls the
  originals inference-only positive controls and not outputs or evidence from
  that Mac run.
- Independent `ffprobe` metadata inspection reproduces the GIF/MP4 container,
  codec, dimensions, durations, frame counts, and generic encoder tags. It
  exposes no author, copyright, or source-receipt metadata and supplies no
  provenance authority.
- All seven receipt payloads verify, with exact path coverage. `SHA256SUMS`
  hashes to
  `21a4521adb629f88a3e2a28875904c9dc749a7d3d13f79c1ad25e38decc4bf87`.
- The working inventory regenerates exactly as 65 complete / 0 partial / 5
  missing with `fully_resolved=false`. Until correction and re-review, the
  last accepted inventory remains Reviewer 048's 64 / 1 / 5 state.

## Required Correction - Fail-Closed Semantic Coverage

`validate_local_provenance_archaeology` accepts each of these independently
rehashed receipt mutations:

- replacement of the upstream license README digest;
- replacement of the declared license scope;
- removal of the meniuniu branch map;
- inversion of a repository's root-only target-history result;
- replacement of the meniuniu positive-control statement with a false claim;
- replacement of a media file digest.

Required correction:

- Bind the exact license evidence path/hash, upstream declaration
  revision/README hash, and license scope in the validator.
- Bind every exact public repository branch name/head, each root-only target
  history result, the separate-policy path and distinct digest, and the
  positive-control disposition used by the decision.
- Bind each media metadata record to its exact file digest and the retained
  non-authoritative metadata result.
- Require exact key coverage for evidence maps whose absence would weaken the
  terminal result.
- Add negative mutation probes for these fields, recompute the receipt
  manifest, and rerun focused and full validation.

## Required Correction - Stable History Scope

`genesis-target-history.json` records 153 reachable commits and labels the
scope as all local heads, remotes, and tags at accepted base `321f0a9`.
Independent reproduction finds 150 commits in accepted-base ancestry; the
additional three came from transient Codex-internal refs present during
collection. The five path-history results remain one root commit, but the
scope/count description is not stable or self-contained.

Define and retain the exact ref set used for the count, or replace it with a
stable accepted-base ancestry scope plus the separately enumerated public
branch queries. Update the validator and mutations to bind that declared
scope. Do not infer authority from transient local refs.

## Other Validation

- Focused source-chain validation, existing negative mutation probes,
  provenance generation/check, file-provenance tests, and Python compilation:
  pass.
- Exact authority-enabled full suite: pass with `tous les tests passent`,
  including both environment smokes. The suite executed only its existing
  fixture policy; none of the five target artifacts was downloaded, parsed,
  loaded, executed, or evaluated.
- Diff checks, branch hygiene from `321f0a9`, workflow audit, and stop sentinel:
  pass. Branch hygiene reports 14 manifests and 71 immutable logs.
- Previously accepted receipts and Reviewer/Manager records are unchanged.
- Closing authenticated `brev ls --json` reports `workspaces: null`; review
  created or mutated no Brev resource.

## Authority Boundary

M6 remains incomplete and M5 remains externally blocked. Preserve the five
missing files, `fully_resolved=false`, and `<stop-orchestrator/>`. Do not treat
the working 65/0/5 inventory as accepted until the two corrections above pass
independent re-review.
