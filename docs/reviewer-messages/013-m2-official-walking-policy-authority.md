# Reviewer Message 013 - M2 official walking policy authority

**Date:** 2026-09-02

## Decision

`STOP`

## Evidence Anchor

Confidence `100` - directly confirmed upstream-authority blocker.

- Commit `4ee05e5` records the bounded search and a locked
  `official_policy_authority_missing` result.
- The pinned official training commit's object tree contains no ONNX,
  checkpoint, or checkpoint archive.
- The project-owned Hugging Face revision
  `088524a64e2557dc453256b6071dbb9d23888802` carries the same walking artifact
  digest as the official runtime. Its manifest binds 61 observations, 14
  actions, 50 Hz, and a perpetual role, but omits the training and export chain.
- Protobuf-only inspection passed ONNX validation and found the baked Sub/Div
  normalizer. The artifact metadata says `run_path=None`.
- The runtime commit `39544966ab901a5434a8ad87338d5d11abae1397`
  replaces the policy without updating the older prototype-source provenance
  table or binding an exact checkpoint/export record.

## Review Validation

- A detached clean worktree passed contract freeze, the focused authority test,
  branch hygiene, and `git diff --check`.
- Negative probes rejected inspector use without `--no-execute` and rejected a
  mismatched artifact digest.
- The BAM-enabled broad test runner completed with `tous les tests passent`.

## Findings

The official artifact is available, immutable, normalized, and deployment-shape
compatible. Those facts do not identify which checkpoint and exact official
task produced it, which exporter invocation created it, or where its normalizer
statistics came from. Running it would therefore skip the brief's provenance
gate rather than close it.

Genesis repository and M0 smoke policies were rejected as non-official
substitutes. No official rollout, final Genesis candidate inspection, held-out
case, training, credential use, publication, paid compute, or hardware action
occurred.

## Milestone State

M2 remains open. The durable result is
`official_policy_authority_missing`; official-policy repeatability is not
checked.

## Resolution Required

Resume only when upstream provides one of the resolution paths in the locked
authority result: a complete immutable manifest for this digest, a reproducible
project-owned checkpoint/export chain, or another designated normalized
artifact with complete provenance.
