# V55 complete: stopping improves in the yaw arm; neither final is accepted

September 12, 2026. Both fixed 2,592,000-transition runs, both smokes,
57,600 paired conformance controls and all **11 evaluation banks** completed.
The doubled-yaw arm survives all four exposed downhill sessions, including
both newly added headings. It still fails yaw and final face pitch, and loses
one whole-composition heading gate. Keep original V21/V15 with V30 retained;
keep V54 shared as the prior development starting point. No policy is activated.

Protocol: [YAW-REFINEMENT-v55.md](YAW-REFINEMENT-v55.md).
Research: [YAW-RESEARCH-v55.md](YAW-RESEARCH-v55.md).

## Complete outcome

| Required evidence | V54 shared parent | V55 control, yaw weight 3 | V55 yaw weight 6 |
|---|---:|---:|---:|
| Original plus repeated flat cases | 63/63 | 63/63 | 63/63 |
| Full 180-second compositions, all gates | 2/2 | 2/2 | 1/2 |
| Original downhill sessions, all gates | 0/2 | 0/2 | 0/2 |
| Original downhill sessions, full-duration survival only | 2/2 | 1/2 | 2/2 |
| Newly exposed heading sessions, all gates | 0/2 | 0/2 | 0/2 |
| New heading sessions, full-duration survival only | 0/2 | 1/2 | 2/2 |
| Original passing surface sessions retained | 5/5 | 5/5 | 5/5 |
| All exposed surface sessions | 5/14 | 5/14 | 5/14 |
| Conditions with a complete 180-second training episode | 18/24 | 22/24 | 22/24 |

The parent column's new-heading results were collected in V55; other parent
results are the unchanged V54 receipts. Each downhill session contains two
continuous walk/stop windows. Four sessions and eight windows are not eight
independent trials. All new starts use the same +3-degree slope, nominal
mass/friction and 6-tick motor/1-tick sensor delay. They are exposed heading
interpolation checks, not unseen-terrain or physical generalization evidence.

The yaw6 composition start 1 completes all 180 seconds and its individual
windows, but its whole-session maximum heading error is **20.0981985 degrees**
against 20. Endpoint error is 10.1642691 degrees against 15. The failed maximum
is retained; a small miss is not a pass. Composition start 2 passes completely.

## Downhill behavior and first failures

V54 parent falls after the second stop at 32.40 and 32.12 seconds in the new
.04- and .08-radian heading sessions. This shows why surviving the familiar
two starts was insufficient evidence of robust stopping.

The V55 control regresses to first-stop falls at **14.14 seconds** on original
start 1 and **14.10 seconds** on the new .04-radian start. It completes the
original .12 and new .08 starts, but fails yaw and final face pitch. Its two
complete original windows have yaw errors .2192344 and .2168590 rad/s.
Its first original walking interval has post-hoc yaw error .2303096 rad/s;
that diagnostic does not fill missing full-case/stop evidence after the fall.

The yaw6 final survives all four complete downhill sessions and all eight
stops. Every one of its eight windows passes the other required gait, loaded
slip, motor/joint, posture-over-the-window, non-foot-support, penetration,
internal-load, settling and local/session-heading checks; **yaw tracking and
final standing face pitch still fail in every window**.

| Yaw6 session / window | Mean absolute yaw error (rad/s), limit .20 | Final standing face pitch (degrees), limit 30 |
|---|---:|---:|
| Original start 1 / 1 | .2262637 | 30.5276 |
| Original start 1 / 2 | .2309903 | 31.0277 |
| Original start 2 / 1 | .2200171 | 31.3967 |
| Original start 2 / 2 | .2154603 | 31.5803 |
| New heading .04 / 1 | .2225269 | 31.1658 |
| New heading .04 / 2 | .2227778 | 31.1742 |
| New heading .08 / 1 | .2175769 | 31.5840 |
| New heading .08 / 2 | .2197879 | 31.0677 |

Yaw6 improves each original window's yaw error relative to V54, but the
matched control also improves the walking intervals it reaches. On original
start 2, yaw6 is slightly worse in window 1 and slightly better in window 2
than the control. This single matched seed does not establish reliable yaw
superiority from doubling the penalty, and there is no overall accepted winner.

## Actual training exposure and verification

Both arms start from byte-identical V54 shared actor **and critic** tensors,
with unchanged initial exploration, frozen normalizers, old V21/V15 flat
teachers, original passing V54 replay examples, cold optimizers, fixed 3e-5
PPO rate and the same curriculum. Only the downhill walking yaw coefficient
differs. Physics, commands, action ABI, contact geometry and evaluator thresholds
are unchanged. The initialization/run details are in the frozen protocol.

| Training evidence | Control | Yaw6 |
|---|---:|---:|
| Main transitions | 2,592,000 | 2,592,000 |
| Main elapsed seconds | 3303.4222 | 3455.7996 |
| Short / medium / long complete episodes | 419 / 387 / 118 | 414 / 382 / 120 |
| Stochastic training falls | 209 | 270 |
| Falls after last switch to standing / walking | 188 / 21 | 270 / 0 |
| Final environments in short / medium / long stage | 0 / 3 / 45 | 1 / 3 / 44 |
| Conditions with long completion | 22/24 | 22/24 |

