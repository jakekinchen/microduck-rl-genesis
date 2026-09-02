# Slice Brief 007 - Actualization prerequisites

**Date:** 2026-09-02

## Objective

Correct three control-plane gaps before resuming M1 semantics: synchronize the
execution queue with accepted work, make the optional official-mjlab validation
lane reproducible from a fresh clone, and define a precise whitespace policy
for byte-preserved receipt logs.

## Acceptance Criteria

- Replace stale evidence and "Immediate next three runs" text in
  `TRAINING_ACTUALIZATION.md` with the accepted M1 state and unambiguous next
  work.
- Add a repo-owned, frozen optional mjlab/MuJoCo Warp environment plus setup and
  verification commands that work without a sibling checkout's prebuilt venv.
- Keep official-adapter validation separate from default lightweight CI while
  making the optional lane explicit and reproducible.
- Preserve receipt payload bytes. Exempt only manifest-bound raw log files from
  trailing-whitespace diagnostics, verify their manifests, and keep ordinary
  source/docs subject to `git diff --check`.
- Enforce the policy in a branch-hygiene script and CI path, with deterministic
  tests where practical.
- Write an Executor log and scoped implementation commit, then a separate
  Reviewer decision before returning to walking semantics.

## Validation

```bash
scripts/setup_official_mjlab.sh
BAM_REPO=<clean-pinned-checkout> scripts/verify_official_mjlab_fixtures.sh
scripts/check_branch_hygiene.sh origin/main
python scripts/freeze_contract.py --check
```

## Evidence Boundary

This slice improves reproducibility and evidence hygiene. It does not add task
semantics, evaluate a policy, establish CUDA execution, or grant physical
authority.

## Stop Conditions

- The locked optional environment cannot install on the current supported
  platform from a fresh environment.
- Receipt verification fails; do not rewrite captured evidence to make a
  whitespace check pass.
