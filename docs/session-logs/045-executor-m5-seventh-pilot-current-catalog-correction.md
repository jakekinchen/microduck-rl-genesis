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

## Work In Progress

Affected bindings and validation pending.
