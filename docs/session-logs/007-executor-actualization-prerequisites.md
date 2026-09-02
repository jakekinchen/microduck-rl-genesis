# Executor Session Log 007 - Actualization prerequisites

**Date:** 2026-09-02

## Slice

Executed `docs/briefs/007-actualization-prerequisites.md` to remove three
prerequisites that blocked the next M1 semantics slice: stale actualization
guidance, a sibling-environment dependency in the official mjlab fixture lane,
and branch-wide whitespace failures caused by byte-preserved receipt logs.

## Files Changed

- `.gitattributes`
- `.github/workflows/contract.yml`
- `.gitignore`
- `README.md`
- `TRAINING_ACTUALIZATION.md`
- `docs/autonomous-workflow/05-devops-and-session-ops.md`
- `docs/session-logs/007-executor-actualization-prerequisites.md`
- `microduck_contract/actuator/bam-m6-xl330-v1.lock.json`
- `scripts/check_branch_hygiene.sh`
- `scripts/freeze_contract.py`
- `scripts/setup_official_mjlab.sh`
- `scripts/verify_official_mjlab_fixtures.sh`
- `validation/official-mjlab/pyproject.toml`
- `validation/official-mjlab/uv.lock`

## Implementation

- Reconciled `TRAINING_ACTUALIZATION.md` with the accepted M1 BAM, official
  adapter, and model-reconciliation evidence, then made walking/backflip
  semantics and the divergence decision the immediate queue.
- Added a repo-owned Python 3.12 optional validation project locked by uv and a
  setup script that verifies every direct runtime version before allowing the
  official adapter gate to run.
- Kept the official lane out of default CI and exposed it through an explicit
  manual macOS workflow that checks out the exact BAM authority commit.
- Declared a narrow Git whitespace attribute for raw Apple baseline `.log`
  receipt payloads. No accepted receipt was normalized or rewritten.
- Added a branch-hygiene gate that verifies every accepted receipt manifest,
  requires every exempt log to be manifest-bound, confirms the exact Git
  attribute, and then runs `git diff --check` across the branch.

## Failure Trail

The first new-environment run exposed two imports that the published mjlab and
pinned BAM source do not declare for this source-checkout consumer:

1. `scipy` was absent when mjlab imported its manager modules.
2. `colorama` was absent when the pinned BAM source imported `bam.core.base`.

Both were added at the exact versions already present in the official Microduck
lock (`scipy==1.18.0`, `colorama==0.4.6`). The environment was re-locked and
rebuilt; no import shim or sibling virtual environment was used.

## Validation

All final commands exited 0:

```text
uv lock --project validation/official-mjlab
scripts/setup_official_mjlab.sh
.venv-apple/bin/python scripts/freeze_contract.py
BAM_REPO=<fresh-detached-62bd8ce-checkout> scripts/verify_official_mjlab_fixtures.sh
scripts/check_branch_hygiene.sh origin/main
.venv-apple/bin/python scripts/freeze_contract.py --check
git diff --check
bash -n scripts/setup_official_mjlab.sh scripts/check_branch_hygiene.sh scripts/verify_official_mjlab_fixtures.sh
```

Results:

- The setup script created its own environment and verified exact direct
  versions for colorama, mjlab, MuJoCo, MuJoCo Warp, SciPy, PyTorch, and Warp.
- The official adapter consumed all 29 open-loop rows with zero field error.
- The closed-loop fixture's all-step maximum was 0.276 degrees for joints and
  1.962 mm for base height; its step-60 errors were 0.079 degrees and 0.140 mm.
- All 20 accepted receipt files retained their recorded SHA-256 values; all
  eight exempt raw logs were manifest-bound.
- Contract generation and checked-in snapshots agree.

## Reachability

The fresh-clone procedure is the documented README path and the
`workflow_dispatch` job runs the same setup and verification scripts. The
branch-hygiene script is also called by the default deterministic CI job.

## Evidence Boundary

This slice establishes reproducible optional fixture validation and evidence
hygiene. It does not define task semantics, evaluate policy success, establish
CUDA execution, or grant physical authority.

## Suggested Next Slice

Return to `docs/briefs/008-m1-walking-task-semantics.md` and freeze walking
semantics before inspecting or training any final policy candidate.
