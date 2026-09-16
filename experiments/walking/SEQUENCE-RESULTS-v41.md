# Contact, stopping and terrain continuation — September 6

This bounded sequence is complete through its failed prerequisite gates. The
V30 motor pair/controller remains the retained baseline; V38, V41 and V42 are
rejected. Fresh terrain expansion was not opened. Physical calibration remains
unmet; all work here is local simulated development.

## Matched-support diagnosis

All eight probes preserve 211 float32 action vectors and 844 physics steps per
lane, covering five original initial-standing prefixes. Native-plane controls
reproduce within 1e-10 qpos, and V31's added observer reproduces original Genesis
within 1e-7. The unchanged diagnostic limits are 2 mm base position and 5° joint
discrepancy at the original 50-Hz observations. These are short numerical probes,
not closed-loop walking or calibrated-material tests.

| Probe | Changed property | Matched-box cases passing |
|---|---|---:|
| V31 | Native ground plane replaced by the same four boxes | 0/5 |
| V32 | Genesis GJK/contact patches on original simplified hulls | 2/5 |
| V34 | Retain authored collision hulls, original MPR | 2/5 |
| V35 | GJK/contact patches on authored hulls | 0/5 |
| V36 | Disable contact pruning on V35 | 0/5 |
| V37 | Genesis numerical compatibility mode on V36 | 0/5 |
| V39 | Euler integration on V34 | 2/5 |
| V40 | Native legacy MPR on V34, original plane control unchanged | 0/5 |

V33 audited all 11 actual robot colliders using 2,054 support directions at the
same HOME pose. Original sole differences reach 0.354/0.289 mm, and the largest
body difference is 0.654 mm. Disabling collision-mesh decimation reduces the
maximum sampled difference to 2.194e-8 m; runtime body masses still match.
This corrects a representation mismatch, but does not close soft-contact
agreement. The original V30 scores remain bound to their original lanes.

V36 produces the same Genesis poses as V35. V40 produces the same Genesis poses
as V34: its only changed dynamics are in the explicitly labeled native-box lane.
No stiffness, gravity, motor target, action correction or acceptance limit was
fitted to improve these comparisons. All raw 200-Hz contacts, torques, targets
and poses are retained in compressed receipts.

The installed Genesis mesh loader documents collision decimation; its runtime
mesh audit, rather than the model filename, establishes the observed discrepancy.
MuJoCo documents its different convex detectors and multiple-contact methods:
https://mujoco.readthedocs.io/en/latest/computation.html

## Stopping intervention

V38 changes only translational command deceleration during exact STOP to
0.25 m/s². Both downhill sessions reach 36 seconds without falling, but fail
yaw tracking and final head posture. Both long compositions develop falls;
overall 0/4 sessions pass. Reject this candidate and keep V30's command ramp.
Its three command arithmetic/state tests pass; tests do not override failed
behavior evidence. Broader V38 evaluation is not justified by this regression.

## Focused native learning

V41 trains only the standing actor in native MuJoCo/BAM from original V15 FINAL,
with the original V21 walker and V30 controller reserved for evaluation. The
eight-template handoff bank retains full native dynamics, BAM and delay states;
every template passes exact reset continuation. The downhill source action
prefix is byte-identical to the original V30 evaluation.

Both native refinements completed their fixed 64×250 budgets: **384,000
transitions each**, in 333.161 s (V41) and 301.575 s (V42). Each had a separate
960-transition smoke. Both began from original V15 FINAL; only the actor and
normalizer were warm-started. The critic and optimizer were reinitialized.
V42 changed the stationary-posture/yaw objective; it kept V41's seed, physics,
eight handoff templates, reset mixture, learning rate and budget. Every template
and source-action hash matches across the two runs and their smokes. Both full
runs visited HOME and handoff starts for all eight templates. Ground-contact
counts record contacts, not force-qualified support coverage.

| Candidate | Original + repeated flat | Downhill sessions | 180-s compositions | Exposed surfaces |
|---|---:|---:|---:|---:|
| Retained V30 | 63/63 | 0/2 | 2/2 | 5/14 sessions, 12/28 windows |
| V38 slower STOP | Not run | 0/2 | 0/2 | Not run |
| V41 native standing | Not run | 0/2 | 0/2 | Not run |
| V42 posture revision | 63/63 | 0/2 | 1/2 | 3/14 sessions, 11/28 windows |

