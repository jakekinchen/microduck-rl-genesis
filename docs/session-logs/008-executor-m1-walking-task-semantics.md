# Executor Session Log 008 - M1 walking task semantics

**Date:** 2026-09-02

## Slice

Executed `docs/briefs/008-m1-walking-task-semantics.md` against official
Microduck commit `109e06d4ce4921b635c5609e5304079fc30960ae` (tree
`98d8b93e4425388ec077a4847117c5043fc4552e`) and BAM commit
`62bd8ce12154340be97e06f7f41a0ca8f116d967`. The official source was
materialized with `git archive`; neither sibling working tree supplied task
contents.

## Files Changed

- `microduck_contract/README.md`
- `microduck_contract/tasks/walking-v1.json`
- `microduck_contract/tasks/walking-v1.lock.json`
- `microduck_contract/tasks/walking-v1.schema.json`
- `scripts/freeze_contract.py`
- `scripts/generate_walking_semantics.py`
- `tests/run_all.py`
- `tests/test_walking_semantics.py`
- `docs/session-logs/008-executor-m1-walking-task-semantics.md`

## Implementation

- Added an exact-commit generator that archives official source, imports its
  effective task config through the repo-owned locked mjlab environment, and
  compares comparable declarations against pure-data Genesis modules.
- Bound official commit/tree/source hashes, BAM authority, local source hashes,
  and the existing interface, actuator, model, and reconciliation locks.
- Froze the common 61D actor, 14D HOME-relative action, 5 ms/decimation-4
  control, command distributions, delays, noise, reward weights, curricula,
  reset declarations, and randomization ranges.
- Added a formal JSON Schema plus a default lightweight validator. When clean
  official and BAM checkouts are supplied, the validator regenerates the file
  byte-for-byte from both pinned authorities.
- Classified 28 semantic fields. Exact/equivalent declarations remain distinct
  from versioned divergences and backend-specific unavailable equivalence.
- Preregistered `microduck.walking-acceptance.v1`: 23 velocity/head command
  cases, two start populations, five counter-derived seeds, 230 required
  episodes, zero assistance, and thresholds for survival, velocity/head
  tracking, stop drift, slip, orientation, joint/torque margin, finite state,
  evaluator errors, and inference deadlines.

## Failure Trail and Preserved Divergences

The first generator subprocess resolved the venv interpreter symlink and
therefore bypassed the venv. It failed to import mjlab. The generator now keeps
the venv executable path and a subsequent clean authority import passed.

Effective config inspection found material differences that source constants
alone would have hidden:

- The official task package registers rough training and then rough play using
  a shared terrain object. The play mutation leaves the effective registered
  training object at 5x5 with terrain curriculum disabled, despite a 10x20
  source declaration. Genesis uses a 10x10 curriculum heightfield.
- Official training uses a 76D critic. Genesis gives its critic the 61D actor
  observation plus a 29D privileged vector (90D total).
- Official pseudo-inertia randomization scales trunk mass and inertia together;
  Genesis currently applies a trunk mass shift without scaling inertia.
- Foot-height/contact sensing, rough geometry, RNG streams, step lifecycle,
  rough boundary handling, and action input guarding are backend-specific.
- Official reset yaw is +/-3.14; Genesis uses +/-pi.

All remain explicit versioned rows. No training-trajectory-equivalence claim is
made and no opportunistic runtime fix was included in this semantics slice.

## Validation

Final focused and authority checks exited 0:

```text
scripts/setup_official_mjlab.sh
validation/official-mjlab/.venv/bin/python scripts/generate_walking_semantics.py --official-repo <repo> --official-commit 109e06d4... --bam-repo <clean-62bd8ce-checkout>
.venv-apple/bin/python scripts/freeze_contract.py
OFFICIAL_MICRODUCK_REPO=<repo> BAM_REPO=<clean-62bd8ce-checkout> OFFICIAL_MJLAB_PYTHON=<locked-python> .venv-apple/bin/python tests/test_walking_semantics.py
.venv-apple/bin/python scripts/freeze_contract.py --check
BAM_REPO=<clean-62bd8ce-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

Results:

- Authority regeneration was byte-identical.
- The validator reported 61D/14D/50 Hz, 28 classified fields, and 230
  preregistered cases.
- Generated task-lock metadata matches the semantic-file digest and suite ID.
- The BAM-enabled broad suite ended with `tous les tests passent`.
- Branch hygiene verified all immutable receipts and found no whitespace error.

## Evidence Boundary

This freezes declared walking semantics and a future acceptance battery. It
does not evaluate a candidate, prove task success, establish identical training
trajectories, transfer to hardware, or grant physical authority.

## Suggested Next Slice

Freeze backflip training and ordinary-start, zero-assistance acceptance
semantics, keeping reverse-curriculum and spotter populations excluded from
acceptance.
