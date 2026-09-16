# V54 locomotion recipe comparison

September 9, 2026. **Both bounded runs, all eight evaluation banks and combined
verification are complete. Neither arm passes every prerequisite.** The shared
recipe is the stronger development starting point; the retained controller
remains original V21/V15 with V30. Broader terrain and adaptation stages remain
unexecuted because their prerequisites failed. This does not complete the wider
capability program.

## Frozen question and completed work

The [protocol](RECIPE-COMPARISON-v54.md) compares jointly trained routed actors
with one shared command-conditioned actor. Both use the complete-contact-v11
native MuJoCo/BAM model, 61 observations, 14 actions, raw 50-Hz control and
200-Hz physics. Initialization, parameter sharing and parameter counts differ:
this compares two learning recipes, without isolating architecture as a cause.

The routed actor MLPs have 395,548 parameters together; the shared MLP has
197,774. Both critics start with identical 196,097-parameter MLP tensors. The
original actor normalizers and teacher policies remain fixed during learning.

Completed preflight evidence:

- 83,700 original retained action examples; the original teachers reproduce
  the stored labels with maximum absolute error 0.000001431 rad.
- Shared initialization: exactly 20,000 supervised updates, 10,240,000 sample
  presentations, 68.02 seconds and no new RL transitions.
- All 72 cell/layout conformance reports pass, covering 448,640 paired control
  comparisons. Original downhill falls remain in this conformance evidence.
- Both 2,880-transition smokes complete. Their finite input/action streams and
  mode-switch records verify; these short smokes do not establish stopping.
- 141 workspace tests and three focused V54 tests pass. Source binding covers
  229 files. Tests are tooling/runtime evidence, not behavior admission.

Each main arm receives exactly 1,728,000 PPO transitions. The routed arm finished
in 2,000.64 seconds and the shared arm in 1,916.38 seconds. Only final iteration 1499 is
eligible. No paid compute, hardware action, policy activation or protected bank
is part of this comparison.

## Complete behavioral outcomes

| Frozen exposed test | Retained V30 | V54 routed | V54 shared |
|---|---:|---:|---:|
| Original and continuous repeated flat cases | 63/63 | 63/63 | 63/63 |
| Whole 180-second compositions | 2/2 | 1/2 | 2/2 |
| Whole downhill sessions, every gate | 0/2 | 0/2 | 0/2 |
| Whole exposed surface sessions | 5/14 | 5/14 | 5/14 |

The routed arm preserves exactly the five original surface passes. One downhill
start falls at 14.40 seconds. The other survives both stops over 36 seconds,
but fails yaw, final head posture and whole-session heading. Its two walking
windows have mean absolute yaw errors 0.234733 and 0.232287 rad/s, above 0.20.
Composition start 1 passes the complete 180 seconds; start 2 falls at 32.06
seconds, with a recorded penetration failure as well as incomplete evidence.

The shared arm retains both complete compositions and exactly the five original
surface passes. It survives both complete 36-second downhill sessions, including
four stops (two successive stops per session). All four downhill windows still
fail mean absolute yaw error: **0.241103, 0.244045, 0.224153 and 0.233787 rad/s**
against **0.20**. Start 2's first window also fails final standing face pitch:
**30.4054 degrees** against **30**. Both downhill whole-session heading gates
pass. Surviving and settling is a useful improvement; these are still failed
whole-task sessions. No new policy is activated.

The 14 surface sessions include rigid controls and exploratory numerical contact
profiles. This denominator is not 14 physically calibrated carpet types. Names
containing `unseen` are historical: these are exposed development cases now.
Repeated windows are not independent trials or a statistical reliability claim.

## Training coverage and stop diagnosis

The routed arm records 363 complete level-0 episodes, 313 level-1 episodes and
36 level-2 episodes. Long episodes complete in 18/24 cells. All six downhill
cells lack a complete long episode, so the frozen coverage prerequisite fails.
Training completion means surviving the scheduled horizon; it does not establish
the independent gait, slip, posture, joint, heading and contact gates.

