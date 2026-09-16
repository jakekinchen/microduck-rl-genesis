# Visual marker following V1

## Versioned V3 sensor fixture, before its first run

V2's retained smoke exposed a reflection confound: the direct 0.20 m marker
was outside the downward-facing camera FOV in most standing frames, while
its floor reflection remained visible. At 1.0 s the direct center projects
to (183,−29) pixels and its reflected center to (190,117), matching the image.
When both appear, the detector correctly refuses ambiguity. V2 does not
establish correct target recognition or camera-driven locomotion.

V3 lowers the same 70 mm diameter artificial marker center to 0.04 m (5 mm
floor clearance) and sets only the floor material's visual reflectance to zero.
It remains a rendered marker, not a laser, physical rolling ball or obstacle.
Reflective floors are explicitly outside V3's supported perception envelope.
The detector, camera, actors, command gains and all acceptance thresholds stay
fixed. Whole compiled-model numeric arrays must be identical between old/new
fixtures except visual `mat_reflectance`. No collider or actuator is changed.
Retained V2 image tests verify that a direct-plus-reflected ambiguous pair
stops; a single reflection can still fool this appearance detector, so it
must not receive a broader reflective-floor safety claim.

The initial fresh offset-bay declaration uses mass ×1.05 / friction 0.8,
which the inherited frozen physical-domain lane rejects. The array-only
preflight reports it explicitly and prevents that bank from launching.
It remains unopened and unready. A separately versioned fresh-bank amendment
with supported factors is required; the shared physical-domain code is not
changed. All nine ordinary development factors pass the same actual function
on numeric stubs. This preflight addition changes no V3 sensor/motor behavior.

## Versioned V2 low-light follow-up, before its first run

The frozen six-second V1 smoke is retained at
`receipts/visual-follow/20260915-v1-smoke`, including the complete original
source/protocol snapshot and manifest. It observed zero detections, 0/0
qualified steps and no forward progress. Saved images show the marker clearly;
its red channel is 31–45/255, below V1's assumed 100/255. Optical/CAD face
alignment remains 1.0 throughout; no camera-axis reversal is justified.

V2 changes only detector photometry: red ≥20/255, red minus max(green,blue)
≥12/255, and the original red:green/blue ≥1.7 ratios. Camera, illumination,
target geometry, physics, motor actors, command gains and acceptance limits
stay identical. Added tests cover low-light quantization, noisy neutral pixels,
colored false positives, rectangles and large/central partial occlusions.
This improves coverage of observed rendering, not calibrated camera robustness.
`protocol.json` now explicitly identifies V2; the directory and named launcher
retain their V1 experiment-family names. Freeze V2 and a bank-wide source anchor
before observing a new candidate. Every case must match that anchor.

Preregistered September 15, 2026, before any V1 closed-loop candidate run.
This adds pixels-derived commands to the retained V21 walker / V15 stander /
V30 heading controller. It trains no motor actor and changes no motor action.
`protocol.json` is the executable frozen case/threshold matrix.

The initial capability is following one known-size red spherical visual marker
on a flat floor. It is not real ground-laser detection, target identification,
perceptual obstacle avoidance or generalized navigation. Using a raised 35 mm
radius marker at 0.20 m is an explicit sensor-task choice: the prior near-ground
dot is frequently outside the head camera's unchanged field of view.

## Inputs and camera geometry

The perception module accepts only 320×240 RGB pixels and fixed camera
intrinsics/marker radius. The command adapter accepts only a detection,
capture timestamp, monotonic frame sequence and current control timestamp.
No simulator object, target coordinates, robot position, orientation, depth,
segmentation labels or route waypoints enter these APIs. The retained motor
controller keeps its existing proprioceptive observations and IMU heading loop.
Privileged coordinates are restricted to scene rendering and independent scoring.

TerrainWorld already applies `microduck.head-camera-site-aligned.v2`:
camera optical −Z maps to physical CAD-site +X and image-up +Y to site +Z.
The runner verifies those axes and co-location on copied kinematics, records
the camera quaternion/FOV and a physics-array signature, and verifies geometry
and actions are unchanged by rendering. This is a versioned rendering correction,
not physical camera calibration. Camera extrinsic/intrinsic uncertainty remains
a required later randomized sensor factor; V1 fixes those values explicitly.

The detector estimates bearing from image centroid and range from apparent
area plus known marker size. It rejects multiple comparable red components,
clipped blobs, malformed frames, strongly noncircular/occluded shapes and
observations outside its 0.25–1.8 m / ±20 degree vertical envelope. Two new
valid frames are required to acquire/reacquire. A frame older than 120 ms
forces a zero command. Sequence replays cannot refresh its age.

