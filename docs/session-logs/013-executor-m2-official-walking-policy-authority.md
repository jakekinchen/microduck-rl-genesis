# Executor log 013 - M2 official walking policy authority

**Date:** 2026-09-02

**Role:** Executor

**Brief:** `docs/briefs/013-m2-official-walking-policy-authority.md`

## Result

`official_policy_authority_missing`

The official runtime's designated `policies/alpha_walking.onnx` is an immutable,
project-owned candidate with SHA-256
`e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
Safe protobuf-only inspection established a float32 61D-to-14D graph and a
leading Sub/Div normalizer. It was not executed.

The project-owned Hugging Face repository at immutable revision
`088524a64e2557dc453256b6071dbb9d23888802` distributes the same digest. Its
schema-v2 manifest binds the 61D/14D/50 Hz deployment contract and perpetual
role, but no checkpoint, training run, task-source commit, exporter
commit/invocation, or normalizer source.

That is not sufficient provenance. The artifact's metadata records
`run_path=None`; the commit that replaces the walking binary also omits those
bindings. The runtime policy README's prototype-source table predates that
replacement, and the pinned official training tree contains no ONNX or
checkpoint artifact.

The repository's Genesis policy and the retained M0 Apple-smoke policy were
recorded and rejected as non-official substitutes. No final Genesis candidate
was inspected.

## Durable evidence

- `microduck_contract/policies/official-walking-authority-v1.json`
- `microduck_contract/policies/official-walking-authority-v1.lock.json`
- `scripts/inspect_onnx_authority.py`
- `tests/test_official_walking_policy_authority.py`

## Stop condition

M2 repeatability cannot honestly proceed until an upstream immutable manifest
binds the current ONNX, or another designated normalized artifact, to its exact
checkpoint, run, task/source commit, exporter invocation, and normalizer
provenance. Credentials, private W&B/Hugging Face state, retraining, and policy
substitution are outside this slice.

## Evidence boundary

No official-policy rollout, visible or held-out evaluation, task success,
backend comparison, transfer, publication, hardware activation, or physical
authority occurred.
