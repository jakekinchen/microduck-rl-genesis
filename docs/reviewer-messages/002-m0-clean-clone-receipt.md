# Reviewer Message 002 - M0 clean-clone receipt

**Date:** 2026-09-01

## Decision

`CONTINUE`

## Evidence Reviewed

- Receipt `20260901T215219Z-2ce72a94` binds source commit
  `2ce72a9492789c23d2191c7517e28a5b6bb12678`, which is an ancestor of the
  current branch.
- All 20 manifest paths exactly match tracked receipt files, and
  `shasum -a 256 -c SHA256SUMS` passes.
- Both source-status receipts are empty. Sanitized metadata records only the
  allowed machine/OS/package fields and contains no serial, UUID, home path,
  credential, or secret token.
- Both ONNX files pass full ONNX checker validation, use opset 17, contain no
  external-data tensors or sidecars, and expose 61D input to 14D output.
- Full test, two Metal/MPS 64x5 smokes, two randomized export comparisons, and
  two 60-step real-observation comparisons passed with the values recorded in
  the Executor log.
- The temporary clean clone was removed after the copied manifest passed.

## Findings

The first receipt commit omitted extension-ignored payloads. The follow-up
commit added a receipt-scoped ignore exception and tracked every manifest entry;
the exact tracked-versus-manifest comparison now passes. Raw logs retain
trainer-emitted spacing and ANSI output by design and remain byte-bound by the
manifest.

No unresolved M0 defect remains. BAM authority comparisons are still absent,
but they are explicitly M1 and did not masquerade as M0 passes.

## Milestone Decision

M0 is closed. The repository has a reproducible Apple artifact-production
baseline for the exact recorded source commit. Its proof class is
`artifact_validated`; this decision does not establish walking, backflip,
held-out reference, hardware, or physical success.

## Next Slice

Proceed to `docs/briefs/003-m1-authoritative-bam-golden-vectors.md`. Preserve
the observed authority drift: the official Microduck RL lock names BAM commit
`62bd8ce12154340be97e06f7f41a0ca8f116d967`, while the live
`mjlab_frictionloss` branch currently points at
`57d13ead53206a6bf0db3d66f86506ae8c2ce01a`. Do not silently substitute branch
head for the locked implementation.
