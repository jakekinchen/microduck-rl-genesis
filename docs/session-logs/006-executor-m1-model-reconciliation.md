# Executor Session Log 006 - M1 model reconciliation

**Date:** 2026-09-01

## Slice

Executed `docs/briefs/006-m1-model-reconciliation.md` against committed
official Microduck revision `109e06d4ce4921b635c5609e5304079fc30960ae`
(tree `98d8b93e4425388ec077a4847117c5043fc4552e`). Inputs were materialized
from `git archive`; the sibling checkout's working tree was not read as model
authority or modified.

## Files Changed

- `microduck_contract/model/reconciliation-v1.json`
- `microduck_contract/model/reconciliation-v1.lock.json`
- `scripts/freeze_contract.py`
- `scripts/reconcile_models.py`
- `tests/run_all.py`
- `tests/test_model_reconciliation.py`
- `docs/session-logs/006-executor-m1-model-reconciliation.md`

## Implementation

- Added a deterministic generator that requires an explicit official repo and
  immutable commit, materializes only committed model blobs, and binds commit,
  tree, date, subtree, local model locks, source digests, and MuJoCo version.
- Compared compiled counts; ordered bodies, masses, inertias, and inertial
  positions; joint order/types/ranges/limits/armature/damping/friction;
  actuator order/targets/types/ranges; collision geoms; and keyframe qpos/ctrl.
- Kept six variants separate: walk, all-collisions, walk-backlash,
  all-collisions-backlash, rollers, and rollers-backlash.
- Added a retained report lock and a default runner check that rehashes all
  local inputs and recompiles every local semantic manifest.

## Validation

All final commands exited 0:

```text
.venv-apple/bin/python scripts/reconcile_models.py --official-repo <repo> --official-commit 109e06d4ce4921b635c5609e5304079fc30960ae
.venv-apple/bin/python scripts/freeze_contract.py
<regenerate-to-temp-and-cmp-with-retained-report>
.venv-apple/bin/python tests/test_model_reconciliation.py
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python -m py_compile scripts/reconcile_models.py tests/test_model_reconciliation.py scripts/freeze_contract.py
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
git diff --check
```

Results:

- Retained report SHA-256:
  `f34cacf7b831a6a2fd53c7ca35c55ec7d3f83ffc2bc2c5f1fffa3ad522181601`.
- Regeneration was byte-identical.
- 69 of 70 local runtime-source files are byte-identical to the official
  commit. All six in-scope root inputs are byte-identical.
- All six compiled manifests are semantically identical local versus official.
- Walk/all-collisions: 16 bodies, 15 joints, 14 actuators; backlash adds 14
  passive joints; rollers adds four bodies and four passive joints; the
  combined rollers-backlash model has 20 bodies, 33 joints, and 14 actuators.
- The 47 official-only `.part` CAD source files are recorded as non-runtime
  inputs; the runtime models reference retained STL assets.
- The BAM-enabled full suite ended with `tous les tests passent`; no BAM or
  model reconciliation check skipped.

## Preserved Deferred Divergence

The first generator run stopped on `ball.xml`. The official commit adds
`priority="1"` to `ball_geom`; the repo-local file omits it. Ball is not used by
the six Slice 006 variants, so the final report classifies this as one explicit
`unresolved-divergence-outside-slice` rather than hiding it or blocking the
in-scope reconciliation. Ball task semantics remain open and must resolve this
before any ball model or task claim.

## Evidence Boundary

This establishes structural and selected numerical agreement for the six exact
committed model variants. It does not establish cross-engine contact
equivalence, task semantics, policy quality, held-out performance, or physical
authority.

## Suggested Next Slice

Freeze walking task semantics first: command ranges, 61D observation use,
14D action interpretation, control timing, curriculum/assistance state,
termination, reward-independent success definitions, and acceptance starts.
Keep the deferred ball contact-priority difference out of walking scope and in
the durable report.