These rules cannot prove arbitrary partial-occlusion or red-distractor safety.
A partial circle that still meets the shape bounds, an unseen red object with
the same projection or unknown marker size can create an incorrect range.
The artificial-marker envelope and explicit ambiguity negatives prevent
claiming an open-world recognition solution. Out-of-envelope test failures
are preserved and block their respective broader claims.

## Independent tests and splits

Two fixed starts per case, each 30 s, with target movement from 1–24 s and
six uninterrupted stopping seconds. Faults occur at 10–13 s; require zero
commands within 140 ms, actual settling in the last second of that interval,
and two fresh frames before resumption. Continuous state, actuator delay and
sensor history are preserved throughout. Cancellation and malformed/future
timestamps are tested at the pure adapter boundary; physical cancellation,
communication jitter and full-duration fault endurance are still unexecuted.

Nine exposed development conditions include straight/sine/mirrored routes,
mass/inertia ×1.1, friction 0.6, motor lag 30 ms, ±0.04 rad start yaw,
image gain 0.7–1.0, RGB noise σ0–2/255, loss, drop, stale sequence,
rendered opaque occlusion, two rendered red markers, and a stationary negative.
Repeated seeds vary image noise; the second independent start also adds
0.01 rad initial yaw, recorded before construction. No training population is
invented for a deterministic controller. The unrandomized straight case is
the baseline. Every materialized physical array is checked against its factor,
and repeat construction from the nominal model checks non-accumulating reset.

Two distinct fresh layout development families (narrow corridor/dogleg and
offset bay/half-cosine with combined variations) are defined before runs and
gate on ordinary development success. They are not seed-only holdouts and
must never be relabeled protected final acceptance after inspection. Existing
protected final banks remain unopened. Future final acceptance must freeze
new layout, appearance, camera and object-size families, ≥20 independent
trials per required bucket, 100% observed safety and ≥95% task success with
reported binomial intervals, plus 180 s and 600 s continuous compositions.
Those tests are not completed by this V1 bank.

Task gates inspect physical target distance, forward progress and cross-track
error. Whole-session gait, loaded slip, actual joint margins, torque, full CAD
penetration, physics-rate applied internal loads, all obstacle contacts,
neutral posture and final settling are independently required. The inherited
gait evaluator's historical reduced-model text remains historical; the new
receipt explicitly binds complete-contact-v11 and active pair audits.
Evaluator exit zero means completion only. Negative control must fail motion
and task completion; physical evidence must remain present.

## Physics and reproducibility

Complete-contact-v11, pinned BAM, 200 Hz integration, 50 Hz 61D→14D ONNX;
no blending, offsets, IK, action clipping, root writes or within-run resets.
Render-only marker/occluder geoms have no dynamics. Solid corridor geoms
retain active contact pairs. Explicit pairs/masks and copied collision witnesses
are audited. Target world geometry is logged for scoring, never fed to control.
Every actual action is byte-compared with fresh inference from the recorded
actor observation. Observations, action tensors, qpos/qvel, camera RGB,
timestamps, detections, commands and 200 Hz load rows are retained.

Freeze local sources/protocol, actor receipt hashes, model documents and mesh
hashes before stepping a candidate; check them after. Preserve failures and
complete per-case manifests. Camera rendering must not change state/action
bytes. Cross-engine and timestep/solver sensitivity remain later diagnostic
gates; no prior same-engine pass supplies that missing evidence. Public BAM
servo data does not calibrate this individual robot, camera, floor or carpet.
Physical calibration, broad robustness and transfer remain blocked.

## Bounded execution

Pure tests require no simulator. Root task coordinates any guarded renderer
smoke and bank with competing training. The smoke runs 6 s of the exact same
protocol and is always marked diagnostic-duration-only; its gates cannot
qualify the behavior. A full exposed bank is at most 27,000 control steps
and 108,000 physics steps. Fresh layout testing is gated on that bank, adds
6,000 controls / 24,000 physics steps, and remains development evidence.
Stop after this frozen candidate and diagnose the first failing component;
do not tune thresholds on its failures or silently rerun a changed candidate.

```sh
.venv-apple/bin/python -m unittest discover -s experiments/visual-follow-v1 -p 'test_*.py' -v
./scripts/duck-ops guard && .venv-apple/bin/python scripts/visual_follow_v1_evaluate.py --case straight --repeat 0 --duration 6 --output receipts/visual-follow/UNUSED-SMOKE
./scripts/duck-ops guard && .venv-apple/bin/python scripts/visual_follow_v1_evaluate.py --bank development --output receipts/visual-follow/UNUSED-DEVELOPMENT
```
