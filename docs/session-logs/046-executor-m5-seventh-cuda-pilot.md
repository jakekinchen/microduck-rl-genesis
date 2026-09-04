# Executor Session 046 - M5 seventh CUDA pilot

**Date:** 2026-09-04

## Baseline And Authority

- Accepted corrected handoff: `e3b9fb4`.
- Reviewer 045 acceptance: `ad175f1`.
- Manager authority 013 is committed with this brief before paid action.
- Exactly one workspace and at most one harness invocation are authorized.

## Pre-Create And Workspace

- Manager 013 committed at `f2b8ebb` before creation. Every accepted hash,
  twice-reproduced bundle, live Lambda row, immutable dry run, clean source,
  and empty-inventory gate passed.
- Create anchor: `2026-09-04T08:20:21Z`. Exactly one workspace was created:
  `microduck-m5-pilot7-20260904`, ID `qcolxobcf`, exact Lambda type
  `gpu_1x_a100_sxm4`.
- Brev's create wait timed out at `08:25:28Z`; inventory was
  `STARTING / BUILDING / NOT READY / UNHEALTHY`.

## Readiness Terminal Result

- The explicit 900-second state machine retained 36 authenticated exact-ID
  polls at least 15 seconds apart. Every poll was
  `UNHEALTHY / BUILDING / NOT READY / UNHEALTHY`; maximum consecutive
  qualifying count was zero.
- At `08:35:29Z`, 908 seconds after create, the window expired and the pilot
  became terminal negative at `workspace-provisioning-readiness-window`.
- Because three qualifying polls never existed, the no-op shell and disk probes
  were not permitted. Zero files were uploaded and the harness was invoked zero
  times; no suite, smoke, or export ran.

## Receipt, Cost, And Teardown

- Receipt: `receipts/m5/pilot/20260904T082021Z-qcolxobcf/`.
- Eighteen payloads, including primary pre-create/create/readiness/delete/
  teardown logs, verify against manifest SHA-256
  `4b11eabf7f7c5bd4ebbe960c38f3a477fd92bdb76e4277cb0465c85a2d1b8c65`.
- Exact-ID deletion was requested at `08:35:45Z`; inventory became empty at
  `08:37:49Z` and five later polls stayed empty through `08:38:20Z`.
- Create-to-terminal: 908 seconds / `$0.602307`. Create-to-empty: 1,048
  seconds / `$0.695173` at `$2.388/hour`, below the two-hour / `$4.776`
  ceiling. These are estimates, not a provider invoice.

## Evidence Boundary

Provisioning/readiness-window evidence only. Manager 013 is consumed. This
proves no shell, disk, CUDA, smoke, M5, task, policy, candidate, held-out,
publication, activation, transfer, or physical success. No retry or replacement
is authorized.

## Step-9 Flags For Reviewer

- Verify the exact authority chain, inputs, single workspace identity, and
  primary control-plane logs.
- Recompute 36 poll intervals, qualifying counts, 908/1,048-second clocks, and
  both cost figures.
- Confirm no shell/disk probe, upload, or harness invocation was permitted.
- Verify all 18 payloads, exact-ID teardown, five later empty polls, previous
  receipt immutability, full local gates, and final empty inventory.
- Retain the stop sentinel and authorize no retry or replacement.

## Reviewer Outcome

The independent Reviewer returned CONTINUE on exact Executor handoff
`6e6e1db352a8212b8ad31f74f0a7d8096312bb75`. Reviewer Message 046 accepts
the result only as terminal-negative provisioning/readiness-window evidence
with exact-ID teardown and empty inventory. Manager authority 013 is consumed;
no retry or replacement authority exists.
