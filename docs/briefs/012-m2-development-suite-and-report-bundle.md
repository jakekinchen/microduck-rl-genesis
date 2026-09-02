# Slice Brief 012 - M2 development suite and report bundle

**Date:** 2026-09-02

## Objective

Extend the accepted evaluator core into a deterministic visible development
suite and complete policy-bound artifact envelope. Keep development cases
separate from held-out acceptance and do not inspect or classify a final
Genesis candidate.

## Acceptance Criteria

- Add versioned visible development cases for deterministic standing and a
  small command sequence, with case IDs and seeds disjoint from frozen
  acceptance seeds.
- Emit `evaluation.json`, `trajectory.parquet`, `rollout.mp4`,
  `environment-lock.json`, and `attestation.json` into an isolated run root.
- Bind every artifact, policy, task, interface, model, BAM source, evaluator
  source/config, and runtime version by SHA-256; include no absolute paths or
  wall-clock fields in deterministic content.
- Produce deterministic evaluation/environment/attestation bytes and stable
  trajectory metrics under repeated identical runs. Declare any codec-level
  video nondeterminism explicitly rather than hiding it.
- Validate Parquet schema/row counts and decode the MP4 frames. A synthetic or
  designated non-candidate policy may prove plumbing only; task-success fields
  must remain `not_evaluated`.
- Add focused tests, Executor log, scoped commit, and separate Reviewer
  decision. Do not expose held-out cases or promote any policy.

## Expected Files

- versioned development suite and artifact writer under `evaluator/`
- focused bundle validator/tests and retained small fixture manifest
- `docs/session-logs/012-executor-m2-development-suite-and-report-bundle.md`

## Validation

```bash
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python <focused-bundle-test>
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python tests/run_all.py
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

This slice proves deterministic artifact production for visible development
cases only. It does not establish task success, held-out acceptance, backend
superiority, transfer, or physical authority.

## Stop Conditions

- A required writer/codec dependency is unavailable and the omission cannot be
  recorded honestly.
- Determinism would be claimed by deleting meaningful runtime or authority
  evidence.
- The next action would inspect a final candidate, reveal held-out cases,
  publish, push, require credentials, spend paid compute, activate a policy, or
  operate hardware.
