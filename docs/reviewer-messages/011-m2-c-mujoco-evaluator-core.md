# Reviewer Message 011 - M2 C MuJoCo evaluator core

**Date:** 2026-09-02

## Decision

`CONTINUE`

## Evidence Reviewed

- Executor commits `99ee0b7` and `71b6cb7` contain the evaluator core, retained
  report, documentation, focused test, and the corrected ONNX fixture tracking
  rule.
- A detached clean worktree loaded the retained ONNX fixture, both frozen model
  variants, and the clean BAM checkout at `62bd8ce1...` without relying on an
  untracked artifact.
- Two independent 40-step runs produced byte-identical reports and trajectory
  digest `sha256:2b58cb...`; each used ten CPU ONNX calls and 40 pinned BAM
  controller updates.
- Contract freeze and branch hygiene passed, and the detached review worktree
  remained clean.
- Negative Reviewer probes rejected an unpinned BAM checkout, missing ONNX,
  unknown task, and walking-only smoke under the backflip task.
- The BAM-enabled broad suite passed with the evaluator check reachable from
  `tests/run_all.py`.

## Findings

The core validates the task's referenced contracts, model root and scene,
interface shapes/order, BAM parameter and source commit, CPU-only ONNX provider,
and fixed 5 ms / decimation-four / unfiltered loop before stepping. It consumes
BAM's own CPU MuJoCo controller rather than duplicating the actuator equations.

The retained zero-policy result is correctly scoped as infrastructure-only and
sets task success to `not_evaluated`. It does not yet provide the full report
bundle, visible/held-out case split, or frozen task classifiers.

## Milestone State

The M2 evaluator core is accepted. M2 remains open for deterministic case
execution, complete policy-bound artifacts, and repeatability proof with the
designated official walking ONNX.

## Next Slice

Proceed to `docs/briefs/012-m2-development-suite-and-report-bundle.md`. Build a
visible development suite and complete artifact envelope without inspecting a
final Genesis candidate or claiming task success.
