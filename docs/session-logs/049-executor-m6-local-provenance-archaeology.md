# Executor log 049 - M6 local provenance archaeology

**Date:** 2026-09-04

**Brief:** `docs/briefs/049-m6-local-provenance-archaeology.md`

## Exact Ball Resolution

Genesis root commit `8659972a88cb6d6eab89ace269ef585bb172a581`
introduced local `ball.xml` as Git blob `42c3278...`. The same blob is publicly
addressable at official source commit
`84790795a6647f7dbd2353f53f7263229d7b7051`, with matching SHA-256
`54a455bf...c865`. The source commit is an ancestor of the later declared
official revision `109e06d...`.

The sole ball-path change between those revisions is commit `7831c514...`,
which later added `priority="1"` plus an explanatory comment/line wrapping;
mass, inertia, size, color, and friction stayed unchanged. The Genesis file
therefore matches an earlier exact official source rather than representing an
unexplained local transform. Existing CC-BY-SA-NC asset license evidence remains
applicable. The inventory upgrades this entry from partial to complete.

## Five Terminal Negatives

The GIF, MP4, and three original ONNX files were each introduced exactly once
in the parentless Genesis root commit and never changed in reachable local or
public-fork history. The root tree contains no source checkpoint, campaign
receipt, artifact-specific export receipt, normalizer source, raw policy
evidence, media production chain, or file-level policy/media license.

The root `.gitignore` explicitly excludes training runs/checkpoints and the
video-production toolchain. Live anonymous public-repository checks found no
tags, releases, or action artifacts. The only second-fork branch with a
manifested policy publishes a different policy/digest and explicitly labels
the original three ONNX files inference-only positive controls, not products or
evidence of that run. Generic media encoder tags bind no author, license, or
production source. Exact digest/filename web searches found no other authority.

The two media and three policy records remain `missing` with their existing
blockers. Inventory becomes 65 complete / 0 partial / 5 missing and remains
`fully_resolved=false`.

## Retained Evidence

- `receipts/m6/provenance/20260904-local-provenance-archaeology/`
- Seven payload files plus exact `SHA256SUMS` coverage.
- Receipt-manifest SHA-256:
  `21a4521adb629f88a3e2a28875904c9dc749a7d3d13f79c1ad25e38decc4bf87`.
- `artifact_contract/local_provenance_archaeology.py`
- `scripts/validate_m6_local_provenance_archaeology.py`
- `tests/test_m6_local_provenance_archaeology.py`

## Validation

- Focused receipt/source-chain validator: pass with the exact official checkout.
- Negative mutation probes: pass.
- Provenance generation/check: 65 complete / 0 partial / 5 missing.
- File-provenance tests: pass.
- Fresh public raw source download hashes exactly to `54a455bf...c865`; the
  public commit API reproduces commit, tree, and parent identities.
- Full authority-enabled suite: `tous les tests passent`, including both
  environment smokes. The ONNX deployment check remained honestly not
  applicable because no matching local training checkpoint exists.
- Python compilation, JSON parsing, and all seven receipt payload hashes: pass.
- Branch hygiene: pass from reviewed base `321f0a9` with 14 manifests and 71
  immutable logs. Workflow audit and staged/unstaged diff checks: clean.
- Closing authenticated `brev ls`: no instances in organization
  `NCA-09be-32030`.

## Evidence Boundary

File-level provenance resolution and terminal negative archaeology only. No
policy was downloaded, imported, parsed, loaded, executed, or evaluated; no
training, publication, activation, credential use, hardware action, or compute
provisioning occurred. M6 remains open and no policy or physical authority
exists.

## Reviewer Outcome

The independent Reviewer returned NUDGE on exact Executor handoff
`69c89263ee77655eebe17d0292d8c6eec4baa4f2` from accepted base
`321f0a9396b7596e62a0834d79c167a9fe8ce32a`. The factual ball chain, public
remote searches, five terminal negatives, 65 / 0 / 5 working inventory, tests,
and empty Brev state were independently reproduced. Acceptance is withheld
because independently rehashed mutations to critical license, remote branch/
history, meniuniu disposition, and media-digest fields pass the validator, and
the receipt's 153-commit description omits its dependence on transient
`refs/codex/*`. Reviewer Message 049 requires exact semantic bindings, stable
history scope, new negative probes, a recomputed receipt, and re-review. The
last accepted inventory remains 64 / 1 / 5; no policy, compute, activation, or
physical authority exists.
