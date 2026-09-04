# Executor log 051 - M6 local provenance distribution gate

**Date:** 2026-09-04

**Brief:** `docs/briefs/051-m6-local-distribution-gate.md`

## Result

Added an exact distribution allowlist derived from accepted inventory revision
`c9a610b8005287dc83130660719af94f80274f67`. It admits 65 complete records and
quarantines the two legacy media plus three legacy ONNX files. Quarantine means
retained in the repository and excluded from this bundle, not deleted.

The deterministic archive contains the canonical allowlist, accepted inventory,
`LICENSE`, `microduck/assets/LICENSE-ASSETS.md`, and the 65 allowlisted files.
It contains no `demo/` or `policies/` payload. Its exact properties are:

- path: `receipts/m6/distribution/20260904-local-complete-assets-v1/microduck-complete-assets-v1.tar.gz`
- SHA-256: `f732dcbda8a77dbe11adbfcb5b85ab4bbd11699dae885649a2357166fb73093c`
- size: 9,272,643 bytes
- receipt `SHA256SUMS` SHA-256:
  `7c09028cf77754f7b7ea7d8793daa640c872e5ea892e8ca03eaaddc4bcf821c2`

## Fail-Closed Coverage

The validator requires exact allowlist equality to the accepted inventory and
checks the inventory blob at exact source revision `c9a610b...`. It rejects a
missing file added to distribution, quarantine/role coverage removal, file
digest drift, license/source revision drift, lifecycle or authority promotion,
rehashed receipt-result promotion, archive corruption, unsafe archive members,
and payload/order/metadata drift.

Official and community policy-manifest requirements remain visibly open across
all ten roles. This local bundle is not an official/community policy artifact.

## Validation

- Focused receipt/allowlist/archive validation: pass.
- Two independent deterministic generations: byte-identical to retained bundle.
- Adversarial allowlist, rehashed receipt, and corrupted-archive probes: pass.
- Python compilation, receipt checksums, and diff check: pass.
- Full authority-enabled `tests/run_all.py` suite: pass, ending
  `tous les tests passent`.
- Branch hygiene from accepted base `c9a610b...`: pass with 16 manifests and
  71 immutable logs. Workflow audit and staged/unstaged diff checks: clean.
- Closing `brev ls --json`: `workspaces: null`.
- Isolated exact-Executor-commit clone/staging proof is required after commit
  and is recorded by independent review.

## Evidence Boundary

Byte-only local packaging and staging only. No policy was imported, parsed,
loaded, executed, evaluated, approved, activated, or published. No credential,
hardware, remote publication, or compute action occurred. M6 remains open and
M5 remains externally blocked.
