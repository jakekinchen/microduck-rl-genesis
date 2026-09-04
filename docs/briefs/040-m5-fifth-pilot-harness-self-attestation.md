# Slice Brief 040 - M5 fifth-pilot harness self-attestation

**Date:** 2026-09-04

## Objective

Resolve Reviewer 039's final native-name staging defect locally. Make the
fifth-specific harness require, retain, and hash its exact proposal-bound file
without an old-name alias, then refreeze and independently review the proposal.

## Immutable Inputs And Boundaries

- Preserve `scripts/run_m5_cuda_pilot.sh` and every accepted receipt
  byte-for-byte.
- Preserve the exact fifth-pilot resource, `$1.656/hour` rate, `$3.312`
  ceiling, immutable image, source/runtime hashes, execution order, receipt and
  teardown requirements, and prohibitions.
- Keep `compute_authorized=false`; no Manager record is authorized in this
  slice.
- No Brev create/start/exec/copy/stop/delete, training, smoke, export,
  candidate, held-out, full CUDA matrix, publication, activation, transfer, or
  physical work.

## Required Correction

- The fifth harness must require `$INPUT_ROOT/run_m5_cuda_pilot_5.sh`, copy it
  to `$RECEIPT_ROOT/run_m5_cuda_pilot_5.sh`, and hash that exact receipt file.
- A deterministic local failure-path regression must stage only the native
  fifth filename, prove execution advances beyond bootstrap to the deliberately
  unavailable `host-nvidia-smi` gate, prove the retained file bytes/hash equal
  the proposal binding, and prove no old-name alias is present or required.
- The semantic validator must bind these self-attestation statements.
- Refreeze the fifth harness and proposal file/semantic hashes.

## Acceptance Criteria

- Focused validator and mutation/regression suite pass, including old-rate and
  old-name rejection.
- Original harness and accepted receipt trees are unchanged.
- Full authority-enabled local suite, static CUDA, artifact, Python/Bash/
  shellcheck, manifests, immutable logs, branch hygiene, workflow audit, diff
  checks, and closing authenticated empty Brev inventory pass.
- Executor changes are committed and an independent Reviewer records a final
  decision.
- Restore `<stop-orchestrator/>` at the Manager boundary.

## Evidence Boundary

This slice can prove only exact local staging and self-attestation semantics for
the non-authorizing fifth-pilot proposal. It cannot authorize compute or prove
CUDA smoke, M5, task, policy, candidate, held-out, publication, activation,
transfer, or physical success.
