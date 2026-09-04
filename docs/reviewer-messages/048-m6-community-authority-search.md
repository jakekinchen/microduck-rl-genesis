# Reviewer Message 048 - M6 community authority search

**Date:** 2026-09-04

## Decision

**CONTINUE** - accept exact Executor handoff
`6ebdec5fe4bdbec15dbc391a4f8c2cedf24ec5dd` from accepted base
`9c2a17543af44d6d31341e6b953dab3928c6c7a8` strictly as a terminal public
authority search and one file-level BAM provenance closure.

Required corrections: none.

This acceptance grants no policy-manifest completion, candidate admission,
artifact import, policy execution, evaluation, publication, approval,
activation, transfer, hardware, paid-compute, retry, replacement, or eighth
pilot authority.

## Exact Public Authority Search

- Live anonymous Hugging Face queries reproduced exact revision
  `fa7b27eeb5610d3b351362f4bd71691ee8be3d7d`, five commits, and the complete
  six-item tree: one directory plus `.gitattributes`, `README.md`,
  `manifest.json`, `media/preview.mp4`, and `policy.onnx`.
- LFS metadata binds `policy.onnx` to
  `5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040`
  at 793,772 bytes and preview media to
  `dd079687dba782bdf3c0cd63f010b0cfd6d1084024018f6810cb3468d1d1f82a`
  at 11,412,279 bytes. Neither object supplies checkpoint, normalizer,
  evaluator, or raw-evidence authority.
- Live anonymous GitHub queries reproduced training commit
  `6cd45fc7a865299f118f7671142465d377853928`, tree
  `8e6b4f2a9ee405e7091c7b93c25b6b1585d88e22`, all 251 recursive API items,
  and all ten retained 100-commit response hashes.
- A separate blob-filtered, no-checkout audit of the same bounded 1,000-commit
  path/message window found no named run ID, run name, `model_9999.pt`, model
  or checkpoint suffix, named normalizer, evaluator, evidence, or results
  path. This remains a bounded-history result, not a claim beyond that window.
- The exact source tree contains `scripts/export.py` and the generic HF
  auto-export template, but no immutable artifact-specific invocation or
  checkpoint-to-ONNX receipt.
- Exact source binds W&B project `pollen-robotics/mjlab_microduck`; task source
  and the model card name run `yr25mna4` and checkpoint `model_9999.pt`.
  With credential variables removed, live anonymous GraphQL returned
  `data.project: null`, the run URL returned only a generic noindex application
  shell, and metadata, summary, config, and checkpoint endpoints each returned
  404. No mutable dashboard alias or credential was used.

## Terminal Role Result

Community remains exactly 6/10 roles:

- bound: `bam`, `exporter`, `license`, `model`, `normalized_onnx`, `task`;
- missing: `evaluator`, `evidence`, `normalizer`, `source_checkpoint`.

Exporter source is bound, but artifact-specific invocation provenance remains
incomplete. The resolution remains `rejected_incomplete`, emits no formal
manifest, records `authority=none`, and keeps import, evaluation, approval, and
activation unperformed or unauthorized.

## Immutable Downloads And Receipt

- A fresh verifier matched all 16 pinned supporting files byte-for-byte. The
  retained `.source` files were inspected only as inert text; neither those
  downloads nor either candidate policy was imported, loaded, or executed.
- Receipt `receipts/m6/provenance/20260904-community-rough-walk-e/` contains
  exactly ten payload files, with exact manifest coverage and successful
  per-file SHA-256 checks.
- `SHA256SUMS` hashes to
  `07f508813e84beda655c02600eccd9ac6b82da9bcfd2818e9a1a963100bd5887`.

## BAM File-Level Closure

- Exact BAM commit `62bd8ce12154340be97e06f7f41a0ca8f116d967` carries Apache License 2.0
  at repository root.
- Its `bam/params/xl330/m6.json`, the retained source copy, and local
  `microduck/assets/xl330_m6.json` are byte-identical at SHA-256
  `61c699362fb3fabdde93eeba5e1ad3bf4ef9ca2f71d03e316b1924ff005b20d3`.
- Inventory generation and validation reproduce 70 files: 64 complete, one
  partial, and five missing. `fully_resolved=false`; this closes one file-level
  provenance gap and does not close M6 or grant policy authority.

## Independent Verification

- Focused community-search, real-resolution, provenance, and artifact-contract
  tests pass, including fail-closed mutation probes.
- The full BAM-authority local suite passed twice with `tous les tests passent`,
  including both environment smokes. The second run used the Executor's exact
  `BAM_REPO`, `OFFICIAL_MICRODUCK_REPO`, `OFFICIAL_MJLAB_PYTHON`, zero-copy,
  and `.venv-apple` bindings; no substantive divergence appeared.
- An initial broad invocation under unconfigured system Python failed only on
  absent `torch`, `numpy`, `mujoco`, and `onnx`. Re-running under the documented
  project runtime resolved every dependency and passed; this was a runner
  selection error, not a repository failure.
- Receipt validation, immutable download verification, provenance regeneration,
  Python compilation, diff checks, branch hygiene, workflow audit, and stop
  sentinel pass. Branch hygiene reports 13 manifests and 71 immutable logs.
- Previously accepted receipts and Reviewer/Manager records are unchanged.
  The slice diff is scoped, and the review began from and returns to a clean
  tracked worktree on `main`, which remains intentionally ahead of
  `origin/main`.
- Closing authenticated `brev ls --json` reports `workspaces: null`. Review
  created or mutated no Brev resource.

## Evidence And Authority Boundary

This is terminal negative public-attribution evidence plus one valid BAM
file-level provenance improvement. M6 remains open on the four missing
community roles and the other inventory gaps. M5 remains externally blocked;
no new compute authority exists. Retain `<stop-orchestrator/>` in `GOAL.md`.
