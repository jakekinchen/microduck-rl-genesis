# Slice Brief 005 - M1 official mjlab fixture consumer

**Date:** 2026-09-01

## Objective

Make the exact pinned `bam.mjlab.BamActuator` consume the approved open-loop
and 14-servo closed-loop fixtures through the official mjlab/MuJoCo Warp path.
Keep the deployed adapter's `mjlab-deployed-v1` behavior distinct from BAM core.

## Acceptance Criteria

- Refuse any BAM checkout other than
  `62bd8ce12154340be97e06f7f41a0ca8f116d967`, any dirty authority checkout,
  or any runtime outside that checkout.
- Re-execute all approved open-loop rows through the pinned official mjlab
  implementation, including deployed friction behavior and selective reset.
- Build the canonical 14-servo model through official mjlab plus MuJoCo Warp,
  use 5 ms physics, one world, HOME target, fixed 7.35 V, no randomization,
  no voltage drop, and no command delay, and consume the retained every-step
  trajectory under explicit profile-aware tolerances.
- Record runtime/device/backend versions and whether MuJoCo Warp executed on
  CPU or CUDA. A CPU run is acceptable for semantic conformance; it is not GPU
  throughput evidence.
- Report every per-joint/time and base-height violation. Preserve the known
  deployed-mjlab no-quadratic-gate divergence rather than changing the fixture
  or adapter to hide it.
- Wire the official consumer into a reproducible command. If it cannot run in
  the local authenticated environment without paid compute, retain the exact
  terminal prerequisite and stop without provisioning a Brev instance.

## Expected Files

- an official-adapter consumer under `tests/` or `scripts/`
- minimal runtime/authority helpers needed by that consumer
- `docs/session-logs/005-executor-m1-official-mjlab-fixture-consumer.md`
- generated contract metadata only if required to bind a distinct deployed
  profile tolerance

## Validation

```bash
BAM_REPO=<pinned-checkout> OFFICIAL_MJLAB_PYTHON=<locked-python> scripts/verify_official_mjlab_fixtures.sh
.venv-apple/bin/python scripts/freeze_contract.py --check
git diff --check
```

If the full consumer runs locally, also rerun the BAM-enabled repository test
suite. If it requires CUDA, record the exact local failure and leave the M1
checklist item open.

## Evidence Boundary

Passing establishes fixture consumption by the exact pinned official adapter
on the recorded device only. It does not establish CUDA throughput, full model
reconciliation, walking, backflip, task success, held-out evaluation, or
physical authority.

## Stop Conditions

- The official adapter import or MuJoCo Warp execution requires unavailable
  CUDA in the current no-spend envelope.
- Passing would require modifying pinned BAM, assisting either simulator, or
  conflating BAM-core and deployed-mjlab behavior.
- The source/model/fixture digests do not match the approved locks.
