# Moving laser course — Night Shift

September 13, 2026. Scoped local simulation development and video delivery.

The retained V21 walker, V15 stander and V30 heading controller complete the
constructed moving-target course in all six preregistered exposed conditions.
The film uses the nominal run, in full, at its original speed. This does not
admit a general laser behavior to the library or establish physical authority.

## Why the earlier laser gait looked wrong

The old turn-v2 laser policy was a separate motor policy, not the retained
walking policy. Its target reward permitted pathological locomotion. The
retained audit in `GAIT_DIAGNOSIS.md` recorded only 1/0 qualified left/right
swings in 16 seconds, both hip-yaw joints at their stops for the full active
window, and loaded slip above 3 cm/s for 22.76% of loaded samples. It was
simulated dynamics, but its target-only score did not establish valid walking.
That policy and the earlier compilation remain historical rejected evidence.

The new implementation converts the moving dot and robot position into bounded
forward/yaw commands upstream of the retained motor actors. The actors' outputs
are unchanged: no joint offsets, action clipping, IK, root-pose corrections,
motion retiming or resets during a run. This is a coordinate-target adapter;
it does not detect a red dot from camera pixels or perform obstacle perception.
The prescribed moving-dot route guides the duck through the constructed layout.

The actor files come from `receipts/walking/20260906-v30-flat-regression/` and
were checked against that receipt's original manifest:

| Actor | SHA-256 |
|---|---|
| V21 walking | `402d8a8c2b5c67baac9e5cebcf347f8cc5e6159278230d2c452b9826ae4ce017` |
| V15 standing | `2fddc9a9bc4ff9a17a34af51215a31c43503cbe68a1b815a97b3042abf248db8` |

## Course and physics

The course has four alternating solid barriers, two solid overhead gates and
two side walls, on a flat supporting floor. Cyan/magenta lighting, yellow
barrier caps, reflective flooring and a distant backdrop provide the visual
setting. Decorative lights and paint are explicitly non-colliding. All twelve
physical obstacle geoms retain active masks against every robot collider; a
deliberate collision on a copied state verifies engine contact filtering.

The actual simulation uses complete-contact-v11 CAD collision geometry, BAM
actuation, 200 Hz integration and 50 Hz exact ONNX motor inference. Body mass,
inertia, armature, damping and the configured timing remain independently
checked. No training or paid instance was needed. The pinned BAM checkout was
clean at `62bd8ce12154340be97e06f7f41a0ca8f116d967` during readiness checks.

## Final results

Authoritative bank: `receipts/laser-course/20260913-v2-development-r2/`.
Each run lasts 66 seconds, including one second of startup, 60 seconds of a
continuously moving visible dot and a five-second stopping interval.

| Exposed condition | Course and all declared gates | Qualified L/R swings | Loaded slip >3 cm/s | Final X |
|---|---|---:|---:|---:|
| Nominal | Pass | 199 / 200 | 7.36% | 5.083 m |
| Initial yaw +0.04 rad | Pass | 199 / 200 | 7.03% | 5.085 m |
| Motor latency 30 ms | Pass | 191 / 191 | 6.39% | 5.095 m |
| Sliding friction 0.6 | Pass | 199 / 199 | 4.56% | 5.088 m |
| Mass and inertia ×1.1 | Pass | 201 / 201 | 8.14% | 5.081 m |
| Mirrored route, yaw −0.04 rad | Pass | 199 / 199 | 6.75% | 5.085 m |

All six traverse both gates, clear the finish, maintain bilateral stepping,
pass command-response/posture/torque/joint-margin checks, and stop. All six
record zero obstacle contact load, zero obstacle penetration, zero measured
self-penetration, no falls and no non-foot support frames. Each passes the
separate 200 Hz internal-load gate. The nominal gate crossings occur at
29.38 and 55.94 seconds. Nominal final-stop maximum speed is 0.00324 m/s,
maximum yaw rate 0.02147 rad/s, and maximum tilt 6.79 degrees.

