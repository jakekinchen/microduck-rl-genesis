# Slice Brief 014 - M2 pinned BAM materializer

**Date:** 2026-09-02

## Objective

Replace every drift-prone fresh-clone BAM instruction with one repo-owned
materializer that obtains and verifies the exact authority commit already bound
by the contract.

## Acceptance Criteria

- Read the repository URL and authority commit from the frozen contract; do not
  accept a branch name or a caller-supplied replacement commit.
- Clone or fetch, detach at the exact commit, then verify exact HEAD, expected
  origin, and a clean worktree.
- Refuse to reuse a dirty or wrong-origin destination.
- Update current README and validation guidance to use the helper.
- Add a local-git regression proving that moving a branch after the first
  materialization cannot change the selected authority.
- Preserve all accepted BAM fixtures and evaluator evidence byte-for-byte.

## Validation

```bash
.venv-apple/bin/python tests/test_materialize_bam_authority.py
scripts/materialize_bam_authority.py /tmp/microduck-bam-authority
BAM_REPO=/tmp/microduck-bam-authority .venv-apple/bin/python tests/test_evaluator_core.py
BAM_REPO=/tmp/microduck-bam-authority .venv-apple/bin/python tests/test_evaluator_bundle.py
python scripts/freeze_contract.py --check
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

This corrects authority materialization only. It does not regenerate fixtures,
repin BAM, evaluate a candidate, or add policy/physical evidence.

## Stop Conditions

- The exact commit disappears from the declared upstream repository.
- The destination is dirty, has the wrong origin, or would require destructive
  cleanup.
- The next action would repin authority, use credentials, spend externally,
  publish, inspect a final candidate, activate a policy, or operate hardware.
