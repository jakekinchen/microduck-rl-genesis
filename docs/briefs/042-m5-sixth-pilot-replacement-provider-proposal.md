# Slice Brief 042 - M5 sixth-pilot replacement-provider proposal

**Date:** 2026-09-04

## Objective

Prepare one local-only, fail-closed sixth-pilot proposal after Reviewer 041's
accepted terminal-negative fifth pilot. Select a genuinely different
single-A100 provider/type with stronger catalog-visible connectivity and
cost-recovery properties, without creating paid compute.

## Selection Boundary

- Exclude every previously failed exact type, including
  `hyperstack_A100_80G` and `massedcompute_A100_sxm4_80G_DGX`.
- Prefer a direct provider with catalog-visible flexible ports and stoppability
  because the fifth pilot failed before SSH. Treat these as better
  connectivity/recovery indicators, not proof that a future shell will work.
- Record advertised boot time and disk size honestly, including any regression
  or capacity risk.
- Require an exact container-mode immutable-digest dry run and empty
  authenticated inventory. Do not create a workspace.

## Required Proposal

- Bind one exact unique workspace, one GPU, one type, no fallback,
  substitution, retry, or second workspace.
- Bind exact accepted proposal/review/Manager/terminal chains, immutable image,
  sixth-specific harness, runtime lock, deterministic source bundles, and all
  hashes.
- Require a 4,800-second inner harness timeout and conservative two-hour cost
  ceiling at the exact live hourly rate, remaining inside the user's `$210`
  total envelope.
- Preserve suite-first execution. Only after it passes may the four frozen
  public-development 64-environment by five-iteration smokes run, followed by
  named normalized ONNX exports.
- Require complete terminal receipts, explicit no-shell handling, exact remote/
  local manifest equality when applicable, exact-ID teardown, and empty
  inventory.
- Keep `compute_authorized=false` and require a fresh separately committed
  Manager record after independent Reviewer acceptance.

## Acceptance Criteria

- Machine-readable schema, semantic validator, and mutation tests freeze every
  proposal field and reject explicit compute authority, old provider types,
  rate drift, and harness self-attestation drift.
- Deterministic source bundles reproduce twice at exact hashes.
- Focused validators, full authority-enabled local suite, static CUDA,
  artifact, Python/Bash/shellcheck, all manifests and immutable logs, branch
  hygiene, workflow audit, and final empty Brev inventory pass.
- Executor commits the proposal and an independent Reviewer records a decision.
- Restore `<stop-orchestrator/>` at the Manager boundary.

## Evidence Boundary

This slice can establish only a locally reproducible non-authorizing proposal.
Catalog properties and a dry run do not prove shell readiness, CUDA
compatibility, task success, or physical authority.