V41 fails all 24 diagnostic windows: downhill falls near 3.1 seconds; both
complete long compositions violate standing posture. V42 passes 17/24 windows
and restores all 63 flat gates, including independent heading, bilateral gait,
posture, joint/torque, body interference and applied internal-load checks.
However, its first composition falls at **140.16 seconds** during standing;
only the second composition completes and passes. Its downhill sessions fall
at **20.52 and 4.12 seconds**. Exposed surfaces have three falls and regress in
complete-session acceptance from 5/14 to 3/14. The surface cases named “unseen”
are already exposed V25 development cases; this evaluation creates no new
held-out evidence. All incomplete and unrun windows remain failures.

These results reject V42 despite its complete flat regression. The V21 walker,
V15 stander and V30 controller remain the retained baseline. V42's final SHA is
`f9390d939d0a8e96bb6cfa5ef9c5e2455ab135e1139337828d3e700072c7589e`;
V41's is `caf6340620976d54b8a7be98930a25099cf6940292dee735039a6affa36c28f8`.
No intermediate candidate was selected. Both full actors and every logged
training scalar are finite. Finiteness and completed computation are not
behavior acceptance.

Next investigate **handoff-state coverage under the candidate's own preceding
behavior**. The training bank starts from V30-generated HOME/handoff states and
uses isolated three-second episodes. Evaluation also includes initial standing,
walking after the new standing actor, and repeated continuous windows. This is
a concrete distribution-gap hypothesis, not an established cause. Before more
learning, quantify state and delay-history coverage at the first failed handoff;
then freeze one bounded intervention that preserves the passed flat gates.

## Expansion decision

Require every 21+42 flat gate and both long compositions, with improved targeted
stopping, before evaluating a fresh environment bank. Failed/missing gates keep
that bank unopened. The existing soft-contact discrepancy separately blocks
broad Genesis terrain training and physical carpet claims.

## Receipts and verification

- Contact probes: `receipts/walking/20260906-v31-matched-contact` and individually
  named V32/V33/V34/V35/V36/V37/V39/V40 folders; all 15 resulting diagnostic and
  behavior receipt manifests were rechecked.
- Rejected behavior receipts: `20260906-v38-stopping-endurance`,
  `20260906-v41-native-standing-endurance` and the four
  `20260906-v42-native-standing-{endurance,flat,repeated,surfaces}` folders under
  `receipts/walking/`.
- Permanent training finals, source snapshots, event logs, prefix action arrays,
  template state arrays/reconstruction prefixes and all 19 source freezes are
  retained under
  `receipts/walking/20260906-v42-sequence-verification`. The verifier rereads raw
  physics traces, checks target application, exact action hashes and unchanged
  lane comparisons. It also checks full training accounting and every logged
  scalar. Complete reset state (including BAM and sensor/delay histories) was
  tested in memory. Saved NPZ files contain diagnostic state arrays; reconstruct
  complete state through the frozen prefix code/actions, not NPZ alone.
  A first verifier attempt incorrectly required both reset types in
  the short smoke; that error is retained and the full-run requirement remains.
- Workspace verification: **135/135**. V38/V30 focused arithmetic tests: **5/5**.
  `duck prepare` binds V42's passing flat reference, explicitly labeled as a
  rejected candidate overall. V30 is retained separately; a direct active-packet
  comparison was refused because the flat receipts omit the explicit matching
  domain draws required by that preparation path.
- Compressed traces now work in workspace inspection and preparation, with
  decoded byte/line limits and SHA-256 identity of the stored compressed bytes.
  Native paired-policy variants retain standing identity and internal-load gates.
- Recorded-pose videos, without new dynamics or repaired motion:
  [failed long composition](../../outputs/walking-sequence-v42/composition-failure.mp4)
  and [failed downhill start](../../outputs/walking-sequence-v42/downhill-failure.mp4).
  Sidecars bind source traces, models, renderer and video hashes; both show FAIL.

No jobs remain from this sequence. All runs were local; no paid compute,
hardware, policy activation or library admission occurred.
