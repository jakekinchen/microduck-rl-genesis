# Reviewer Message 047 - M6 real artifact resolution

**Date:** 2026-09-04

## Decision

**CONTINUE** - accept exact Executor handoff
`0785e8fdf8cd32d73e475da943cced5014fdfac0` from accepted base
`6571111c33f53936e107055ae77e333de2367484` strictly as a fail-closed
immutable attribution audit and durable external M5 blocker.

Required corrections: none.

This acceptance grants no paid compute, eighth pilot, retry, replacement,
artifact import, policy execution, evaluation, publication, approval,
activation, transfer, or hardware authority.

## Durable M5 External Blocker

Reviewer messages 037, 041, 043, and 046 establish four consecutive distinct
provider/type attempts that failed before usable remote execution:

- `hyperstack_A100_80G` / `tpo91g7kj`: provisioning health;
- `massedcompute_A100_sxm4_80G_DGX` / `i1bsb56r7`: provisioning connectivity;
- `a2-highgpu-1g:nvidia-tesla-a100:1` / `urmhasks7`: provisioning
  connectivity, with READY only after terminal declaration;
- `gpu_1x_a100_sxm4` / `qcolxobcf`: provisioning/readiness-window expiry.

Each exact workspace was deleted and independently accepted as terminal
negative. Manager authorities 010 through 013 are consumed. No current compute
authority exists, no eighth pilot was proposed or created, and fresh
authenticated Brev inventory is empty. The durable no-eighth-pilot boundary is
therefore accurate and requires new user direction, a newly reviewed proposal,
and fresh exact Manager authority before any later paid attempt.

## Immutable Candidate Retrieval

- Official Pollen Robotics `alpha_walking.onnx` was retrieved only from full
  Hugging Face revision `088524a64e2557dc453256b6071dbb9d23888802`.
  Its committed 793,705 bytes hash to
  `e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
- Community `RemiFabre/microduck-rough-walk-e` was retrieved only from full
  revision `fa7b27eeb5610d3b351362f4bd71691ee8be3d7d`. Its 793,772-byte
  policy hashes to
  `5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040`.
  The retained sources bind training commit
  `6cd45fc7a865299f118f7671142465d377853928` and BAM commit
  `62bd8ce12154340be97e06f7f41a0ca8f116d967`.
- All 13 source records carry full 40-hex immutable revisions embedded in
  their URLs. A fresh network re-fetch matched every committed size, SHA-256,
  and byte sequence.
- New runtime code only hashes and compares downloaded bytes. Downloaded
  Python is stored under `.source`; neither ONNX candidate was loaded, imported,
  initialized, or executed.

## Manifest-v2 Resolution

- Official binds exactly 2/10 roles: `license` and `normalized_onnx`. It is
  missing `bam`, `evaluator`, `evidence`, `exporter`, `model`, `normalizer`,
  `source_checkpoint`, and `task`.
- Community binds exactly 6/10 roles: `bam`, `exporter`, `license`, `model`,
  `normalized_onnx`, and `task`. It is missing `evaluator`, `evidence`,
  `normalizer`, and `source_checkpoint`; source provenance also remains blocked
  on the exact exporter invocation and the corresponding checkpoint,
  normalizer, evaluator, and raw-evidence bindings.
- Every missing role has a non-empty blocker. Both reports are
  `rejected_incomplete`, `authority=none`, lifecycle-inert, and emit no
  `policy-manifest-v2.json`.
- The existing policy-manifest-v2 schema and synthetic fixtures are unchanged
  byte-for-byte from the accepted base. A resolution report is independently
  rejected when passed to the formal-manifest validator.

## Independent Validation

- Both non-executing real-candidate validators and offline mutation probes:
  pass, including digest drift, fabricated binding, unpinned URL, unbound file,
  lifecycle promotion, authority promotion, and formal-manifest confusion.
- Synthetic artifact-contract fixtures and file-provenance inventory: pass.
- Full authority-enabled local suite, including both environment smokes: pass.
- Python compilation, relevant JSON parsing, diff checks, branch hygiene,
  workflow audit, and stop sentinel: pass. Branch hygiene reports 12 manifests
  and 71 immutable logs.
- Previously accepted receipts, Reviewer messages, Manager records, formal
  manifest schema, and synthetic fixtures are unchanged.
- Closing authenticated Brev inventory is empty. Review created or mutated no
  Brev resource.

## Evidence And Authority Boundary

This acceptance establishes immutable retrieval and attribution gaps only.
Neither candidate is a valid policy manifest or an admitted library artifact,
and neither may be imported, evaluated, published, approved, activated, or
used on hardware from this decision. M6 remains blocked on the recorded roles;
M5 remains externally blocked. Retain `<stop-orchestrator/>` in `GOAL.md`.
