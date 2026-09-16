# Laser locomotion: systemic failure and correction

This supersedes walking-quality implications in the earlier L1/L2 delivery.
Historical target-only receipts remain unchanged. Current status: the bounded
gait-v4 intervention and evaluation are complete, with a **terminal negative**.
Joint-stop parking was eliminated in the four visible cases, but credible
walking was not learned. Neither policy has walking or transfer acceptance.

## What went wrong

The laser objective and evaluator measured the consequence (reaching the dot),
not the locomotion used to get there. The v2 correction emphasized yaw reward
12 plus yaw-progress reward 4 while reducing pose weight to .2 and action-rate
weight to -.01. The inherited actual-limit penalty and foot-slip penalty were
small relative to that objective. No evaluator gate inspected actual joint-stop
occupancy, bilateral foot lifts, or loaded contact slip. More randomization
then optimized the same incomplete objective; it did not repair its meaning.

I treated improved endpoint scores and upright videos as enough development
evidence, despite the repository's explicit warning that neither proves a gait.
The adaptive wide camera and small robot image made the missed checks less
obvious. The missing safeguard was a physical-behavior acceptance contract,
not an additional reviewer/executor cycle or more training compute.

The repository already had canonical walking slip and joint/torque-margin
criteria in `evaluator/success.py`; the laser experiment bypassed that physical
behavior reasoning through a separate proximity-only classifier. Those frozen
canonical batteries remain separate and unclosed. The new laser evaluator
removes the endpoint-only promotion path by requiring its own measured gait
gate too; it does not pretend the full canonical battery has been run.

## Measured failure in the selected policy

Exact policy `7d634c6f64178f1bbb8cbe3a4129418ad8661dad6abfbaae3ac533244c3d0fed`,
16-second nominal circle, unchanged C MuJoCo/BAM rollout:

| Measurement | Observed |
|---|---:|
| Traveled path | 1.351 m |
| Qualifying swings: left / right | 1 / 0 |
| Both hip-yaw joints within outer 5% of range after startup | 100% of samples |
| Loaded foot-contact samples slipping faster than 3 cm/s | 22.76% |
| 95th-percentile loaded contact slip | 10.05 cm/s |
| Maximum actual joint-limit overshoot | 0.089 rad |
| Maximum body tilt | 2.53 degrees |
| Backward translation relative to PHYSICAL head site | 0% |

Qualified swing means unloaded for at least 60 ms, sole-mesh clearance at
least 5 mm, followed by loaded landing. These are visible-development rejection
thresholds, not experimentally calibrated hardware tolerances. The 50 Hz probe
cannot resolve every substep contact. It computes on copied data and does not
change simulator or policy state. All 800 original action/command/position
samples match the previously retained circle values; tests also compare actual
float32 action bytes and state bytes with/without instrumentation.

Receipt: `receipts/laser-gait/20260905-turn-physical-face-audit-v3/`.
The earlier audit-v1/v2 backward-facing labels are invalid; retain them only as
the evidence of the rejected camera-axis assumption.

The final frozen four-case baseline is even clearer: **4/4 target passes,
0/4 gait passes, 0/4 composite passes**. Bilateral-step coverage during movement
ranges from 0 to 20.4%; every case parks actual joints at their stops. See
`receipts/laser-gait/20260905-turn-composite-baseline/`.

Two Genesis diagnostics separate policy pathology from renderer appearance:
an 8-second feedback run has no root-below-7-cm event, but both hip-yaw joints
still occupy the outer 5% of their ranges throughout post-startup samples.
A separate exact-float32-action replay falls below 7 cm at 0.72 s; the replay
is no longer closed-loop after engine states diverge, so that fall is not a
feedback-policy failure or a calibrated simulator-gap measurement. Both full
traces are retained under `20260905-genesis-feedback-diagnostic/` and
`20260905-genesis-exact-action-replay/` respectively.

## A second model bug, and a rejected diagnosis

The first audit used the rendered camera's optical axis as "face forward."
That was wrong. The mouth lies 45 mm in front of the head COM along +X, and
the CAD `head_camera` SITE +X agrees. The legacy CAMERA's optical axis is -X,
pointing into the head; its image-up is world +Y rather than +Z at HOME.

That mistake led to a v3 opposite-axis smoke and an interrupted longer run.
The run was quarantined, not selected or silently repurposed: final retained
stdout shows 1,695,744 completed transitions, plus an unknown partial iteration,
out of a planned 14,745,600. Genesis did not stop on the initial graceful signals;
the exact owned process was killed and exit137 verified. Original metadata,
checkpoints and exact source snapshots are retained. The active v4 trainer now
installs explicit stop handlers after Genesis initialization.

The correct model intervention is **render-camera-only v2**, not reversing the
robot, swapping joints, or rotating visual meshes. `camera_alignment.py` maps
camera local -Z to the physical site's +X and camera image-up +Y to site +Z.
Local camera quaternion changes from `[0,0,-1,0]` to approximately
`[.7071,0,0,-.7071]`; physical geometry, inertia, collisions, sensors, servo
targets and dynamics stay fixed. An 85 cm ground target becomes visible with
upright pixels. A retained 65 cm probe is clipped at the unchanged FOV boundary:
close-range camera tracking still requires an explicit perception/head-control
task. This is not a calibrated or camera-driven policy.
This camera defect cannot explain the current gait: the laser actor receives
ground-truth-derived commands, not camera pixels. It is a separate perceptual
model misalignment that the audit exposed and corrected.

