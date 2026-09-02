# Slice Brief 010 - M1 versioned divergence decision

**Date:** 2026-09-02

## Objective

Close the final M1 choice by recording an explicit, versioned, machine-readable
decision for the known Genesis/official-mjlab semantic differences. Bind the
decision to both frozen task contracts and retain local conformance as the
chosen path; do not submit or publish upstream under the active constraints.

## Acceptance Criteria

- Enumerate every non-exact walking and backflip inventory row by stable field,
  classification, disposition, and task-contract digest.
- Distinguish accepted backend differences, required future evaluator
  normalization, deferred implementation reconciliation, and features that
  make training trajectories non-equivalent.
- Preserve exact deployed-interface, BAM-fixture, and model-conformance claims
  without promoting task success, held-out evidence, transfer, or physical
  authority.
- Add a schema, deterministic generator or validator, lock metadata, default
  runner reachability, Executor log, scoped commit, and separate Reviewer
  decision.
- Fail if either task contract drifts, a divergence disappears without an
  explicit superseding disposition, or the decision claims upstream
  submission/publication that did not occur.

## Expected Files

- `microduck_contract/divergence/decision-v1.json`
- `microduck_contract/divergence/decision-v1.schema.json`
- `microduck_contract/divergence/decision-v1.lock.json`
- a focused generator/validator under `scripts/` and `tests/`
- `docs/session-logs/010-executor-m1-versioned-divergence-decision.md`

## Validation

```bash
.venv-apple/bin/python <divergence-generator> --check
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python <focused-validator>
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python tests/run_all.py
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

This decision documents compatibility scope and unresolved differences. It is
not an upstream submission, an evaluator result, policy success, transfer
evidence, or physical authority.

## Stop Conditions

- A non-exact task inventory row cannot be represented without erasing its
  evidence boundary.
- The next action would publish, push, require credentials, spend paid compute,
  activate a policy, or operate hardware.
