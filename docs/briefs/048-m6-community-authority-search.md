# Slice Brief 048 - M6 community authority search

**Date:** 2026-09-04

## Objective

Search the exact immutable authorities named by the community rough-walk-e
candidate for its four missing policy-manifest-v2 roles and exporter
provenance. Preserve terminal negatives. If no role resolves, close one
independent file-level license/provenance gap using only attributable bytes.

## Acceptance Criteria

- Inspect Hugging Face revision
  `fa7b27eeb5610d3b351362f4bd71691ee8be3d7d`, including commit history,
  complete tree, and LFS object metadata.
- Inspect training commit
  `6cd45fc7a865299f118f7671142465d377853928`, its complete tree, relevant
  source files, and bounded accessible history without importing or executing
  repository code.
- Query only publicly addressable metadata for the retained W&B run. Do not use
  credentials, mutable aliases, inferred tensor values, or self-claims as
  authority.
- Bind a source checkpoint, separate normalizer, evaluator, raw evidence, or
  artifact-specific exporter invocation only if immutable public bytes and
  provenance exist. Otherwise retain exact non-empty blockers.
- If policy roles remain blocked, resolve the local `xl330_m6.json` provenance
  gap only if it is byte-identical to an exact licensed BAM source blob.
- Preserve primary API responses and a self-checking receipt. Run focused and
  full validation, make one Executor commit, and obtain independent review.

## Evidence Boundary

Public authority search and file-level provenance only. No downloaded code or
policy execution, model/checkpoint loading, import, evaluation, publication,
approval, activation, hardware use, paid compute, or task-success claim.
