# Visual marker following: V3 development complete, advancement blocked

September 15, 2026. The unchanged V21 walker / V15 stander / V30 heading
controller now follows RGB-derived marker observations in several exposed
flat-floor conditions. The complete frozen development bank passes **11/16
required cases**, with both stationary negatives correctly rejected.
`next_stage_allowed` is false. No final bank, training, hardware operation,
policy activation or paid compute was used.

This task follows a **70 mm diameter artificial red marker centered 4 cm
above a nonreflective flat floor**. It is not real laser tracking, open-world
object recognition, obstacle perception or physically calibrated navigation.
Reflective floors remain outside this sensor fixture's envelope.

| Required condition | Complete / all gates pass | Result |
|---|---:|---|
| Straight target | 2/2 / 2/2 | 1.682–1.684 m forward; tracking 100%; final stop passes |
| Curved target | 2/2 / 2/2 | 1.691 m forward; maximum cross-track 15.1 cm |
| Combined timing / mass / friction / appearance / mirrored route | 2/2 / 0/2 | Marker clips at 1.6 s; only 6.33–6.37 cm progress and 2/1 foot swings |
| Target disappears 10–13 s | 2/2 / 1/2 | Both fault stops pass; start 0 fails yaw response |
| Camera dropout 10–13 s | 2/2 / 2/2 | Freshness stop, physical settling and resumption pass |
| Replayed stale camera frames 10–13 s | 2/2 / 2/2 | Stale timestamps cannot prolong motion |
| Rendered opaque occlusion 10–13 s | 2/2 / 1/2 | Both fault stops pass; start 0 fails yaw response |
| Two visible red markers 10–13 s | 2/2 / 1/2 | Both ambiguity stops pass; start 0 fails yaw response |
| Stationary negative controls | 2/2 / correctly rejected 2/2 | No useful translation, 0/0 foot swings, task/gait rejected |

All 18 complete their uninterrupted 30 s; none falls, contacts a corridor
obstacle, fails geometric self-contact or applied internal-load gates, or
fails the measured posture/joint/torque/final-stop checks. The missing gait
and target progress in the combined cases remain failures despite those
other checks. All ten fault cases produce zero commands throughout the
required fault interval and physically settle; worst measured late-fault
speed is 0.003413 m/s against 0.04.

The three start-0 reacquisition failures have mean yaw error
**0.2002463513 rad/s against 0.20**. It is a small but real frozen-gate failure.
Those runs reacquire at 14.8 s after clipping/out-of-envelope observations;
start 1 reacquires at 13.1 s. The three fault types yield byte-identical motor
actions/observations/qpos/qvel for each matched start. Drop and stale cases
likewise share realized motion. These are separate input-fault tests, not
independent physical reliability trials.

## Camera failures that preceded V3

V1's six-second smoke demanded red ≥100/255 and detected nothing. V2's
explicit low-light correction detected red pixels but exposed a scene error:
the high marker's **floor reflection** was often visible while the direct
marker was above the camera FOV. At 1 s, direct center (183,−29) is outside;
reflection center (190,117) matches the dark image. Detecting both correctly
causes ambiguity stops. Camera optical and CAD face axes agree throughout;
reversing the task would have been wrong.

V3 lowers only the rendered target and removes only visual floor reflectance.
The compiled-array audit compares 484 arrays by dtype, shape and bytes: only
`mat_reflectance` changes, .08→0. All other arrays, including collision and
actuation data, match. At the same 251 exposed prior poses, whole-marker
visibility improves 34→213 samples. This static diagnostic is not new behavior
evidence. Original V1/V2 source snapshots, scores and images remain retained.

The V3 six-second smoke has 50/50 active detections, 15/15 foot swings and
40.1 cm progress, but retains a short-window yaw failure. The next unchanged
30-second isolated straight run passes every gate. It is byte-identical in
actions/observations/qpos/qvel to bank straight-r0, so it is a duplicated
exposure rather than another independent success.

## Verification and artifacts

Fourteen focused tests pass. They cover the real V2 reflection ambiguity,
its explicitly unresolved single-reflection limitation, noisy low-light
pixels, large/central partial occlusions, stale/replayed frames and supported
physical-domain configuration. The bank anchor froze before any case; each
case matched before stepping and after completion.

Independent offline verification replays **5,340 original RGB frames** and
capture/receive timestamps through each receipt's frozen detector/follower.
All **27,000 float32 pixel-command rows** match exactly. It then runs fresh
CPU ONNX inference for all **27,000 stored 61D observations / 14D actions**;
every action byte matches. All **108,000 physics-rate load samples** are
present on the expected time axis, and **1,008 bank manifest files** verify.
No root position, target coordinate, depth or segmentation input enters the
pixel replay. All 18 materialized mass/inertia/friction arrays match immutable
nominal values times their declared factors; seven duplicate-motion pairs
are explicitly checked. Supporting smoke/fixture manifests also verify.

- Bank: `receipts/visual-follow/20260915-v3-development/bank.json`.
- Offline verification: `outputs/visual-follow-20260915/development-verification.json`.
- Compiled physics/optics proof: `receipts/visual-follow/20260915-v3-fixture-audit-r2/audit.json`.
- Domain and duplicate checks: `outputs/visual-follow-20260915/analysis-r2/analysis.json`.
- Three complete original-rate simulated camera videos and contact sheet:
  `outputs/visual-follow-20260915/analysis-r2/` (straight pass, combined failure,
  and target-loss start-0 failure). These replay recorded RGB without physics
  integration, generated frames, interpolation or motion edits.

## Next bounded experiment

Do not broaden terrain or call this capability accepted yet. Isolate the
combined case's first camera clipping at 1.6 s by restoring one active
property group at a time, and separately inspect camera/face pose during
stop→reacquire. Keep physics, motor outputs, camera alignment and thresholds
fixed; do not rescue this result by weakening circularity or yaw gates.
The priority is maintaining a usable sensor view through actual locomotion
and stopping, then rerunning every retained case with a fresh candidate freeze.

The unopened fresh offset-bay case also specifies unsupported mass ×1.05 /
friction 0.8. Preflight now rejects it before model execution. It needs a
separately versioned supported-factor amendment before that fresh bank can be
opened; the current developmental failures already block it. New layout
generalization, long endurance, partial-occlusion families, camera calibration
uncertainty, cross-engine diagnostics and physical calibration remain required
uncompleted gates. No broad carpet, navigation or real-world readiness claim
follows from the bounded passes above.
