# Executor log 047 - M6 real artifact resolution

**Date:** 2026-09-04

**Role:** Executor

**Brief:** `docs/briefs/047-m6-real-artifact-resolution.md`

## M5 External Blocker

Reviewer messages 037, 041, 043, and 046 establish four consecutive exact
provider/type failures before a usable remote execution boundary:

- `hyperstack_A100_80G` / `tpo91g7kj`: provisioning health;
- `massedcompute_A100_sxm4_80G_DGX` / `i1bsb56r7`: provisioning connectivity;
- `a2-highgpu-1g:nvidia-tesla-a100:1` / `urmhasks7`: provisioning
  connectivity, with a READY signal only after the terminal decision;
- `gpu_1x_a100_sxm4` / `qcolxobcf`: 900-second provisioning/readiness window.

Every exact workspace was deleted and each receipt was independently accepted.
No eighth pilot was proposed or created. Authenticated Brev inventory remained
empty throughout this slice.

## Immutable Candidate Retrieval

- Official candidate: Pollen Robotics `alpha_walking.onnx` from Hugging Face
  revision `088524a64e2557dc453256b6071dbb9d23888802`, SHA-256
  `e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
- Community candidate: `RemiFabre/microduck-rough-walk-e` revision
  `fa7b27eeb5610d3b351362f4bd71691ee8be3d7d`, policy SHA-256
  `5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040`.
  Its model card names training commit
  `6cd45fc7a865299f118f7671142465d377853928`, task
  `Mjlab-Hostile-FinetuneFeetProgress-MicroDuck`, and run
  `pollen-robotics/hostile-e-finetune-feet-progress-20260830-0103`.
- Thirteen files were retrieved only from URLs containing full immutable
  revisions. A fresh re-fetch reproduced every committed size and SHA-256.
  Downloaded Python and both ONNX policies remained inert bytes.

## Manifest-v2 Resolution

- Official: license and normalized ONNX are bound. BAM, evaluator, evidence,
  exporter, model, normalizer, source checkpoint, and task are missing.
- Community: BAM, exporter, license, model, normalized ONNX, and task are
  bound. Evaluator, raw evidence, a separately attributable normalizer, and an
  immutable source checkpoint are missing. The exact exporter invocation also
  remains a source-provenance blocker.
- Both candidates are `rejected_incomplete`, `authority=none`, and emit no
  formal policy manifest v2. The resolution schema and validator reject digest
  drift, unpinned URLs, unbound files, fabricated missing-role bindings,
  lifecycle/authority promotion, and use of a resolution report as a formal
  manifest.

## Verification

- Both non-executing real-candidate validation commands: pass.
- Offline fail-closed real-candidate test: pass.
- Fresh immutable re-fetch: 13/13 remote files match committed bytes.
- Existing synthetic artifact-contract tests remain unchanged and passing.
- Full authority-enabled local suite: `tous les tests passent`, including both
  environment smokes. Python/JSON compilation, branch hygiene, workflow, and
  diff checks pass. Final authenticated Brev inventory is empty.

## Evidence Boundary And Stop

This is immutable retrieval and attribution evidence only. Neither candidate
is accepted into a library or eligible for evaluation, publication, approval,
activation, task claims, transfer, or hardware. M6 remains blocked on the
listed roles. M5 remains externally blocked; no paid compute authority exists.
