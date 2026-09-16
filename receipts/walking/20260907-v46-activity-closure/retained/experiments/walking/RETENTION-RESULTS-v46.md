# V46 restores retention; downhill acceptance remains unmet

The V45 component isolation and one bounded V46 correction are complete. V46
restores the behavior lost by V44, but adds no passing session over retained
V30. **Do not promote V46. Keep the original V21 walker / V15 stander with the
V30 controller.** Fresh sequence and protected terrain banks remain unrun.

## Independent acceptance

| Exposed bank | Retained V30 | Rejected V44 | V46 FINAL249 |
|---|---:|---:|---:|
| Original flat windows | 21/21 | 0/21 | 21/21 |
| Continuous repeated flat windows | 42/42 | 0/42 | 42/42 |
| 180-second compositions | 2/2 | 0/2 | 2/2 |
| Original downhill sessions | 0/2 | 0/2 | 0/2 |
| Public-prior surface sessions | 5/14 | 0/14 | 5/14 |

The four V46 evaluations completed and every required case was read. The
diagnostic bank passes 20/24 windows and 2/4 complete sessions; surfaces pass
12/28 windows and 5/14 sessions. Missing windows after termination remain
failures. The surface pass set is exactly unchanged: both rigid controls, both
soft-low-traction starts and `unseen-low-medium-start-1`. The historic “unseen”
case names belong to exposed development, not a newly held-out bank.

Both downhill sessions switch to standing at 13.16 s and fall at 13.84/13.78 s.
Applied 200-Hz internal loading exceeds 1 N continuously for .095/.065 s,
above the unchanged .05-s limit. Incomplete duration, heading and missing final
standing evidence also fail. Falling while standing does not alone identify
which actor produced an unrecoverable incoming state; loading may accompany
the fall rather than initiate it.

Both long compositions finish 180 s without resets and pass every original
window and whole-session gate. Heading endpoint errors are 7.80/5.87 degrees;
maxima are 19.13/14.29 degrees against unchanged 15/20-degree thresholds. The
first maximum is closer to its limit than V30's 15.88 degrees; this is not a
uniform numerical improvement. Neither long composition has internal load
above 1 N. The first nominal flat case has zero right-knee near-limit samples
in both V46 and V30; V44 had 192/605 walking samples in that band.

## What changed, and what was verified

[V45 component isolation](COMPONENT-RESULTS-v45.md) evaluated all four actor
pairs on the same six sessions and reproduced 27,703 original/joint control
action rows byte-for-byte with exact numeric poses. Replacing the walker
reproduces knee occupancy; replacing the stander causes long-composition falls.
Both mixed pairs survive the selected zero-delay window while joint V44 falls.
The V46 frozen protocol's first paragraph overstates that last result: the fall
is an interaction in this bank, not a reproduced walker-only fall. Frozen
protocol and source bytes remain intact, including inherited V44 wording in
some docstrings/error messages; actual V46 identities are checked in code.

V46 initializes from original V21/V15 and trains only walking. Standing and
the V21 teacher remain byte-identical, with frozen normalizers. PPO adds two
auxiliary action-retention losses: one against the original teacher on current
moving observations, and one against 38,451 original action/observation replay
rows from the 63 exposed passing flat windows. These are learning inputs, not
held-out evaluation. A continuous joint-margin cost replaces V44's binary cost.
Twelve balanced terrain/timing cells cover both flat sequence orders and
uphill/downhill with the three existing delay profiles. This combined correction
does not isolate the contribution of each training design choice.

The full run completes 360,000 transitions in 434.424 s after a 1,440-transition
smoke. Only the preregistered FINAL249 is evaluated. Native MuJoCo/BAM physics,
contact-v11, 61D observations, 14D raw actions, 50-Hz control, 200-Hz physics,
V16 command ramp and V30 heading controller remain fixed. Physical stepping and
scoring blocks match the earlier frozen evaluators; thresholds are unchanged.

Verification covers 56,398 paired conformance controls across twelve cells and
repeated non-accumulating resets; all 360,000 stored observation/action rows;
812 actual switch histories; exact actor component splits; frozen teacher and
standing tensors; 3,138 finite learning scalars; and all five V46 source freezes.
The main training freeze binds 197 files. Original replay teacher agreement is
within 1.431e-6 rad; maximum measured flat/repeated ONNX agreement is 1.669e-6 rad.
Switch histories include actuator/sensor state but are not complete MjData
restart snapshots. 139 workspace tests and two focused actor/reward tests pass.

During stochastic learning, the twelve cells complete 98 full 54-second cycles:
59 flat, nine downhill and 30 uphill. Downhill completions are six nominal-delay,
three zero-delay and zero longest-delay; 33 longest-delay downhill episodes fall.
These curriculum counts identify the weak bucket, not an acceptance rate or a
fair numerical comparison with V44's different training budget.

## Next step

Freeze one focused experiment on longest-delay downhill braking and the handoff
to standing. Use the complete incoming body, actuator, sensor and controller
history to locate the earliest divergence before selecting the actor or
transition property to change. Apply explicit retention to that correction,
then require all 63 flat gates, both long compositions, both downhill sessions
and no loss of the five passing surfaces. Do not repeat unrestricted joint
learning or expand the terrain curriculum while these known downhill gates fail.

No calibrated Ducky physics, carpet generalization, physical transfer, library
admission or policy activation is established. This activity used local
simulation only. All its compute jobs are finished. Disk space is below 1 GiB
at closure; restore headroom before another training run while preserving receipts.

## Retained evidence

- Protocol: `experiments/walking/RETENTION-CORRECTION-v46.md`.
- Control diagnosis: `receipts/walking/20260907-v45-analysis/analysis.json`.
- Run: `logs/retention-native-20260907-v46/run.json`.
- Joint FINAL SHA-256: `b71ec676ade54cc6a3a7cf738d53b9d9e1af9dce945765e22c1fe756ce9c8f9d`.
- Evaluated walker SHA-256: `c372aa08c4292769a54db683ecb4805794dffba52f3319035e36bf11538ddba0`.
- Evaluated original stander SHA-256: `acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46`.
- Evaluation receipts: `receipts/walking/20260907-v46-retention-{flat,repeated,endurance,surfaces}`.
- Verification and retained final/raw training: `receipts/walking/20260907-v46-retention-verification`.
- Comparison and knee/posture plot: `outputs/walking-retention-v46`.
- Final review, status snapshots and test logs: `receipts/walking/20260907-v46-activity-closure`.
