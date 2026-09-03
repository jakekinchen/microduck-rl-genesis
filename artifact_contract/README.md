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

Run:

```bash
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/official --source-class official
.venv-apple/bin/python scripts/validate_artifact_bundle.py \
  artifact_contract/fixtures/community --source-class community
```
