# V44 full-sequence experiment: completed and rejected

September 7, 2026. Keep the original V21 walker, V15 stander and V30 controller.
Joint sequence learning completed, but its final candidate regressed on every
required test bank. No policy was promoted or activated. Fresh sequence and
protected terrain evaluations remain unrun; physical calibration remains unmet.

## Independent results

| Required bank | Retained V30 | V44 FINAL499 |
|---|---:|---:|
| Original flat windows | 21/21 | **0/21** |
| Exposed repeated flat windows | 42/42 | **0/42** |
| Downhill sessions | 0/2 | **0/2** |
| Continuous 180-second compositions | 2/2 | **0/2** |
| Exposed surface sessions | 5/14 | **0/14** |

All four evaluation processes completed, with source hashes and artifact
manifests verified. That is execution completion, not acceptance. The diagnostic
bank has 1/24 passing windows; surface evaluation has 0/28. Original flat cases
contain nine actual falls. Repeated flat evaluation contains ten actual fall
windows plus ten explicitly unrun windows. Diagnostic and surface evaluations
contain 17 and 10 explicitly unrun windows respectively. Later windows are not
reset, omitted, or counted as passes.

Downhill falls occur at 13.96 and 13.76 seconds. The two intended 180-second
compositions fall at 67.98 and 14.06 seconds. All five previously passing surface
sessions regress: both rigid controls, both soft/low-traction starts and the
first previously exposed low/medium start. Existing surface IDs containing
`unseen` are historical names; this is exposed regression, not new held-out proof.

## What was trained and verified

- One smoke: 8 environments x 5 iterations x 24 steps = 960 transitions.
- One full run: 64 x 500 x 24 = **768,000 transitions**, 913.809 seconds.
- Fixed seed 26090744, final checkpoint 499 only. No checkpoint selection or extension.
- Both original actor means and normalizers initialized from V21/V15. Two MLPs
  learn together, routed by exact-zero raw command; normalization remains fixed.
- Continuous 54-second episodes contain three walk–brake–stand windows and
  restarts. Equal template assignments cover two flat command orders and +/-3°
  straight slopes. Reset only on terminal fall or completed episode.
- Native MuJoCo, contact-v11, original BAM, 200-Hz physics, 50-Hz unfiltered
  actions, 61 observations/14 actions, six-tick motor and one-tick sensor delays.
  No physical parameters, collision masks, solver settings or heading/ramp
  controllers were changed.

The conformance probe matched **17,582 paired controls** with actual observation
and action bytes, complete physical continuation and non-accumulating HOME
resets. It reproduced the original downhill fall. The sequence adapter checks
its predicted input against the actual deployment input at every training step,
and records four applied internal-load samples per control step.

Stored evidence contains all **768,000 finite observations and actions**, with
raw byte hashes and exact lengths, plus **2,230 policy-switch histories** including
motor FIFO, BAM previous torque/target, sensor history, joint state and friction.
These histories are diagnostic coverage, not complete MjData snapshots. Every
component tensor equals the corresponding joint-final tensor; both actors changed
and both parent normalizers remain byte-identical. All **5,888 logged scalar
samples** are finite. These checks verify learning/evidence integrity, not quality.

| Training bucket | Completed 54-s episodes | Stochastic falls | Walk→stand / stand→walk switches |
|---|---:|---:|---:|
| Flat order A | 31 | 69 | 222 / 235 |
| Flat order B | 26 | 81 | 225 / 238 |
| Downhill | **0** | 527 | 244 / 546 |
| Uphill | 48 | 131 | 207 / 313 |

Downhill reaches both actor switches but only 94 control samples in the defined
restart phase after a full first window. A curriculum recipe did not produce
complete downhill sequences. These stochastic training counts are not independent
acceptance trials or comparable to deterministic evaluation fall counts.

## Specific regression to investigate

The first original case, nominal-delay forward 0.08 m/s, finishes but fails the
unchanged joint-stop occupancy gate. V44's right knee enters the band within 5%
of its joint range for **31.74% of walking-phase controls**, versus **0%** for V30.
Neither pair enters that band while its standing actor is selected in this case.
Whole scored-window occupancy is 22.56%, above the unchanged 20% gate.

