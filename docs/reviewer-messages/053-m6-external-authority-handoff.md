# Reviewer Message 053 - M6 external authority handoff

**Date:** 2026-09-04

## Decision

**ESCALATE** - accept exact Executor handoff
`e8ba06563019875df4766d29387bed6825d3b0e3` from accepted base
`f22c799a6fc81375588f899da15468087731219d`, then stop the local workflow at
the external-input, third-party-contact, and human-publication authority
boundary.

Evidence anchor: **100**. Every honest repo-local M6 gate is exhausted. The
remaining official/community roles require immutable publisher-owned inputs;
contact and publication require new explicit human authority. Do not invent or
delegate another local slice.

This decision grants no contact, message transmission, publication, push, tag,
release, upload, credential use, policy import/parse/load/execution/evaluation,
approval, activation, hardware, paid-compute, retry, replacement, or eighth-
pilot authority.

## Packet Integrity

- `receipts/m6/authority/20260904-external-handoff-v1/` contains exactly six
  manifest-covered payloads plus `SHA256SUMS`; all six payload hashes and exact
  path coverage verify.
- `AUTHORITY_PACKET.json` SHA-256 is exactly
  `897a80891f785d6a519ed3e8aee61ee9269d94d139fe84e3bc2544792afefcc8`.
- `SHA256SUMS` SHA-256 is exactly
  `6c88e445fe4d07af869fb01f3cba1b1af68f4fbfbe40b358a999d1e0ede1e981`.
- Rehashed mutations removing a role/evidence requirement, claiming contact or
  publication, executing the plan, inventing a repo-owned role closure,
  reducing the human-authority list, changing the terminal decision, or
  replacing a support file all reject.

## Exact Remaining Roles

The packet reproduces the accepted resolution bundles byte-for-byte by digest,
candidate identity, bound roles, missing roles, original blocker text,
`rejected_incomplete`, and `authority=none`.

- Official missing roles are exactly `bam`, `evaluator`, `evidence`,
  `exporter`, `model`, `normalizer`, `source_checkpoint`, and `task`.
- Community missing roles are exactly `evaluator`, `evidence`, `normalizer`,
  and `source_checkpoint`.
- Every role retains one concrete acceptable immutable-evidence class:
  publisher/upstream repository and immutable revision/path/digest bindings,
  artifact-specific exporter invocation where needed, standalone normalizer or
  checkpoint-statistics provenance, immutable checkpoint/run lineage, and raw
  digest-bound evaluation receipts as applicable.

No narrative, mutable alias, aggregate metric, screenshot, preview media, or
new repo-owned output is promoted into the missing publisher authority.

## Unsent Contact Drafts

- Both Pollen and RemiFabre/W&B documents are digest-bound in the packet and
  remain marked `UNSENT`, `draft only`, and `status=unsent`; packet action
  fields confirm no third party was contacted and no draft was transmitted.
- Both drafts cover source checkpoint bytes/run lineage, separately
  attributable normalizer data, exact exporter source and artifact-specific
  invocation, evaluator revision, digest-bound raw evidence, license coverage,
  immutable revisions, and file digests.
- The drafts explicitly reject mutable prose/media/aggregate claims as role
  closure and require owner authorization before transmission.

## Preregistered Publication Plan

The plan remains `preregistered_not_authorized_not_executed` and binds:

- accepted source `f22c799a6fc81375588f899da15468087731219d`;
- local `origin` URL and expected `origin/main`
  `3257775beeeb8b1df646dd295bf84e34967e42ec`, which is an ancestor of the
  accepted source;
- v2 archive SHA-256
  `0c92aa28888754d9b6c07a6d92f45f06fae8e7564ad76482ec1aa06a385300d9`
  and size 9,272,643;
- exact GitHub/Hugging Face tag or revision
  `m6-complete-assets-v2-0c92aa28`, currently absent locally;
- a human-supplied and confirmed Hugging Face repository plus explicit GitHub
  and Hugging Face write credentials;
- clean-source, pre-mutation drift checks, fresh Git re-fetch, immutable
  Hugging Face re-download, digest/manifest verification, and byte-only staging
  to `staged_not_imported` with no `demo/` or `policies/`;
- stop conditions for missing authority/credentials/destination, remote drift,
  digest mismatch, quarantine leakage, test failure, or lifecycle promotion,
  plus preserve-and-quarantine rollback rather than overwrite or deletion.

No plan step was executed and no public surface was mutated.

## No Honest Repo-Owned Closure

Independent inspection confirms zero role closures:

- Official/community contract fixtures explicitly identify themselves as
  synthetic validation-only data, including non-executable text placeholders.
- `evaluator/` is a repo-owned development evaluator introduced outside the
  publisher evidence chain; it was not used for either upstream candidate's
  reported claims.
- `export_onnx.py` is current repo tooling, not a retained artifact-specific
  invocation that produced either exact candidate digest.
- The four retained Apple baseline `.pt` files are local five-iteration smoke
  checkpoints with distinct digests and task/lineage scope; they are not either
  candidate's source checkpoint.
- The accepted distribution contains only attributable meshes, MJCF, one asset
  transform, and one BAM parameter. It contains no evaluator, exporter,
  checkpoint, policy, or media payload and cannot prove official candidate use.
- Parsing baked ONNX tensors would neither recover checkpoint-statistics
  provenance nor be authorized. A new local candidate run would create local
  evidence, not the missing publisher-owned raw evidence.

## Validation And Authority Boundary

- Focused packet validation, accepted resolution/distribution cross-checks,
  rehashed negative probes, and Python compilation pass.
- The full authority-enabled `tests/run_all.py` suite passes with the pinned
  BAM checkout, exact official MicroDuck checkout, official MJLab Python,
  Apple zero-copy gate, both environment smokes, and final
  `tous les tests passent`.
- Diff checks, branch hygiene from `f22c799...`, workflow audit, and stop
  sentinel pass. Branch hygiene reports 18 manifests and 71 immutable logs.
- Existing authority is exactly local read/audit, scoped edit/commit,
  deterministic validation, byte-only staging, and unsent drafting. New human
  authority is required for contact, GitHub mutation, Hugging Face destination
  selection/upload, public-mutation credentials, and every policy action.
- Every action field remains false. Closing authenticated `brev ls --json`
  reports `workspaces: null`; review created or mutated no Brev resource.

M6 remains open at this external boundary with the five source-tree files still
quarantined. M5 remains externally blocked. Preserve `<stop-orchestrator/>` and
resume only after the user supplies the required upstream material or grants a
specific contact/publication action with exact destinations.