Camera receipt: `receipts/laser-gait/20260905-camera-alignment-v2-r2/`.
The coordinate mapping follows [MuJoCo's camera convention](https://mujoco.readthedocs.io/en/stable/modeling.html#cameras).

## Corrective lane

`gait-correction-v4.json` freezes a bounded local intervention from the early
first-party walking checkpoint, before the hip-stop laser lineage. It keeps
canonical +X target steering and the existing physical model/BAM/61D→14D ABI.

- Price actual position near mechanical stops and terminate sustained parking.
- Restore action smoothness and meaningful loaded-foot slip cost.
- Require recent qualifying landings from BOTH feet for full translation
  credit; reduce free reward for standing under a nonzero velocity command.
- Evaluate target success AND independent gait rejection, including no-op,
  skating, one-foot hopping, backward traversal, and mechanical-stop negatives.
- Display fixed-scale feet, a fixed-world overview, physical-facing direction,
  foot loads/clearance/slip and joint-stop telemetry; never label proximity alone
  "walking success."

Do not clip command references to mechanical limits as a cosmetic fix. A BAM
position target may exceed the mechanical angle to produce torque under load.
Actual hard-stop occupation is the relevant failure here. Tests explicitly
allow legitimate reference overshoot without actual limit parking.

The camera correction and instrumented observer have unchanged-action/state
tests. Existing frozen core/model/training source files are not modified. The
walking model still lacks body-to-floor contacts, and contact compliance,
backlash, latency, electrical/thermal duty and physical gait envelope still need
separate evidence before any real-robot trial. No paid compute or hardware used.

## Exit rule

Run exactly one bounded v4 experiment, select its final checkpoint only, and
retain all failing cases. The fresh reserved bank stays closed unless all four
visible target AND gait cases pass. A better policy is not automatically a
transfer-ready policy. Update this document and the existing queue with the
actual final result, including a terminal negative if it fails.

## Final bounded result: reject both policies

The local 1,024-environment, 600-iteration v4 run completed 14,745,600 new
transitions in 1,940.55 seconds. Only its declared final checkpoint,
`model_599.pt`, was exported. The independent C MuJoCo/BAM evaluation used the
same frozen four-case composite evaluator as the old laser baseline.

| Frozen visible-development measure | Previous laser policy | Gait-v4 final |
|---|---:|---:|
| Target-only cases passed | 4/4 | 1/4 |
| Gait cases passed | 0/4 | 0/4 |
| Combined cases passed | 0/4 | 0/4 |
| Worst actual joint-stop occupancy across cases | 100% | 0% |
| Sustained bilateral-step gate | Failed all cases | Failed all cases |

The new checkpoint has **zero qualifying swings on either foot in all four
cases**. It removed stop parking but mostly substituted standing or shuffling;
target acquisition also regressed. The circle's loaded-slip p95 remains
9.14 cm/s, so passing the slip-fraction threshold is not absence of slip.
No falls occurred in these cases, which still does not make the gait acceptable.
Fixed-scale rendered footage agrees with the contact/clearance measurements.

Final policy SHA-256:
`6190f954425c2b31c3b301faa5dcfed613d5c9c867b9d00ce71abc722b3df308`.
Evidence: `receipts/laser-gait/20260905-v4-evaluation/` and the package's
`comparison.json`. Real-observation Torch/ONNX maximum difference is
1.3113e-6 rad. The full repository test run and 14 focused gait tests passed;
the full run preceded the last two additional focused regression tests.
Those software checks validate instrumentation/export, not walking success.

The fresh reserved bank remains unopened. No candidate was promoted, no
hardware or paid compute was used, and no training job remains active.
The local playground retains the old policy only as an explicitly unvalidated
diagnostic, with constant-scale feet and contact/stop telemetry.

## Next priority: establish locomotion before pursuit

1. Freeze a nominal command-conditioned walk/turn/stop development battery,
   including sustained bilateral stepping, actual joint/torque margins, loaded
   slip, useful velocity tracking and settling. Reuse canonical criteria where
   applicable; do not relax this failed evaluator to qualify the checkpoint.
2. Diagnose the training-to-evaluator gap in foot clearance/contact rewards and
   actual base/joint/contact dynamics using fresh closed-loop traces in both
   engines. Audit the missing body-floor contacts and inertia/contact handling
   before changing the physical model; fixed-action replay and feedback are
   different experiments. Only evidence-backed changes get a versioned lane.
3. Learn and accept basic locomotion in that bounded lane first. Then compose
   laser pursuit and domain randomization on top, rerunning the composite
   acceptance checks. Add camera-driven perception separately.

This closes the diagnosis and one corrective experiment, **not** the walking
milestone. It changes the definition of accepted behavior and the next task
order; it does not justify another unbounded training or reviewer/executor loop.
