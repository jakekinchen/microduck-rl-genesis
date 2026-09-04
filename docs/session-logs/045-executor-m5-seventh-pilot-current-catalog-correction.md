# Executor Session 045 - M5 seventh-pilot current-catalog correction

**Date:** 2026-09-04

## Baseline And Authority

- Reviewer 044 NUDGE commit: `edcc4e5`.
- The NUDGE accepted all reliability-protocol and validation gates but found
  that proposed Crusoe type `a100-80gb.1x` had disappeared from the live
  authenticated catalog.
- This correction is local and non-authorizing. No Brev resource, upload,
  remote execution, training, smoke, or export is permitted.

## Current Catalog Decision

At `2026-09-04T07:50:14Z`, Crusoe remained absent. No currently exposed
unused direct-provider row combined a practical fixed disk with stoppability.
The strongest currently exposed unused direct row is
`gpu_1x_a100_sxm4` from Lambda Labs: one A100 40 GB, 30 vCPUs, 200 GiB RAM,
fixed 512 GB disk, 600-second advertised boot estimate, non-stoppable,
rebootable, no flexible ports, at `$2.388/hour`.

This trades away stoppability and flexible ports but preserves practical disk,
direct-provider identity, and rebootability. The stronger shell-readiness state
machine and mandatory exact-ID deletion remain unchanged. The exact
immutable-container dry run selected only this type; inventory remained empty.

## Refrozen Bindings

- Opening commit: `0fda9b1`; correction implementation: `562730a`.
- Proposal byte SHA-256:
  `714da8cdd4e521e1ba0d088809ff568f29ec909b514d796a2d67c0a1c0564f53`.
- Proposal semantic SHA-256:
  `604eb30d560cbb5045c551af5094dada621d23e0c92697defccccdc6532c8b4c`.
- Schema SHA-256:
  `4d38202f7b97971b11af8d0e417fe0cef03ffa3a25b47d9aa1096104cfd970c7`.
- Seventh harness SHA-256:
  `a960bfd3b88bf9bad74eb3a53c0460b2d96d42c372b01464d55bc2c103f60571`.
- Exact Lambda rate and ceilings: `$2.388/hour`, 4,800-second inner harness,
  7,200-second global create-to-delete, and `$4.776`.
- The Crusoe type is explicitly prohibited as an unavailable substitution.
  Previously failed fourth/fifth/sixth types and seventh-pilot retry remain
  prohibited.
- The source commits and unique seventh-pilot bundle bytes are unchanged from
  slice 044 because the resource correction does not alter source inputs.

## Validation

- Exact validator and mutation suite: pass with 222 scalar mutations and 261
  deletions, including current exposure, direct Lambda identity, non-stoppable/
  rebootable/no-flex recovery properties, rate/cost, unavailable Crusoe,
  readiness state machine, no retry, and harness self-attestation.
- Full authority-enabled local suite: pass, including both environment smokes.
- Static CUDA, artifact, Python compilation, Bash, shellcheck, diff, branch
  hygiene, all manifests, accepted-receipt immutability, and workflow gates:
  pass.
- Authenticated inventory remained empty and no paid resource was created or
  mutated.

## Evidence And Authority Boundary

This correction proves only that the proposal is internally bound to a type
exposed in the authenticated catalog at the recorded time. The exact row must
still be present and identical at any future separately authorized pre-create
gate. `compute_authorized=false`; no Manager authority exists. No shell, CUDA,
smoke, M5, task, policy, candidate, held-out, publication, activation,
transfer, or physical success is claimed.

## Step-9 Flags For Reviewer

- Recheck the exact live Lambda row and dry run; distinguish current catalog
  exposure from future availability or shell readiness.
- Verify every refrozen hash and the unchanged source-bundle hashes.
- Confirm there is no currently exposed unused direct provider with both
  practical fixed disk and stoppability, and that Lambda's regressions are
  explicit rather than hidden.
- Exercise mutation tests for non-stoppable/rebootable/no-flex fields,
  unavailable Crusoe substitution, exact rate/cost, and every readiness gate.
- Re-run the full local suite, manifest/workflow gates, stop sentinel, and empty
  inventory. Create no Manager record or Brev workspace.

## Reviewer Outcome

The independent Reviewer returned CONTINUE on exact corrected Executor handoff
`e3b9fb43e3509725c257c677b6dc307e12a663f9`. Reviewer Message 045 accepts
the Lambda-bound proposal only as local non-authorizing evidence. Any paid
create still requires a fresh exact committed Manager authority and all bound
pre-create gates.
