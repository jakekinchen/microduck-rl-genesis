# Immutable artifact contracts

This directory defines policy manifest v2 plus reference and hardware
attestations. The validator is intentionally non-executing: it parses JSON,
checks relative paths, sizes, SHA-256 digests, source classes, lifecycle state,
and authority boundaries. It does not import the bound exporter, load a Torch
checkpoint, initialize ONNX Runtime, run a policy, download files, publish,
approve, activate, or touch hardware.

The `official` and `community` bundles are synthetic fixtures. Their `.onnx`
and `.pt` files are plain marker bytes and are deliberately not executable.
Passing validation proves only that the packaging rules work; it does not
attribute or accept any real policy.

`real-candidates/` contains byte-for-byte downloads from immutable revisions.
Each `policy-manifest-v2-resolution.json` audits all ten required v2 roles but
is deliberately not a policy manifest: missing roles force
`rejected_incomplete`, `authority=none`, and no `policy-manifest-v2.json` is
emitted. Bound upstream Python is hashed as inert data and is never imported.

`distribution-allowlist-v1.json` is the local source/artifact distribution
gate. It includes only the 65 inventory records with complete, license-bound,
byte-identical source provenance and quarantines the five missing media/policy
records without deleting them. Its retained deterministic archive supports
byte-only validation and library staging; it grants no policy-manifest,
publication, import, evaluation, approval, or activation authority.
The rejected v1 archive is preserved as evidence of an interpreter-dependent
gzip OS-header byte. The current v2 receipt fixes the gzip filename, mtime, and
OS header explicitly and is regression-tested across system, project, and
available Python 3.13 interpreters.

Run:

```bash
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/official --source-class official
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/community --source-class community
.venv-apple/bin/python tests/test_m6_real_artifact_resolution.py
.venv-apple/bin/python scripts/verify_m6_real_candidate_downloads.py
.venv-apple/bin/python scripts/validate_m6_distribution_bundle.py
.venv-apple/bin/python scripts/validate_m6_authority_handoff.py
```
