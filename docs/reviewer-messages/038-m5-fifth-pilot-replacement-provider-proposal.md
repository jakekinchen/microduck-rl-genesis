# Reviewer Message 038 - M5 fifth-pilot replacement-provider proposal

**Date:** 2026-09-04

## Decision

**NUDGE** - do not accept slice 038 or authorize paid compute yet.

The proposal is otherwise a coherent, non-authorizing, no-fallback replacement
for the terminal fourth pilot, but two corrections are required before an
independent acceptance decision:

1. The proposal binds `scripts/run_m5_cuda_pilot.sh`, whose embedded
   `PRICE_USD_PER_HOUR=1.62` is the accepted fourth-pilot rate. The replacement
   proposal binds `$1.656/hour` and a `$3.312` two-hour ceiling. Preserve the
   accepted fourth-pilot harness byte-for-byte, create and bind a fifth-specific
   harness with the exact `$1.656/hour` rate, and add a validator assertion plus
   a negative regression that rejects harness/catalog/limit rate disagreement.
2. `GOAL.md` still presents the consumed fourth-pilot `$1.62/hour`
   `hyperstack_A100_80G` preference and `$3.24` ceiling as current human
   constraints. Mark them historical and explicitly state the no-retry rule,
   the proposed exact `massedcompute_A100_sxm4_80G_DGX` replacement type, and
   its `$1.656/hour` / `$3.312` limits.

After correction, refreeze the harness, proposal semantic/file, and schema
bindings as applicable; rerun the complete local authority-enabled suite,
proposal mutation tests, static CUDA validation, artifact validation, manifest
and immutable-log checks, workflow audit, diff checks, and a closing
authenticated empty Brev inventory. Submit a new committed handoff for
independent review.

## Verified Non-Authorizing Evidence

- Reviewed HEAD: `86da0ef`.
- Proposal byte SHA-256:
  `7cec37d6fe17788eb3097103548e4afc019ed0bbe5b91993515940695811d918`.
- Proposal semantic SHA-256:
  `ce93bd16450b184a4032ff2dff6dee5d5bb7d5322198cbdd303e6db340b45601`.
- Schema SHA-256:
  `5ffa816b0e4c649359e07500974c29dc1674565577ed8dd63fc285c598688102`.
- Bound fourth-pilot harness SHA-256:
  `86e964348ec5bb64f22b64bdee6b3eb446923b2e35f2b8e5f54390eda08798ef`.
- The accepted correction and Reviewer chain, terminal-negative fourth-pilot
  boundary, deterministic source bundles, immutable container digest, exact
  catalog row, dry-run result, suite-first order, four 64-by-5 public-development
  smokes, receipt contract, exact-ID teardown, prohibitions, and
  `compute_authorized=false` all otherwise validated.
- The fresh read-only catalog and exact container-mode immutable-digest dry run
  succeeded for `massedcompute_A100_sxm4_80G_DGX` at `$1.656/hour`.
- Fresh authenticated `brev ls --json` was empty. Review created or mutated no
  Brev resource.
- Previously accepted receipts were unchanged, nine manifests and 68 immutable
  logs validated, and the worktree was clean.

## Claim And Authority Boundary

This NUDGE grants no compute authority. It accepts no CUDA smoke, M5, task,
policy, candidate, held-out, publication, activation, transfer, or physical
success. The failed `hyperstack_A100_80G` fourth-pilot type must not be retried.
Any later paid compute still requires a corrected independently accepted
proposal and a fresh exact committed Manager authorization.

Retain `<stop-orchestrator/>` in `GOAL.md`.
