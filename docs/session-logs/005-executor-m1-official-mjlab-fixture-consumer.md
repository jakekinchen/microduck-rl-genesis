# Executor Session Log 005 - M1 official mjlab fixture consumer

**Date:** 2026-09-01

## Slice

Executed `docs/briefs/005-m1-official-mjlab-fixture-consumer.md` with the exact
Rhoban/BAM checkout at `62bd8ce12154340be97e06f7f41a0ca8f116d967` and a local
official mjlab 1.3.0 / MuJoCo Warp 3.8.1 runtime on Apple CPU. No cloud or Brev
resource was provisioned.

## Files Changed

- `README.md`
- `microduck_contract/actuator/bam-m6-xl330-v1.lock.json`
- `scripts/freeze_contract.py`
- `scripts/verify_official_mjlab_fixtures.sh`
- `tests/test_official_mjlab_fixtures.py`
- `docs/session-logs/005-executor-m1-official-mjlab-fixture-consumer.md`

## Implementation

- Pinned the official adapter runtime versions in the generated actuator lock:
  mjlab 1.3.0, MuJoCo 3.10.0, MuJoCo Warp 3.8.1, Warp 1.12.0, and Torch 2.9.1.
- Added a wrapper that requires explicit paths to the locked Python and clean
  BAM authority checkout; it does not install dependencies or provision
  compute.
- Added fail-closed checks for BAM commit, cleanliness, tree, source digests,
  parameter digest, runtime versions, and actual imported module location.
- Re-executed all 29 open-loop rows through the pinned official sources,
  including the adapter's deployed friction budget and selective reset path.
- Built the canonical 14-servo model through real mjlab `Scene`/`Simulation`,
  the pinned official `bam.mjlab.BamActuator`, and MuJoCo Warp on CPU. The run
  used HOME, 5 ms physics, fixed 7.35 V, no voltage drop, no randomization, and
  no command delay. The deployed adapter retained its default stiff friction
  constraint and documented no-quadratic-gate behavior.

The first prototype called `scene.reset()` and assumed the configured initial
state had been written to simulation. Inspection showed the 14 joint positions
were actually at zero and the root at the model keyframe, producing an honest
terminal mismatch of 26.06 degrees and 174.7 mm. The final consumer explicitly
writes the declared root pose, zero velocity, and HOME joint state, verifies
that state before stepping, and does not otherwise assist either backend.

## Validation

All final commands exited 0:

```text
BAM_REPO=<pinned-checkout> OFFICIAL_MJLAB_PYTHON=<locked-python> scripts/verify_official_mjlab_fixtures.sh
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python -m py_compile tests/test_official_mjlab_fixtures.py scripts/freeze_contract.py
sh -n scripts/verify_official_mjlab_fixtures.sh
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
git diff --check
```

Focused results:

- All 29 open-loop rows were exact for control voltage, motor torque, and the
  deployed-mjlab friction budget.
- Selective reset cleared the selected prior torque and preserved battery
  voltage exactly.
- Official mjlab/MuJoCo Warp worst joint deviation: `0.276 deg` over all 120
  steps and `0.079 deg` at step 60.
- Worst base-height deviation: `1.962 mm` over all steps and `0.140 mm` at
  step 60.
- Runtime device: Warp `cpu` on Apple arm64; CUDA was neither available nor
  required. This is semantic conformance evidence, not GPU throughput proof.

The locked environment contains an installed `mjlab_microduck` task entry
point. While pinned BAM imports `bam.mjlab`, that unrelated task entry point
prints a non-fatal circular-import warning and is not registered. The consumer
verifies that the actuator source actually loaded from the exact pinned BAM
checkout before accepting evidence.

## Reachability

`scripts/verify_official_mjlab_fixtures.sh` is the explicit official dependency
lane and is documented in the numerical-validation section of `README.md`.
Changing the runtime versions or generated actuator lock fails before physics
execution.

## Evidence Boundary

This establishes that the exact pinned official deployed adapter consumes both
approved fixture classes on the recorded Apple CPU MuJoCo Warp runtime. It does
not establish CUDA throughput, complete model reconciliation, walking,
backflip, task success, held-out evaluation, or physical authority.

## Suggested Next Slice

Reconcile the locked Genesis and official mjlab model manifests: counts,
canonical versus collision/backlash variants, masses, inertias, keyframes,
joint limits, and actuator ordering. Keep variants distinct and retain a
machine-readable difference report before deciding whether any source model
must change.
