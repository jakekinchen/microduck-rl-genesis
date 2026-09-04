# Reviewer Message 051 - M6 local distribution gate

**Date:** 2026-09-04

## Decision

**NUDGE** - do not accept exact Executor handoff
`c3c909c78bf541a1c1d8b8a6a7338ac18ed4aa0e` from accepted base
`c9a610b8005287dc83130660719af94f80274f67` yet.

Evidence anchor: **100**. The allowlist, quarantine, receipt validation,
isolated staging, authority boundaries, and retained archive contents are
substantively correct, but the archive builder does not reproduce the retained
SHA-256 across the standard-library Python interpreters available on this
host. The difference is one interpreter-dependent gzip OS-header byte.

This NUDGE grants no publication, push, policy import/parse/load/execution,
evaluation, approval, activation, hardware, paid-compute, retry, replacement,
or eighth-pilot authority.

## Independently Verified Evidence

- Exact Executor/base ancestry and clean handoff reproduce. The slice diff is
  scoped to the local distribution gate and its durable evidence.
- `distribution-allowlist-v1.json` is exact canonical output derived from the
  accepted inventory at `c9a610b...`: 65 complete / 0 partial / 5 missing,
  `fully_resolved=false`.
- All 65 included records are present and locally digest/size-bound. Each has a
  resolved Apache-2.0 or CC-BY-SA-NC license, exact license-evidence digest,
  byte-identical source, source path/revision, and matching source/file digest.
  Fresh Git-object reads reproduce 64 official MicroDuck records and the BAM
  parameter record. Included classes remain 47 mesh, 16 MJCF, one asset
  transform, and one actuator parameter; no policy, media, repo-owned campaign,
  or smoke artifact is relabeled.
- The two media files and three legacy ONNX files remain present in the source
  tree with their exact missing blockers. They are the complete five-record
  quarantine set and are absent from the retained archive.
- The archive contains exactly 69 unique regular payloads: two metadata files,
  two license/support files, and the 65 allowlisted records. It contains no
  `demo/`, `policies/`, receipts, or logs payload.
- Both official and community requirements retain all ten exact roles with
  `open_no_complete_policy_manifest` and `artifact_acceptance=none`.
  Lifecycle remains byte-only through `staged_not_imported`; publication and
  every policy authority remain absent.
- The retained bundle itself validates at SHA-256
  `f732dcbda8a77dbe11adbfcb5b85ab4bbd11699dae885649a2357166fb73093c`
  and 9,272,643 bytes. Receipt payload hashes and exact coverage verify;
  `SHA256SUMS` hashes to
  `7c09028cf77754f7b7ea7d8793daa640c872e5ea892e8ca03eaaddc4bcf821c2`.

## Isolated Exact-Commit Proof

A fresh `--no-local --no-hardlinks` clone at
`/private/tmp/microduck-review-051.rllvU0/clone` was detached at exact Executor
commit `c3c909c78bf541a1c1d8b8a6a7338ac18ed4aa0e`.

- `/usr/bin/python3` 3.9.6 ran
  `scripts/validate_m6_distribution_bundle.py` with a fresh stage directory.
  It returned exact retained bundle SHA-256 `f732dcb...`, size 9,272,643,
  `byte_only_complete`, and `staged_not_imported`.
- The stage contains 70 files including its marker and has no `demo/` or
  `policies/` directory. No policy bytes were imported, parsed, loaded,
  executed, or evaluated.
- Two independent fresh allowlist generations in that clone are byte-identical
  to each other and to the retained allowlist. Their uncompressed tar streams
  are byte-identical to the retained tar stream at SHA-256 `73a6e13f...`.

## Blocking Determinism Counterexample

Two independent `/usr/bin/python3` 3.9.6 builds are byte-identical to each
other, have the expected 9,272,643-byte size, but hash to
`0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9`
instead of the retained `f732dcb...`.

The generated and retained archives differ at exactly one byte: one-based byte
10, the gzip OS header. Python 3.9.6 and 3.13.11 emit header
`1f8b08000000000002ff`; the retained Python 3.12.12 build emits
`1f8b0800000000000213`. Running the focused test under Python 3.13.11 fails its
retained-byte identity assertion at line 90, while the same test under the
project's Python 3.12.12 passes. Decompression yields identical tar bytes, but
that does not satisfy the exact archive digest acceptance gate.

## Fail-Closed And Full Validation

- Independent mutations reject missing-file inclusion, allowlisted/quarantine
  coverage removal, file digest drift, declared-license and license-evidence
  drift, source revision drift, lifecycle and authority promotion, required
  role removal/status promotion, a rehashed receipt authority promotion, and
  archive ordering, unsafe-path, metadata, and payload drift.
- The exact authority-enabled `tests/run_all.py` suite passes under the project
  Python 3.12.12 runtime with final `tous les tests passent`, including both
  environment smokes. This does not erase the independent exact-rebuild
  failure under the other supported local standard-library interpreters.
- Diff checks, branch hygiene from `c9a610b...`, workflow audit, and stop
  sentinel pass. Branch hygiene reports 16 manifests and 71 immutable logs.
- Closing authenticated `brev ls --json` reports `workspaces: null`; review
  created or mutated no Brev resource.

## Required Correction

- Preserve the rejected slice-051 receipt and retained archive unchanged.
- Create a versioned corrective slice/receipt whose gzip writer fixes every
  header field explicitly and reproducibly across supported interpreters.
  `gzip.GzipFile(filename="", mtime=0, ...)` emits OS byte `0xff` on all three
  tested interpreters and is one viable standard-library route, but the new
  digest must be established by the corrective receipt rather than rewriting
  slice 051.
- Add a subprocess regression that builds with at least the available system
  Python and project Python, then requires exact allowlist, archive bytes,
  bundle SHA-256, size, and isolated-stage result equality.
- Re-run the isolated detached-clone proof and independent review before
  accepting the local distribution unit.

## Evidence And Authority Boundary

The accepted inventory remains 65 complete / 0 partial / 5 missing, but the
slice-051 distribution bundle is not accepted. M6 remains open, the five
terminal negatives remain quarantined, publication remains human-owned, M5
remains externally blocked, and no policy, compute, activation, or physical
authority exists. Retain `<stop-orchestrator/>`.
