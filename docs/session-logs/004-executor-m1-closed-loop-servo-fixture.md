# Executor Session Log 004 - M1 closed-loop 14-servo fixture

**Date:** 2026-09-01

## Slice

Executed `docs/briefs/004-m1-closed-loop-servo-fixture.md` against the clean
Rhoban/BAM checkout at the exact revision pinned by the official Microduck RL
lock: `62bd8ce12154340be97e06f7f41a0ca8f116d967`.

## Files Changed

- `microduck_contract/README.md`
- `microduck_contract/actuator/bam-m6-xl330-v1.lock.json`
- `microduck_contract/actuator/fixtures/bam-m6-xl330-v1-closed-loop.json`
- `scripts/freeze_contract.py`
- `scripts/generate_bam_closed_loop_fixture.py`
- `tests/run_all.py`
- `tests/test_bam_closed_loop_fixture.py`
- `docs/session-logs/004-executor-m1-closed-loop-servo-fixture.md`

## Implementation

- Added a deterministic official-MuJoCo generator for 120 physics steps at
  5 ms with all 14 canonical joints, the HOME target, fixed 7.35 V, no domain
  randomization, and no command delay.
- The generator refuses a dirty or wrong-revision BAM checkout and cross-checks
  its commit, tree, BAM model digest, and servo-parameter digest against the
  already approved open-loop authority fixture before producing output.
- Retained every-step joint positions and base height, initial conditions,
  source/model/parameter provenance, profile ID, and explicit tolerances.
- Added a Genesis BAM-core consumer that reports each joint's worst error and
  exact step. A failure records the offending joint or base-height time rather
  than reducing the result to one final scalar.
- Bound the fixture digest and schema from the generated actuator lock and
  wired the consumer into `tests/run_all.py`.

## Validation

All final commands exited 0:

```text
.venv-apple/bin/python scripts/generate_bam_closed_loop_fixture.py --bam-repo <pinned-checkout>
.venv-apple/bin/python scripts/freeze_contract.py
.venv-apple/bin/python tests/test_bam_closed_loop_fixture.py
.venv-apple/bin/python scripts/freeze_contract.py --check
.venv-apple/bin/python -m py_compile scripts/generate_bam_closed_loop_fixture.py tests/test_bam_closed_loop_fixture.py scripts/freeze_contract.py
<regenerate-to-temp-and-cmp-with-retained-fixture>
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
git diff --check
```

Focused results:

- Regeneration was byte-identical to the retained fixture.
- Fixture SHA-256: `0632c794f5128a76a8a86cc2137712365c901c4524a7445ad292731968c71d5d`.
- Worst joint deviation over all 120 steps: `0.410 deg` (`left_knee`, step 120).
- Worst joint deviation at step 60: `0.184 deg`.
- Worst base-height deviation over all steps: `1.811 mm`.
- Base-height deviation at step 60: `0.237 mm`.
- The BAM-enabled full runner ended with `tous les tests passent`; no BAM
  comparison skipped. The absent trained ONNX checkpoint remained explicitly
  non-applicable.
- Existing golden-vector precision remained at `1.776e-15` for voltage,
  `2.220e-16` for motor torque, `2.776e-17` for BAM-core friction, and exact
  for deployed-mjlab friction.

## Reachability

`tests/run_all.py` now consumes the retained closed-loop fixture by default.
The generated actuator lock fails its check if the fixture changes without a
corresponding lock update.

## Evidence Boundary

This establishes a narrow deterministic standing trajectory from pinned
official MuJoCo plus BAM core and thresholded Genesis BAM-core consumption. It
does not establish official mjlab fixture consumption, full model parity,
walking, backflip, task success, held-out evaluation, or physical authority.

## Suggested Next Slice

Make the official pinned mjlab/MuJoCo Warp adapter consume the approved
open-loop and closed-loop fixtures under its explicit `mjlab-deployed-v1`
profile. Preserve its documented quadratic-gate divergence instead of
silently treating BAM core and deployed mjlab as identical.
