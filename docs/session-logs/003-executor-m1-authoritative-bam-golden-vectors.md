# Executor Session Log 003 - M1 authoritative BAM golden vectors

**Date:** 2026-09-01

## Slice

Executed `docs/briefs/003-m1-authoritative-bam-golden-vectors.md` against the
exact Rhoban/BAM commit pinned by the official Microduck RL lock:
`62bd8ce12154340be97e06f7f41a0ca8f116d967`.

The live `mjlab_frictionloss` branch had moved to
`57d13ead53206a6bf0db3d66f86506ae8c2ce01a`; it was not substituted for the
locked authority.

## Files Changed

- `microduck/bam_actuator.py`
- `microduck_contract/README.md`
- `microduck_contract/actuator/bam-m6-xl330-v1.lock.json`
- `microduck_contract/actuator/fixtures/bam-m6-xl330-v1-open-loop.json`
- `scripts/freeze_contract.py`
- `scripts/generate_bam_golden_vectors.py`
- `tests/run_all.py`
- `tests/test_bam_golden_vectors.py`
- `docs/session-logs/003-executor-m1-authoritative-bam-golden-vectors.md`

## Implementation

- Added a deterministic generator that refuses a dirty or wrong-revision BAM
  checkout, imports the pinned source, and records source/tree/license/parameter
  digests.
- Generated 29 edge and seeded cases covering firmware voltage, PWM/current
  saturation, back-EMF torque, zero/high velocity, sign/direction combinations,
  BAM-core friction, deployed-mjlab friction, and reset state.
- Preserved two explicit profiles in one fixture: BAM core uses the quadratic
  opposite-sign gate and strict magnitude direction; deployed mjlab omits the
  sign gate and treats equal magnitude as backdrive.
- Refactored the production Genesis actuator so voltage, torque, and Stribeck
  helpers are the exact code paths exercised by the fixture test.
- Bound the fixture digest and authority commit into the generated BAM lock.

The first fixture run found that the optional Genesis BAM-core mode handled
equal-magnitude opposing torques like deployed mjlab instead of BAM core. The
deployed default was unaffected. The core mode now uses BAM's two strict
direction comparisons and matches the pinned core at that edge case.

## Validation

All final commands exited 0:

```text
<official-microduck-python> scripts/generate_bam_golden_vectors.py --bam-repo <pinned-checkout>
.venv-apple/bin/python tests/test_bam_golden_vectors.py
.venv-apple/bin/python scripts/freeze_contract.py --check
BAM_REPO=<pinned-checkout> .venv-apple/bin/python tests/test_bam_formulas.py
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/test_bam_vs_mujoco.py
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
.venv-apple/bin/python -m compileall -q microduck scripts tests
git diff --check
```

Focused results:

- 29 golden vectors verified.
- Control-voltage maximum error: `1.776e-15`.
- Motor-torque maximum error: `2.220e-16`.
- BAM-core friction maximum error: `2.776e-17`.
- Deployed-mjlab friction maximum error: `0.000e+00`.
- Reset cleared selected prior torque and preserved battery voltage.
- Existing 2,000-case formula test remained bit-exact for voltage/torque and
  within `5.551e-17` for BAM-core friction.
- Documented deployed-mjlab versus core quadratic divergence remained 1.52%
  maximum relative error; it is preserved, not hidden.
- Closed-loop Genesis versus MuJoCo+BAM at 0.30 s: `0.19°` maximum joint error
  and `0.2 mm` height error; the 0.6 s test passed.
- Full BAM-enabled runner ended with `tous les tests passent`; no BAM comparison
  skipped. The default ONNX checkpoint remained non-applicable in this slice.
- Regeneration to a separate temporary file was byte-identical.

The official environment prints a non-fatal task-plugin circular-import warning
while importing `bam.mjlab`; the generator verifies the loaded BAM module path
is inside the exact pinned checkout before producing data.

## Evidence Boundary

This closes only authoritative open-loop/reset fixture production and Genesis
consumption. It does not close the M1 14-servo trajectory fixture, official
mjlab fixture consumer, full model reconciliation, task semantic files, or the
upstream/divergence decision. It grants no task-success or physical claim.

## Suggested Next Slice

Retain a deterministic 14-servo closed-loop trajectory fixture from the pinned
MuJoCo+BAM reference and make both Genesis and the official mjlab checkout
consume the same fixture before promoting cross-backend conformance.