The shared arm records 394/361/36 completions at levels 0/1/2 and 262 falls.
It also reaches complete long episodes in 18/24 cells, but with different gaps:
five downhill cells and the long-delay uphill/yaw-zero cell remain incomplete.
The zero-delay downhill/yaw-.12 cell completes two long episodes. All shared
environments reach at least level 1; the routed arm leaves eight at level 0.
The common curriculum rule produces different exposure, so these fall counts
are not a controlled causal estimate of architecture or physical reliability.

There are 1,038 stochastic training falls. Of 1,028 downhill falls, 1,027 occur
while the recorded actor mode is standing. At level 0 the median delay from the
last mode switch to a downhill fall is 0.76 seconds. Temporal association does
not establish that the standing actor caused the failure: the preceding walking
policy supplies its entry state and actuator history.

The deterministic downhill fall occurs 1.24 seconds after the switch to standing;
the composition fall occurs 0.92 seconds after that switch. This identifies
settling after movement as the immediate inspection target, without claiming a
causal physics or architecture diagnosis.

Shared initialization also exposes a replay imbalance. Only 93 of 83,700 rows
are first nonzero controls, and another 93 are first zero controls after movement.
Initialization RMS error is 0.200206 rad on the former and 0.101791 rad on the
latter, versus 0.011702 rad overall. The largest individual error is 1.173471 rad.
The final routed actor stays much closer to original replay actions overall
(0.004811 rad RMS) but still fails a continuous composition. Low imitation error
alone cannot certify closed-loop retention. Final shared RMS error is 0.011625
rad overall, 0.174889 at first nonzero controls and 0.116176 at first zero
controls. Its maximum replay error remains 1.084420 rad, yet it retains all
63 flat cases and both compositions. Requiring exact reproduction of every
discontinuous routed-teacher action is not justified as a behavior gate.

On the shared downhill walking intervals (2–13 seconds in each window), signed
mean yaw error ranges from -0.000176 to 0.006066 rad/s, while mean absolute error
is 0.224153–0.244045. A descriptive FFT peaks near 3.27 Hz in each window. The
observed failure is primarily oscillation, not persistent heading bias. This
does not identify which contact, actuator or gait mechanism causes it. The
post-hoc analysis preserves the original scores and thresholds.

## Verification and evidence boundaries

Early routed verification checks 1,728,000 stored actor input/action rows, 1,750
episode records and 7,798 handoff records. All 89,952 evaluated ONNX actions
reproduce byte-for-byte from actual observations, with 359,808 recorded physics
load samples. Combined final verification passes for both arms: **186,452 exact
ONNX action rows, 745,808 physics load samples, 3,456,000 main training input/action
rows and 38,940 finite logged scalars**. Initial cold critics are byte-identical;
parent normalizers and teachers remain unchanged. The verifier explicitly returns
`next_stage_allowed: false` because both behavior and coverage prerequisites fail.

Training reads actual internal loads at each physics tick for its reward and
validates four samples per control. It retains all actor inputs/actions, selected
reward components and handoff histories, rather than a complete physical trace
of every training step. Evaluated sessions retain the full required load telemetry.
Neither data export nor verifier completion changes a failed behavior result.

All new bulk evidence uses the UUID-checked external archive under
`/Volumes/cerebro-old/CodexOffload/MicroDuck/20260909-recipe-v54`.
The [storage receipt](../../docs/workspace/STORAGE-HEADROOM-20260909.md) records
the checksum-verified backup offload and measured internal headroom.
The workspace viewer deliberately refuses external symlinks. Its preparation
command now returns structured inspection errors instead of crashing; direct
V54 verification is separate from workspace serving.

No calibrated physical accuracy, carpet generalization or transfer is established.
The comparison does not change any historical score, physical model or threshold.

## Reassessment and recommended next activity