![Recorded right-knee margin and stopping tilt](/Users/kelly/Developer/microduck-rl-genesis/outputs/walking-sequence-v44/knee-and-stop.png)

The plot uses the first failing case, not a selected successful rollout. The gray
region begins at the requested STOP. Stopping tilt improves in this case, while
walking joint margins regress. The association with the walking phase does not
isolate the walker from the incoming state supplied by the stander.

The training penalty uses an absolute .04-radian joint margin; acceptance also
checks time spent within 5% of each joint's range. Those criteria are different.
This is a concrete objective gap to consider after component isolation, not a
reason to loosen the evaluator. The run also trained only the longest existing
motor-delay profile; timing-profile retention needs explicit checking.

[Recorded rejected composition](/Users/kelly/Developer/microduck-rl-genesis/outputs/walking-sequence-v44/rejected-composition.mp4)
contains 703 actual retained controls, rendered as 352 frames at 25 fps. It shows
the second composition failing after STOP at 14.06 seconds. Rendering replays
stored poses; it performs no policy rollout, repairs or new physics evaluation.

## Review and source preservation

Before any candidate evaluation, review found that the first copied surface
adapter still selected the original walker. It was superseded without execution
by `evaluate_native_sequence_surfaces_v44_r2.py`, which checks and evaluates the
joint candidate walker and stander. The r2 flat adapter also corrects a descriptive
V21 label. Original adapters/freezes remain retained. Syntax-tree comparison
confirms the physics/scoring blocks are unchanged from V42, aside from rendered
version labels. All seven source freezes match; training sources remain frozen.

The workspace recognizes the new paired receipt and compute entrypoints, with
standing-identity and failed-load checks preserved. **139 workspace tests and two
focused actor/routing tests pass.** No full simulation suite overlapped training.
All local compute from this activity has completed.

Joint FINAL SHA256:
`0ea6960d5489520704ed39152e946fde1564822c0e9d55eaa932ed7892ff2b99`.
Walker component:
`26640a2b16cabeda12adda00a801cea68a94148461823b4d5cf2234d34c80ff2`.
Stander component:
`df31abb7906173689291e0a05482e0fb5cdd83e1a8a0d6ce8d852695ddad8429`.

## Next best step

Freeze a small component-isolation bank on these exposed failures: compare the
V44 walker with original V15 standing, and original V21 walking with V44 standing,
against both original and joint pairs. Use the first knee-occupancy failure,
a short-delay fall, downhill STOP and a long composition without state resets.
Keep the same dynamics, observations and composite gates. This will distinguish
a walker regression, a stander regression and their interaction.

Only then define one retention-constrained correction for the responsible
component, with baseline rehearsal across timing profiles and an objective that
addresses sustained normalized joint-margin occupancy. Do not broaden terrains
or repeat unrestricted joint training yet. The current results do not establish
that sequence training in general cannot work; this particular bounded run fails.

## Receipts and reproducibility

Protocol: `experiments/walking/NATIVE-SEQUENCE-v44.md`. Full raw training and
per-file evidence verification: `receipts/walking/20260907-v44-sequence-verification`.
Closed-loop conformance: `receipts/walking/20260907-v44-sequence-conformance`.
Evaluator review: `receipts/walking/20260907-v44-gate-review`.
Comparisons and plot inputs: `outputs/walking-sequence-v44/comparison.json` and
`plot-data.json`. Evaluation receipts share the prefix
`receipts/walking/20260907-v44-sequence-` with suffixes `flat`, `repeated`,
`endurance`, `surfaces`. Training run: `logs/sequence-native-20260907-v44`.

Reproduce only in fresh output directories after checking the frozen sources and
conditional compute guard. The used entrypoints are the r2 flat/surface adapters,
`evaluate_native_sequence_endurance_v44.py`, `probe_native_sequence_v44.py`,
`train_native_sequence_v44.py`, `analyze_native_sequence_v44.py` and
`verify_native_sequence_v44.py`. No paid compute, hardware, public publication,
policy activation or behavior-library admission occurred.