Both arms miss exactly `downhill-motor4-sensor1-yaw0.0` and
`downhill-motor6-sensor1-yaw0.12`. All 24 conditions record both transition
directions. The curriculum's completion criterion is survival, not independent
behavior quality. Fall mode is an association with the last observed command
switch, not attribution to a separate standing actor: the actor is shared.
The different realized experience is retained; equal curricula are not equal data.

The main runs total **5,184,000 transitions**; smokes add **5,760**. The final
checkpoints are iteration 2249 only. No intermediate checkpoint was selected,
and no budget was extended after inspection. Complete verification checks:

- All 5,184,000 stored training observation/action rows and reward components;
  independently reconstructed yaw-cost application and curriculum records.
- Exact parent initialization, finite final states, shared split components,
  preserved normalizers/teachers, and 58,436 finite logged scalar values.
- **201,838 byte-identical ONNX action rows** across both finals and the new
  parent baseline, with **807,352 physics-rate internal-load samples**.
- Source freezes, retained artifact manifests and the absence of surface-pass
  regressions. `next_stage_allowed` is **false**.
- 141 workspace tests and five focused V54/V55 tests pass.

The conformance probe compares 57,600 paired controls across both coefficients
and all 24 cells, including end-of-control physical states/constraint forces,
action/observation bytes, reward application and reset histories. It also
verifies the original V54 72-cell/layout conformance receipt. These checks
establish implementation consistency, not measurement-calibrated physics.

## Diagnosis and next experiment

**Next: a matched standing-posture objective ablation from the retained V54
shared development starting point, before another yaw-weight increase.**
Preregister a neutral-standing face-orientation cost with explicit headroom
below the unchanged 30-degree final-face gate. Apply that objective only to
zero-command standing, preserve the current yaw objective and all physics,
actor/critic inputs, retention data and curriculum in both arms. Keep the V55
yaw6 four-session survival result as an unaccepted comparison witness, not an
imitation-label source or replacement for V54's retained composition result.
Require all four complete downhill sessions, all 63 flat cases, both complete
compositions, the five retained surfaces and every original gate.

Why this next: all eight yaw6 final-standing windows fail the same directly
measured physical feature. In their last two seconds the reconstructed existing
head-joint reward cost averages only **.00805–.03070**, and the torso-tilt cost
is zero. The head cost is small, **not absent**: no audited sample simultaneously
has zero head/tilt cost and face pitch above 30. The existing reward penalizes
individual joint deviations; acceptance measures the combined world-space
face vector. This supports an objective-alignment hypothesis, not proof that
posture correction will fix stopping, yaw or coverage.

The post-hoc audit finds the same **3.2668-Hz** dominant frequency in body yaw
and action power in all eight walking windows; 9.60–9.81% of non-DC action
power lies above 8 Hz. This does not isolate the mechanism, rule out effects
of higher-frequency components, or justify a deployment filter. [CAPS](https://ai.bu.edu/caps/)
provides a possible separately tested regularizer if subsequent evidence points
to action sensitivity; normal periodic stepping must remain intact.

If the standing-posture trial fails through optimization/retention tradeoffs,
record per-mode/per-terrain advantages before choosing a critic or normalization
ablation. The [TorchRL MicroDuck tutorial](https://docs.pytorch.org/rl/main/tutorials/microduck.html)
describes per-task advantage standardization, but its different recurrent,
task-conditioned setup is not a drop-in solution or reproduced proof here.
If behavior passes but long exposure still fails, isolate the curriculum or
exploration issue in a subsequent experiment. Do not bundle these interventions.

Two further training seeds and broader terrain remain conditional on passing
the prerequisites. No protected bank was opened. Public research and the
unchanged native model do not supply Ducky-specific physical calibration;
carpet transfer, physical authority and arbitrary-terrain capability remain unproved.

## Retained artifacts

- `receipts/walking/20260912-v55-preregistration/`
- `receipts/walking/20260912-v55-conformance/`
- `receipts/walking/20260912-v55-{control,yaw6}-{flat,repeated,endurance,surfaces,fresh}/`
- `receipts/walking/20260912-v55-parent-fresh/`
- `receipts/walking/20260912-v55-verification/verification.json`
- `logs/yaw-native-20260912-v55-{control,yaw6}/`
- `outputs/walking-yaw-v55/analysis/analysis.json` and `yaw-and-stops.png`
- `outputs/walking-yaw-v55/objective-audit/audit.json`
- Recorded videos: `parent-new-heading.mp4`, `yaw6-new-heading.mp4`,
  `control-original-heading.mp4`, plus provenance and a viewed contact sheet.

Videos render retained generalized coordinates at 25 fps without new physics
integration or repaired actions. They label the whole session FAIL even where
stopping looks stable. The control's 14.14-second fall appears in a 14.16-second
encoded clip because 354 sampled display frames occupy complete frame periods.

Bulk evidence resides on the UUID-verified second external drive under
`CodexOffload/MicroDuck/20260912-yaw-v55`. Workspace external-symlink serving
remains unavailable; dedicated artifact verification above is separate.
No backup deletion, paid compute, hardware operation, policy activation,
publication or commit occurred in this activity.