**Continue from V54 shared as a development baseline, with one bounded yaw-focused
refinement.** The immediate task has narrowed: preserve the demonstrated stopping
and continuous compositions while reducing downhill walking-rate oscillation.
Retain the face-pitch and coverage failures as separate open gates. A shared
controller can preserve the old behaviors and improve simulated stopping in this
pilot; that is stronger evidence for further work than a promise of all-terrain
walking or a general claim that shared networks always win.

1. Freeze a control-versus-intervention comparison from the same V54 shared
   checkpoint. Change one active property group: the downhill yaw objective.
   Preregister its exact coefficient, budget, seeds and final-selection rule;
   keep the current controller, actor inputs, native physics and all gates.
   Bind retention examples to validated flat, composition and surface behavior;
   any stop-only examples from a failed whole session need their own explicit
   component validation and must not imitate the failed walking segment.
2. Require 63/63 flat, 2/2 full compositions, all five retained surface sessions,
   both full downhill sessions with yaw <=0.20 and final face pitch <=30 degrees,
   and completed long episodes in all 24 training cells. Report survival,
   physical-quality gates and curriculum coverage separately. If yaw improves
   but face pitch still fails, address posture as the next isolated property.
3. Once an entire recipe passes, preregister two additional training seeds.
   Then expand the numerical terrain envelope in the existing staged strategy,
   preserving exposed development and protected final families. Adaptation,
   perception and additional behaviors remain conditional on measured need.

This follows the staged refinement and explicit command allocation illustrated
by the [pinned same-platform velocity recipe](https://github.com/pollen-robotics/microduck_rl/blob/2b581c641406a48346e696212930ea881c222c52/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py)
and the [HRP-5P compliant-terrain study](https://arxiv.org/html/2504.13619v1).
Their robot/model differences and physical evidence limits remain those in the
[feasibility review](../../docs/workspace/CAPABILITY_FEASIBILITY_RESEARCH.md).
The proposed yaw ablation is our inference from V54's measured failures, not a
published solution for Ducky.

A privileged-critic comparison remains a separate candidate if refinement stalls;
the upstream recipe supplies simulated base velocity to its critic. If delayed
downhill training still lacks successful entry states, a reference-state curriculum
is another scoped option. [DeepMimic](https://xbpeng.github.io/projects/DeepMimic/DeepMimic_2018.pdf)
supports testing that idea for some simulated skills, while its walking ablation
does not establish a benefit. It would require verified full simulator and BAM
histories, followed by ordinary-start complete evaluation. V54's successful
nominal downhill stops make this a fallback rather than the first intervention.

## Retained evidence and reproduction

- [Frozen protocol](RECIPE-COMPARISON-v54.md) and [upstream audit](UPSTREAM-RECIPE-AUDIT-v54.md).
- [Combined verification](../../receipts/walking/20260909-v54-verification/verification.json).
- [Routed endurance](../../receipts/walking/20260909-v54-routed-endurance/probe.json) and
  [shared endurance](../../receipts/walking/20260909-v54-shared-endurance/probe.json).
- [Replay and training-fall analysis](../../outputs/walking-recipe-v54/replay-analysis/analysis.json),
  [yaw diagnostic](../../outputs/walking-recipe-v54/shared-yaw-diagnostic.json) and
  [recorded stop telemetry](../../outputs/walking-recipe-v54/stop-plots/stop-telemetry.png).

From the repository root, the final evidence checks are
`.venv-apple/bin/python scripts/verify_recipe_v54.py`; that script intentionally
requires a new output directory and refuses to overwrite its completed receipt.
Use the retained verifier source and a separately versioned output for a later
reverification. Analysis commands are `scripts/analyze_recipe_replay_v54.py
--output <new-directory>` and `scripts/plot_recipe_stops_v54.py --root <repo>
--output <new-directory>`, using the Apple environment's Python. The eight
evaluator invocations use the frozen V54 scripts, `--recipe routed|shared`, a
new `--output`, `--fresh` for the exposed repeated flat bank, `--bank diagnostic`
for endurance and `--bank surface` for surface sessions. Guard and launch remain
one conditional operation. No historical receipt is overwritten.
