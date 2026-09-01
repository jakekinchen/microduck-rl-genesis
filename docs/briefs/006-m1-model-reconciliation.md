# Slice Brief 006 - M1 model reconciliation

**Date:** 2026-09-01

## Objective

Reconcile the repo-local Genesis model bundle against an explicit committed
official Microduck source revision. Retain a machine-readable report for
canonical walk, all-collisions, backlash, and rollers variants without
collapsing those variants or changing physics to force equality.

## Acceptance Criteria

- Require an explicit official Microduck repository and immutable commit. Read
  model inputs from committed blobs, not an uncommitted working tree.
- Bind official commit/tree and source paths plus local model-lock digests.
- For each available variant, compare compiled MuJoCo counts, body names and
  masses/inertias, joint names/order/types/ranges/armature/damping/friction,
  actuator names/order/targets/types/ranges, collision geom membership, and
  keyframe names/qpos/ctrl.
- Classify every difference as byte-identical input, semantically identical
  compiled model, expected variant difference, or unresolved divergence.
- Fail on unresolved differences in the canonical walk model. Keep walk,
  all-collisions, backlash, and rollers variants separate.
- Retain the report and bind it from the generated model contract. Do not edit
  either model merely to make the report green.

## Expected Files

- a deterministic reconciliation generator under `scripts/`
- a retained report under `microduck_contract/model/`
- a focused report validator under `tests/`
- generated model lock bindings as needed
- `docs/session-logs/006-executor-m1-model-reconciliation.md`

## Validation

```bash
<python> scripts/reconcile_models.py --official-repo <repo> --official-commit <commit>
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python <focused-validator>
BAM_REPO=<pinned-checkout> .venv-apple/bin/python tests/run_all.py
git diff --check
```

## Evidence Boundary

A clean report establishes structural and selected numerical model agreement
for the exact committed inputs only. It does not establish contact equivalence,
task semantics, policy quality, held-out performance, or physical authority.

## Stop Conditions

- No immutable official commit can be named.
- The canonical walk model has an unresolved semantic difference.
- Reconciliation would require overwriting user-owned official-repo changes or
  silently normalizing distinct model variants.