Nominal bilateral stepping covers 99.23% of translation. Actual hard-stop
occupancy is zero in five cases; one joint in the 30 ms case has 0.0923%
occupancy under the inherited gait metric and passes the separately measured
actual-margin gate. Raw position targets can exceed nominal joint bounds
(nominal target-outside-bounds fraction 66.55%); this is retained telemetry,
not clipped away. Actual joint-limit violation is zero and torque saturation
passes. These facts do not substitute for actuator or hardware calibration.

The inherited `gait.boundary` text describes the old reduced walk model.
For these new receipts, the top-level model binding, complete-CAD self-contact
probe and explicit collision audit supply the applicable geometry evidence.
The historical nested text was preserved rather than rewriting old evaluators.

## Verification and retained failures

- All six SHA-256 manifests verify; source snapshots were frozen before each
  evaluation and checked unchanged afterward.
- 19,800 motor rows exactly match fresh ONNX inference; 79,200 applied
  physics-rate load samples are present.
- Three focused tests pass, including 150 control steps with and without the
  observer. Actions, qpos and qvel are byte-identical; initial reset states are
  identical and all 600 expected observer samples are present.
- All six materialized domain arrays match their declared factors. Three
  repeated perturbation/nominal roundtrips do not accumulate mass, inertia or
  friction changes. The simulation also checks physical arrays after every
  control step and observes the applied contact friction.
- A stationary negative control has 0/0 qualifying swings and fails course
  and gait completion. It is a six-second diagnostic, not a full-course pass.
- The first v1 design finished before the final gate. Its original scores are
  preserved alongside `20260913-v1-development/CLASSIFICATION.json`, which
  explicitly rejects full-course completion. V2 extends the moving dot and
  requires actual crossing plus clearance of both gates. All active collision
  geometry arrays are identical between v1 and v2; only decorative finish paint
  moves. V2 is a fresh exposed bank, not a retroactive promotion of v1.
- An initial source-freeze error and a later NumPy-boolean JSON export error
  are retained as terminal-error receipts. The latter run's saved actions,
  observations, poses and targets are byte-identical to the successful nominal
  retry. Neither failed export is presented as a completed receipt.

Machine-readable summaries and focused logs are under
`outputs/laser-course-20260913/verification.json`, `domain-audit.json`, and
`focused-tests.log`.

## Film and reproduction

`scripts/render_laser_course.py` verifies the receipt manifest, then renders
saved qpos/qvel without integrating physics. Camera changes therefore show
the same uninterrupted run. No generated robot frames or frame interpolation
are used. The saved motion hash is checked again after rendering.

- `outputs/laser-course-20260913/night-shift-multi-angle.mp4`: 66-second run,
  1280×720 at 25 fps, multiple camera angles.
- `outputs/laser-course-20260913/night-shift-wide-reference.mp4`: the same
  66-second run, one fixed wide camera.
- ChatCut project: https://app.chatcut.io/editor/811514c8-7717-4ea9-ba97-0a35b73de035
  — 76 seconds, with a three-second introduction and seven-second results card.
  The complete run occupies frames 75–1724 at playback rate 1.

The composed ChatCut introduction, tracking, overhead, three-quarter, finish
and results frames were inspected. Export verification and final file hashes
are recorded separately in `outputs/laser-course-20260913/delivery.json`.

```sh
./scripts/duck-ops guard && .venv-apple/bin/python scripts/evaluate_laser_course.py \
  --case all --output receipts/laser-course/NEW-UNUSED-RECEIPT
.venv-apple/bin/python scripts/render_laser_course.py \
  --receipt receipts/laser-course/20260913-v2-development-r2/nominal \
  --output outputs/NEW-MULTI-ANGLE.mp4
```

## Remaining limits

These are six declared exposed development cases, with one run per condition
and one deterministic seed. They do not establish unseen-layout success,
statistical reliability, camera perception, obstacle sensing, real laser
visibility, calibrated friction/actuator/contact accuracy, slopes, steps,
carpet transfer or physical robot operation. The floor is flat: this course
tests steering around barriers and passing under gates, not climbing or
jumping. No protected bank was opened and no policy was activated. Broader
admission still requires `docs/workspace/BEHAVIOR_VALIDATION.md`; the previous
V55 rejection and next standing-posture ablation remain unchanged.
