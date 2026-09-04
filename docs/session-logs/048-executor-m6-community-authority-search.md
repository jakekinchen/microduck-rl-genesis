# Executor log 048 - M6 community authority search

**Date:** 2026-09-04

**Role:** Executor

**Brief:** `docs/briefs/048-m6-community-authority-search.md`

## Exact Search

- Hugging Face revision
  `fa7b27eeb5610d3b351362f4bd71691ee8be3d7d` has five commits and a complete
  six-entry tree: `.gitattributes`, README, manifest, preview media, and policy.
  LFS binds the policy SHA-256
  `5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040`
  and preview SHA-256
  `dd079687dba782bdf3c0cd63f010b0cfd6d1084024018f6810cb3468d1d1f82a`.
- Training commit `6cd45fc7a865299f118f7671142465d377853928`
  resolves to complete 251-entry tree
  `8e6b4f2a9ee405e7091c7b93c25b6b1585d88e22`. It has no checkpoint, ONNX,
  named normalizer, evaluator/evidence, or results files. It has one exporter.
- The accessible 1,000-commit ancestor window was searched without claiming
  history beyond the API pagination boundary. It contains no exact occurrence
  of `yr25mna4`, the named run, or `model_9999.pt` in commit messages.
- Exact source binds W&B project `pollen-robotics/mjlab_microduck`; task
  registration and the model card name run `yr25mna4`, `model_9999.pt`.
  Anonymous GraphQL returns `project: null`; direct public metadata, summary,
  config, and checkpoint file endpoints return 404. The generic run-page shell
  is mutable and exposes no file authority. No credentials were used.

## Terminal Policy-Role Result

No additional role resolves. Community remains 6/10 and
`rejected_incomplete`:

- source checkpoint: no public immutable bytes or digest;
- normalizer: baked-only claim, with no separate file or checkpoint-statistics
  authority;
- evaluator: absent from both exact trees;
- evidence: preview media and aggregate model-card claims are not digest-bound
  raw evaluation evidence;
- exporter provenance: exact source and generic HF auto-export template are
  retained, but no artifact-specific invocation or checkpoint-to-ONNX receipt
  exists.

Three additional exact source files are retained as inert `.source` evidence:
task registration, HF job/export template, and W&B project resolver. The fresh
immutable-download verifier now checks 16 files. These improve the search
record but grant no policy role or authority.

## File-Level Provenance Closure

The local `microduck/assets/xl330_m6.json` is byte-identical to exact BAM blob
`bam/params/xl330/m6.json` at
`62bd8ce12154340be97e06f7f41a0ca8f116d967`, SHA-256
`61c699362fb3fabdde93eeba5e1ad3bf4ef9ca2f71d03e316b1924ff005b20d3`.
The existing asset license note and exact Apache-2.0 upstream source now close
that entry from `partial` to `complete`. Inventory becomes 64 complete, one
partial, and five missing; M6 remains open.

## Receipt

- `receipts/m6/provenance/20260904-community-rough-walk-e/`
- Ten payload files verify against `SHA256SUMS`.
- Manifest SHA-256:
  `07f508813e84beda655c02600eccd9ac6b82da9bcfd2818e9a1a963100bd5887`.

## Verification

- Resolution and immutable re-fetch pass for all 16 pinned remote files.
- Provenance generation/check reproduces 64 complete / 1 partial / 5 missing;
  focused mutation, JSON, compilation, branch, workflow, and diff gates pass.
- All 10 receipt payloads verify.
- Full authority-enabled local suite: `tous les tests passent`, including both
  environment smokes.
- Final authenticated Brev inventory is empty.

## Evidence Boundary And Stop

Public authority search and one BAM parameter provenance closure only. The
community policy is not imported, evaluated, published, approved, activated,
or hardware-authorized. No downloaded code or model was executed. No paid
compute authority exists.
