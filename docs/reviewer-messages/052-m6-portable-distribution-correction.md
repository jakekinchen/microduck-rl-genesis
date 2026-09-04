# Reviewer Message 052 - M6 portable distribution correction

**Date:** 2026-09-04

## Decision

**CONTINUE** - accept exact Executor handoff
`93f7362a4ee460e16988e85e2e061b16f861681c` from Reviewer base
`68b0094f70a57fa0c79a71319d1ebe6ad42fff5e` strictly as the corrected,
portable local distribution bundle and byte-only staging gate.

Required corrections: none.

This acceptance grants no publication, push, policy import/parse/load/execution,
evaluation, approval, activation, hardware, paid-compute, retry, replacement,
or eighth-pilot authority.

## Versioned Receipt And Writer

- The rejected v1 receipt is unchanged from Reviewer base at Git tree
  `e415133271872c0e3376afa40273041378e90663`. Its payloads still verify and
  its `SHA256SUMS` SHA-256 remains exactly
  `7c09028cf77754f7b7ea7d8793daa640c872e5ea892e8ca03eaaddc4bcf821c2`.
- The v2 writer uses
  `gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=...,
  mtime=0)` and refuses output unless its first ten bytes are exactly
  `1f8b08000000000002ff`.
- The retained v2 archive has that exact header, SHA-256
  `0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9`,
  and size 9,272,643 bytes. Its three receipt payload hashes and exact file
  coverage verify; v2 `SHA256SUMS` hashes to
  `9c2a1370e7aba9ad6e46899fdc2ed6cb6935be4bb5af93e86a33ccee71a42790`.
- A fully rehashed v2 receipt whose archive OS byte was changed back to
  `0x13`, with its bundle and receipt digests updated consistently, is rejected.
  Rehashed lifecycle/authority promotion and archive corruption also reject.

## Multi-Interpreter And Isolated Proof

A fresh `--no-local --no-hardlinks` clone at
`/private/tmp/microduck-review-052.1vKU9N/clone` was detached at exact Executor
commit `93f7362a4ee460e16988e85e2e061b16f861681c`.

- `/usr/bin/python3` 3.9.6, project Python 3.12.12, and available Python
  3.13.11 each ran the build script in a separate subprocess against that
  clone. Every generated allowlist is byte-identical to the retained allowlist;
  every archive is byte-identical to the retained v2 archive.
- All three builds independently reproduce header
  `1f8b08000000000002ff`, SHA-256 `0c92aa2...`, and size 9,272,643. The focused
  distribution suite also passes when invoked separately under each of those
  three interpreters.
- `/usr/bin/python3` validated the v2 receipt from the detached clone into a
  fresh stage. It returned exact bundle SHA/size, `byte_only_complete`, and
  `staged_not_imported`. The stage contains 70 files including its marker and
  contains no `demo/` or `policies/` directory.

## Scope And Authority

- The canonical allowlist is unchanged from Reviewer base at SHA-256
  `8b473f6e4f00a1a1644edbf126647d92add6082fe6cecb2d5cdd2386d67857e7`.
  It remains exact output from the accepted 65 complete / 0 partial / 5
  missing inventory with `fully_resolved=false`.
- All 65 included files retain resolved license evidence and exact
  source/path/revision/digest bindings. The two legacy media and three legacy
  ONNX files remain present in the source tree, retain their missing blockers,
  and are the exact five-record quarantine set absent from the archive.
- The archive contains the two metadata records, two license/support files,
  and 65 allowlisted files only. It contains no demo, policy, receipt, log,
  repo-owned campaign, or smoke payload.
- Official and community policy-manifest requirements each remain open with
  all ten required roles and `artifact_acceptance=none`. Lifecycle stops at
  `staged_not_imported`; publication and every policy authority remain absent.

## Independent Validation

- Independent mutations reject missing-file inclusion, allowlist/quarantine
  coverage removal, file digest, license, and source drift, lifecycle and
  authority promotion, required-role removal, an actual rehashed gzip-header
  mutation, a rehashed receipt authority promotion, and archive corruption.
- The full authority-enabled `tests/run_all.py` suite passes with the pinned
  BAM checkout, exact official MicroDuck checkout, official MJLab Python,
  Apple zero-copy gate, both environment smokes, and final
  `tous les tests passent`.
- Diff checks, branch hygiene from `68b0094...`, workflow audit, and stop
  sentinel pass. Branch hygiene reports 17 manifests and 71 immutable logs.
- Closing authenticated `brev ls --json` reports `workspaces: null`; review
  created or mutated no Brev resource.

## Evidence And Authority Boundary

This accepts only deterministic local packaging and byte-only staging of the
65 already accepted complete provenance records. M6 remains open because the
official/community ten-role policy manifests still lack authoritative upstream
inputs and publication remains a human-owned action. The five terminal
negatives remain quarantined, M5 remains externally blocked, and no policy,
compute, activation, or physical authority exists. Retain
`<stop-orchestrator/>`.
