# Slice Brief 032 - M5 deterministic evidence correction

**Date:** 2026-09-03

## Objective

Reproduce and diagnose all three deterministic failures preserved by the
second A100 pilot, trace every divergent field or byte sequence to its producer,
and implement the smallest local cross-platform correction without changing
model/evaluator semantics or rebaselining expected outputs.

## Immutable Inputs And Boundaries

- Reviewer 031 and accepted base commit `60a642a`.
- Checksum-bound receipt
  `receipts/m5/pilot/20260904T012843Z-7owxqf4pg/`, especially the immutable
  `logs/full-suite.log`.
- The accepted pilot-028 and pilot-031 receipt bytes must not change.
- Preserve the 61D observation, 14D action order, 50 Hz unfiltered loop, BAM
  authority, evaluator thresholds, and frozen M5 experiment contract.
- Do not create or use a Brev workspace. Do not authorize a third pilot or any
  candidate, held-out, full-matrix, publication, activation, transfer, or
  physical work.

## Required Diagnosis

1. `test_model_reconciliation.py`: compare the Linux compiled-manifest digest
   with frozen source fixtures and the current macOS result, then identify the
   exact producer fields responsible.
2. `test_evaluator_core.py`: compare the Linux report bytes with the frozen
   expected report and current macOS bytes, then identify every volatile or
   semantically different field.
3. `test_evaluator_bundle.py`: identify which of the five same-host artifacts
   differ between repeated generation and trace their nondeterministic bytes to
   the producer.

Classify every difference as semantic drift, platform/path/order/time
nondeterminism, or stale fixture authority. Do not change expected fixtures to
make tests pass.

## Acceptance Criteria

- Add failing-first regressions for Linux-style platform/path/order/metadata
  variation and byte-identical repeated generation.
- Canonicalize only non-semantic volatile fields at the producer boundary.
- Close all three focused failures locally with the exact pinned BAM authority.
- Run the full local suite with all available BAM and official authority,
  branch hygiene from `60a642a`, and the workflow audit.
- Commit a scoped Executor result and obtain an independent Reviewer decision.
- Only if all three failures close, draft a separate third-pilot proposal card
  with `compute_authorized=false`; paid provisioning remains forbidden absent a
  later exact Manager authorization.

## Hard Stops

Stop on a semantic model/evaluator change requiring refreeze, any accepted
receipt mutation, missing pinned authority with no honest local substitute, or
any need for paid/remote compute.

## Evidence Boundary

Local deterministic producer compatibility only. Passing this slice would not
prove CUDA training, task success, candidate admission, held-out performance,
policy acceptance, transfer, or physical authority.
