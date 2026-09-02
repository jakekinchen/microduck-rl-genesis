# Slice Brief 009 - M1 backflip task semantics

**Date:** 2026-09-02

## Objective

Freeze the bounded flat-ground backflip task from clean
`Lulzx/microduck-backflip` commit
`8bde27eb141c8f14db05fc4370e536521203a98d` and the repo-local Genesis port.
Separate reverse-curriculum starts, task phase cues, and virtual-spotter state
from an ordinary-standing, zero-assistance acceptance definition.

## Acceptance Criteria

- Bind the exact source commit/tree and source digests, the repo-local backflip
  sources, the shared 61D/14D/50 Hz interface locks, full-collision model lock,
  BAM lock, and model reconciliation.
- Extract the effective base flat task rather than inferring it from comments
  or mixing in pedestal, cube, mat, reference-state, or specialist variants.
- Record the 4-second episode, fixed zero twist/head command, body-command phase
  and assistance slots, full-body collision semantics, action authority, BAM
  delay, resets, termination, reward terms, success state, spawn populations,
  reverse curriculum, and spotter decay/window/forces.
- Inventory every exact, equivalent, divergent, or backend-unavailable semantic
  field. Fail on an unclassified action, observation, timing, assistance, reset,
  contact, flight, landing, or success difference.
- Preregister acceptance before candidate inspection: ordinary standing HOME
  start, zero virtual force/torque, full action authority, no mid-flight or
  recovery initialization, takeoff, one uninterrupted airborne backward
  revolution, feet-first recontact, no intervening body contact, upright landing,
  finite state, joint/torque margins, and a continuous stable hold.
- Add a schema/validator, generated task-lock metadata, default runner reachability,
  Executor log, scoped implementation commit, and separate Reviewer decision.
- Do not train, replay a candidate, inspect final outcomes, or promote success.

## Expected Files

- `microduck_contract/tasks/backflip-v1.json`
- `microduck_contract/tasks/backflip-v1.schema.json`
- `microduck_contract/tasks/backflip-v1.lock.json`
- an exact-authority generator under `scripts/`
- a focused validator under `tests/`
- `docs/session-logs/009-executor-m1-backflip-task-semantics.md`

## Validation

```bash
<locked-official-python> <backflip-generator> --official-repo <clean-source-repo> --official-commit 8bde27eb... --bam-repo <clean-pinned-bam>
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python <focused-validator>
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python tests/run_all.py
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

Passing freezes declarations and a future classifier battery. It does not show
that any policy completes a backflip, lands autonomously, passes a held-out
reference evaluator, transfers to hardware, or has physical authority.

## Stop Conditions

- The pinned source task cannot be imported or its base task cannot be
  separated honestly from later assisted variants.
- A success threshold would be selected from candidate outcomes rather than a
  preregistered requirement.
- The next action would train a policy, activate hardware, spend paid compute,
  publish, or require credentials.
