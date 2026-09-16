# Latest: V23 terrain/endurance validation

**Terrain: 2/12 new-terrain sessions pass (plus 2/2 flat controls). Endurance: four
sustained 180-second walks pass; both 180-second compositions fail cumulative
heading, despite 24/24 short-window scores. Physical calibration awaits real
Ducky measurements.** See [V23-RESULTS.md](V23-RESULTS.md) for the frozen matrix,
retained failures, additive audit and measurement workflow. V21/V22 scores below
are unchanged. No new training, activation or physical-success claim.

# Proper walking — current evidence

No policy is accepted for proper walking yet. The owner-requested work is local
simulation development, not hardware transfer or a camera-driven laser policy.

## V20–V22: walking foundation clears exposed gates — September 6

**V21 FINAL passes all 63 original/repeated windows; the separately frozen V22
physical-combination bank passes 24/24.** All task, gait, motor, joint, posture,
heading, geometric interference and sustained internal-load gates pass without
relaxing thresholds. This is development success within the tested flat-floor
conditions. Full behavior-library, unseen-terrain and physical acceptance remain
unachieved under `docs/workspace/BEHAVIOR_VALIDATION.md`.

V20 first reproduced the two V19 residual failures in Genesis CPU with the exact
V18/V15 actors, V16 ramp and V19 heading controller. All 2,700 actor observations
and 10,800 delayed motor targets matched independently checked histories.
Genesis yaw MAE: long forward20 .234464, long arc-right .202348, nominal forward20
.172793. The yaw error is oscillatory with small signed bias in both engines.
This closed-loop association is not fixed-action causal isolation or calibration.
The first adapter attempt failed a NumPy-to-Torch scalar assignment before its
first physics step; its terminal negative is preserved, and r2 completed all cases.

V21 changes one objective: double the existing instantaneous yaw-error coefficient
for nonzero twist, preserving every V18 physics, action, observation, command,
reset and other reward path. Warm start is exact V18 FINAL; standing stays exact
V15 FINAL with V16 ramp and V19 filtered heading. Smoke completed 7,680 transitions
in 92.890 s. The single 1024×250 run completed **6,144,000 transitions in 1,100.319 s**.
Only FINAL249 was evaluated: SHA-256
`7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322`.
All 149 training source bindings match. Actor/telemetry and all 50 logged scalar
series are finite; 46 series cover every iteration 0–249. Both initial and final
actual timing snapshots cover all 56 allowed motor/three-sensor lag combinations.

| Evaluation | Result | Evidence boundary |
|---|---:|---|
| Original native suite | 21/21 | Same original command/timing gates |
| Exposed repeated starts/stops | 42/42 | Two windows in each continuous physical/controller session |
| New physical-combination bank | 24/24 | Four declared flat-floor profiles, three new commands/poses, two repeats |
| Additional final-standing posture audit | 87/87 | Existing posture thresholds applied separately to 16–18 s |
| Imported mass/COM/inertia audit | 15/15 bodies | Authored-model consistency within float32 tolerance |

The same-controller V19 comparison isolates the actor refinement more directly
than the older V18 full-suite comparison:

| Original failure | V19 yaw MAE | V21 yaw MAE | Reduction | Unchanged limit |
|---|---:|---:|---:|---:|
| Long-delay forward20 | .216391 | .163660 | 24.37% | .20 rad/s |
| Long-delay arc-right | .202569 | .143314 | 29.25% | .20 rad/s |

V22 was frozen only after the full 63-window gate passed. Nominal, .6× sliding
friction, 1.1× mass/inertia and their combination each pass 6/6. Measured runtime
mass is .737243 or .810967 kg; actual observed contact sliding friction is 1.0
or .6. Immutable nominal arrays, reapplication/restoration and separate model
instances are tested. These are exploratory perturbations, not measured hardware
uncertainty. They do not establish broad randomized-physics learning or unseen
terrain/layout families. Maximum real-observation ONNX/Torch action discrepancy
across all banks is 1.91e-6 rad. All 78,300 control rows and 87 case videos exist.

Receipts under `receipts/walking/`: `20260906-v20-paired-genesis-r2`,
`20260906-v20-engine-comparison`, `20260906-v21-training-complete`,
`20260906-v21-current`, `20260906-v21-exposed-repeated`,
`20260906-v21-imported-physics`, `20260906-v21-verification`, and
`20260906-v22-physical-development`. Training stdout is permanently retained.
The new 54-second exact-case video is
`outputs/walking-progress-20260906-v21/duck-progress.mp4`; the old V18 video remains.

Verification: four V21 objective/contract tests, three V22 factor tests and all
131 workspace tests pass. The full simulation regression with pinned BAM completed without failures.
Its legacy `logs/microduck-velocity` deployment check is not applicable because
that checkpoint is absent; V21 ONNX/Torch agreement is verified on all 78,300
actual control observations. No training or simulation process remains active.
Next: separately preregister terrain/layout families, longer endurance and
dropout/composition tests with appropriate independent geometry/contact metrics;
verify broader randomized learning and held-out measurement-based calibration.
No protected bank has been opened and no policy has been activated on hardware.

## V19 course-correction diagnostic — September 6

**5/7 selected windows pass; candidate still rejected.** Same V18 FINAL walking
and V15 FINAL standing policies, V16 command slew, complete V11 model, BAM and
all existing gates. The only intervention low-passes the outer heading
correction at tau=.12 s. It does not filter motor actions or change requested
commands used for scoring. Freeze: `filtered-heading-diagnostic-freeze-v19.json`.

| Window | V18 combined | V19 combined | V19 yaw MAE (rad/s) |
|---|---|---|---|
| Long 30/20-ms forward12 | Fail yaw | Pass | .194322 |
| Long 30/20-ms forward20 | Fail yaw | Fail yaw | .216391 |
| Long 30/20-ms arc-right | Fail yaw | Fail yaw | .202569 |
| Nominal 20/20-ms forward20 | Pass | Pass | .153498 |
| Zero-lag turn-left | Pass | Pass | .135545 |
| Motor25/sensor20 arc-left117/448, first | Fail geometry | Pass | .124744 |
| Same world, second window without reset | Pass | Pass | .131452 |

All seven finish without falls and pass heading, geometry and sustained-load
gates. First arc-left startup max penetration is now .506505 mm, versus V18's
1.040036 mm; the repeated window has zero overlap. This is a selected exposed
diagnostic, **not** full 21+42 regression or newly held-out success. Two yaw
failures remain above .20 rad/s; do not round or relax them. No new development
bank or training run was opened. Six focused controller tests pass.
All seven actual videos, raw float32 actions, trajectories with 200-Hz loads,
147 source snapshots, exact policy identities and manifest are retained at
`receipts/walking/20260906-v19-filtered-heading-diagnostic/`.
Closing audit verifies all 165 manifest files, all 147 current/captured sources,
6,300 trajectory rows and 25,200 physics-load samples. All seven saved float32
action arrays match their recorded row actions byte-for-byte; the recorded
filtered-correction recurrence also matches. Manifest SHA:
`0c0a83c5ea9dab64cf77fd0cef1f7131a8148af85d3e5b1b41653dc61d374d5f`.
Startup arc-left and failing fast-forward videos decode fully; sampled frames
were inspected for stepping and posture. These checks do not override failures.

Pre-intervention read-only analysis is retained at
`receipts/walking/20260906-v18-residual-analysis/`. The three long-delay yaw
failures have signed mean errors between -.00474 and -.00253 rad/s, but
standard deviations .2456–.2740 rad/s and dominant frequencies 3.09–6.26 Hz.
IMU heading-rate derivatives corroborate the motion. No correction saturation
was found; correlation with body yaw is association, not controller causality.
The filter helps some cases but does not resolve the fast-forward oscillation.
Next: separately freeze a same-pair Genesis closed-loop diagnostic, validating
effective timing/history first. Do not infer a solver cause from differing
closed-loop actions, or prescribe another reward change from this correlation.

### V18 recipe erratum: effective command mix

`UNBRACED-WALKING-v18.md` incorrectly states a 5-percent standing population.
The effective inherited method is V2's
`MicroduckControlledWalkingEnv._resample_twist`: **40% forward, 25% turn,
10% arc, 25% stop**, also recorded in `logs/walking-20260906-v18/run.json`
under `env_cfg.command_mix`. V18 did not change that sampler. The 5% value
belongs to the overridden V1 sampler; inheritance was misread in the prose.
Do not rewrite the frozen plan or run artifacts. This erratum corrects the
description, not the implementation, policy, results or experiment identity.
`tests/test_walking_effective_contract.py` adds deterministic effective-bucket,
bounds, resampling-interval and metadata checks to prevent recurrence.
All three contract tests and six filtered-controller tests pass; both are now
registered in the full runner. Workspace verification passes 122 tests with
zero skips/failures/errors. The full simulation regression was not rerun for
this diagnostic; no trainer/evaluator remains active. The V18 user-video server
is retained for playback, and that older video is not relabeled as V19.

## Latest video and final V18 result — September 6

`walking-20260906-v18` completed all 6,144,000 transitions in 1,398.282 s.
FINAL249 SHA `922bd58e2ad2d6657dc7797f28b638f8294ab57ab9963c458569130b4d13e70b`;
all 140 source hashes match. ONNX SHA
`c207b569c4d4391b9207a7283cffcd94810442293a6a8e0184a80bca35e36a58`.
Current native final is **18/21**: no falls; all 21 heading, self-geometry and
sustained internal-load gates pass. The only failures are long-delay moving
yaw-rate MAE: forward12 .207006, forward20 .218392, arc-right .216174 versus
.20 rad/s. This is a regression on the original V15 bank, not blanket success.
Repeated-start development is **41/42**, improving from V15's 33/42. All 42
avoid falls and pass heading and sustained internal-load gates. One first
arc-left117/448 startup, motor25/sensor20, has one geometric failure at 1.44 s:
battery/leg overlap 1.040036 mm versus 1 mm. Its >1-N load lasts 40 ms, below
the frozen 50-ms rejection, but that does not override the geometric failure.
No new closed bank opens; no trainer or evaluator remains active.

`outputs/walking-progress-20260906/duck-progress.mp4` is the user-requested
54-second video: full nominal forward12 and turn-left recordings, then full
long-delay forward20 labeled as a yaw-stability failure. 25 fps / 1x, 1,350
actual simulator frames, labels/padding only. It decodes cleanly; sampled
frames were visually inspected. Provenance binds the three source videos,
both exact policies and the current evaluator manifest. Not hardware evidence.

Training run.json, final/intermediate checkpoints, 140 captured sources and
TensorBoard iterations 0–249 remain intact. Temporary training stdout was
unavailable at follow-up; it is not synthesized or claimed as retained.

## Current result: V13 rejected; unbraced standing/stop transitions

Latest decision: V15 passes all 21 original cases but **33/42 fresh repeated
windows**, so proper walking is still rejected. Four fast-forward first-cycle
stops fall; four following windows are correctly not run after those falls.
One repeated right-turn STARTUP (not stop) has sustained internal loading.
V16 command slew passes 5/6 selected diagnostic windows, fixing tested
fast-forward stops but leaving 245 ms of turn-start body bracing. V17 tests
one gentler yaw acceleration with fixed actors/physics/gates. Neither limited
diagnostic replaces full regression. Full simulation suite and 120 workspace
tests pass; they do not override the behavior failures.

V13 FINAL controller result is **20/21 motor/posture and combined, 21/21
heading, 20/21 geometric self-contact**. Long-delay fast forward falls at
14.98 s, 1.98 s after zero command; both policy and user command are zero.
Current raw actor is 19/21 motor/posture, 5/21 heading, 20/21 geometry, 4/21
combined, without falls. Old reduced-model protocols are sensitivity evidence:
2/21 old regression (11 falls), 1/21 legacy-sensor (11 falls), 1/21 reduced
current-sensor (13 falls). The corrected model result is not replaced by them.
All final videos, original float32 actions and ONNX are retained. ONNX SHA
`feef32793eb4bf915d9dee93a8fe1a778d37d0b4619ee8c04526d1ff2cf615e2`.
Current-controller real-observation parity max 1.66893e-6 rad.

`20260905-v13-contact-loads` replays three cases with every recorded qpos and
original float32 action byte identical. Native forces are read after every
5-ms step, without re-forwarding physical data. Moving intervals have zero
self-load. Nominal forward08 settled stop has 14.9277 N mean summed internal
normal load, largest pair up to 6.5934 N and >1 N in 100% of samples. Long
arc-left is similar (14.7841 N summed mean). The fast-forward terminal case
has braking loads, but no settled-stop samples: missing is unknown, not zero.
This is **internal leg/battery bracing**, not battery-ground support. It exposes
a missing load-based rejection criterion; it does not alone prove fall cause.
Genesis's >10-N contact-count reward and native summed forces are not directly
equivalent contact-manifold quantities. Geometry-only success was insufficient.

`20260905-v5-complete-stance-baseline` is 2/21 combined on the complete model,
not an accepted older policy. Exact replay in `20260905-v5-complete-stance-loads`
has zero self-load in all phases of nominal forward08, long forward20 and long
arc-left. This motivates one fixed command-only standing/walking split, not
checkpoint search or proof of standing quality.
`STAND-SWITCH-v14.md` freezes additive sustained-load rejection, then scores
unchanged V13 before the fixed V5/V13 pair. Eight load/routing tests pass.
The complete new baseline is **0/21**. Its observing evaluator reproduces all
18,749 original qpos frames and all 21 original action files byte-identically.
The fixed pair is **13/21 combined**, with all 21 heading/geometry/load gates
passing and no falls. **Zero internal contact load across all 75,600 physics
samples.** All failures are stop tilt: eight cases, 15.0712–16.5418 degrees
against 15. No moving tracking, stepping, slip, joint, torque or head failures.
Real-observation parity: walking <=1.54972e-6, standing <=1.07288e-6 rad.
All actual V14 videos are retained and the long-delay fast-forward stop was
visually inspected; the residual lean is visible, not dismissed as perspective.

Current intervention is `STANDING-v15.md`: refine only the standing component,
not the walking actor. Five command/load/reward tests pass; 64x5 smoke completes
7,680 transitions in 83.1798 s, with zero commands and finite rewards/loads.
Smoke checkpoint SHA `ab322573ebd43d22fb7970f63835e1e9ae28f13132df156fbce20db8b786ef69`.
All 118 current/captured sources match. Bounded 1024x250 training completed
all 6,144,000 transitions in 1,416.893 s including startup. Declared FINAL249
SHA is `acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46`.
Complete training is retained at `20260906-v15-standing-training-complete`.
No trainer remains active. Full final paired ONNX evaluation/video is now
**21/21 in every required gate**, without falls. Worst stopped tilt 6.7963
degrees, stopped speed .0034783 m/s, moving forward MAE .0202816 m/s, moving
yaw MAE .177884 rad/s and heading endpoint 2.3443 degrees. Standing ONNX SHA
`2fddc9a9bc4ff9a17a34af51215a31c43503cbe68a1b815a97b3042abf248db8`;
real-observation parity walking <=1.66893e-6 / standing <=1.19209e-6 rad.
There is one brief internal-contact transient in long-delay forward08:
20 ms above 1 N (0.1111% occupancy; peak 5.29893 N), within the pre-frozen
50-ms/1% limits. Do not describe V15 as having zero contact: it avoids sustained
body bracing. All 75,600 load samples and all 21 actual videos are retained
at `20260906-v15-standing-pair`; the current manifest verifies. Actual nominal
forward12 stop footage was inspected and shows the upright correction.
Fresh 42-window development completed at 33/42 and is now exposed. Full
simulation suite and 120 expanded-reader workspace tests pass. V17 gentler
yaw diagnosis is 4/6, worse than V16's 5/6; retain V16, reject V17. V18 now
tests load-aware walking training with fixed V15 standing and V16 command
ramp. No physical deployment or accepted walking yet. Earlier receipts:
`20260906-v14-load-baseline` and `20260906-v14-standing-pair`.

V15 intermediate50, `20260906-v15-standing-intermediate50`: three deterministic
fixed-walker / Torch-standing diagnostic cases pass every required gate.
Nominal forward08, long forward20 and long arc-right stop at 6.7178, 7.0688
and 6.6142 degrees respectively, with zero internal loads. Long forward20
moving yaw MAE .1978965 is close to the unchanged .20 limit. This is positive
diagnosis, not a full-bank, final-ONNX or checkpoint-selection result. Training
subsequently completed unchanged to declared FINAL249. The latest 30 correction tests,
eight standing-routing/load tests, five reward tests and 120 workspace tests
pass; the full simulator suite has not been rerun during the active trainer.

## Retained corrections: real body contacts, heading control, persistent timing

The v9 reduced-model crouch crosses actual watertight battery and leg CAD
triangles. Six positive noncoplanar witnesses are retained in
`20260905-v9-raw-cad-intersections-r2`; even nominal slow-forward crosses at
0.90 s left and 1.16 s right. This is not merely a convex hull filling a cavity.
All 21 old current-sensor traces fail additive >1-mm self-interference rejection.
The reduced model could not detect those battery contacts.

The v11 model uses bundled full CAD and restores support/leg compatibility
by changing the support mask from 2/2 to 1/1. Six tests confirm identical
compiled physical arrays and visuals, union of old contact-filter pairs,
body-floor coverage and clear HOME geometry. Genesis retains battery/leg
pairs; in 2,654 copied poses only two contact-pair presence disagreements
remain. Contact POINT counts differ by manifold algorithm; do not confuse
them with missing-contact FRAME counts. Decimation is not changed or blamed
as the demonstrated cause: disabling it removes sampled support-shape error,
but did not remove the one reduced-model pair-presence disagreement.

The same original v9 actions fall in Genesis after 1.52/1.56 s in the complete
model, ending those fixed-action comparisons before a native fall. However,
normal closed-loop v9 ONNX feedback reacts to the new contacts: full native
21-case baseline has **no falls or body-interference failures**, motor/posture
17/21, heading 7/21 and complete combined 6/21. Four long-delay moving-yaw
failures remain; stops/head/joints/torque/slip/stepping all pass. Full videos
repeat 6/21. Actual slow-forward foot-lift footage was inspected.

V12 separately adds a fixed 2/s IMU heading COMMAND servo (bounded +/-0.25
rad/s correction, +/-0.75 total), not a motor-output filter. Same exact v9
ONNX bytes and complete v11 physics. Score USER commands, record corrected
policy commands and delayed IMU source. Full current bank: **17/21 combined,
21/21 heading**, worst endpoint 6.38 degrees/phase 8.94 degrees; real-observation
Torch/ONNX difference <=1.55e-6 rad. Only long-delay forward12, forward20,
arc-left and arc-right fail instantaneous yaw MAE at .2088/.2194/.2249/.2095
versus .20. Preserve these negatives. This is controller-plus-policy behavior,
not an unassisted policy or hardware IMU validation. Fresh bank stays closed.

V13 activates persistent episode delays on the verified contact model:
`PERSISTENT-CONTACT-v13.md`. Same uniform lag limits/FIFO, v9 reward/control
functions and fixed v12 deployment controller; no inference assistance inside
learning. This first new learning run includes both corrected contact coverage
and persistent timing relative to old v9 training, not a clean training-cause
ablation. V11 model-only training was not started. Thirty correction tests
and 115 workspace tests pass; 64x5 smoke completes 7,680 transitions in 82.12 s,
checkpoint `b3c679d7e3489e484b01868924b1db08f14719cfb2549813b1333dd6ec4f5629`,
all 123 sources/meshes match. Bounded 1024x750 run started; final-only candidate.

The bounded v13 run is now complete: 18,432,000 transitions, 4,214.939 s
including setup and concurrent diagnosis; FINAL `model_749.pt` SHA-256
`f31d47a5343b1283a1bbd28c2f7efb78f95ddd6940554b9c755b73d337c2b7f8`.
All 123 live/captured sources match. `20260905-v13-training-complete` retains
the run, stdout, tests, all checkpoints and source. Final ONNX evaluation is
complete and rejected as summarized above; completion is not acceptance.

Intermediate150 is retained as diagnosis only: **21/21 motor/posture, heading,
self-contact and combined** with the unchanged v12 command controller, using
normalized Torch CPU inference. Checkpoint
`530715a36d86bfcbcce90d28a24bbcab50808369cb50a7fc84ea99e2194503a2`.
Worst moving yaw MAE is below .1674 rad/s, endpoint heading below 4.60 degrees,
stop tilt below 1.88 degrees. Every case has perfectly alternating qualified
landings (37–52 per foot), median swing duration .12–.16 s and median sole
clearance 8.14–18.87 mm. Actual nominal slow-forward, left-turn and long-delay
fast-forward videos are retained; stepping and braking contact sheets were
visually inspected. This earlier probe does not replace the rejected final;
it did not test the later self-load gate. No fresh-bank opening, ONNX acceptance
or physical claim follows this probe.
Separate raw-actor intermediate150 diagnosis is motor/posture 21/21 and body
contact 21/21, but heading/combined only 9/21. This establishes that the heading
servo is still necessary for the 21/21 result; learning has not independently
solved cumulative drift. `20260905-v13-intermediate150-raw` retains all cases.

Intermediate500 is **20/21 combined and motor/posture**, with heading and
self-contact 21/21. Only long-delay arc-left fails moving yaw MAE:
.2177668966 > .20 rad/s. No falls, head/stop/joint/torque/step/slip regressions.
`20260905-v13-intermediate500` preserves every case and three actual videos.
The good intermediate150 is not promoted; evaluate the declared final.

Supplementary v12 physics-step contact audit:
`20260905-v12-substep-contact-audit` covers **75,600 poses at 200 Hz**.
Every original 50-Hz qpos and float32 motor action replays byte-identically;
copied geometry sampling does not change the physical rollout. No sample
exceeds 1-mm self-penetration (maximum .873783 mm). This addresses temporal
gaps between control/video frames on the defined collider model, not exhaustive
raw-CAD or hardware geometry. The original v12 motor result stays 17/21.

New receipts (all under `receipts/walking/`): `20260905-v9-self-contact-copied`,
`20260905-v9-self-contact-no-decimation`, `20260905-v9-raw-cad-intersections-r2`,
`20260905-v9-current-sensor-self-contact`, `20260905-v11-self-contact-copied`,
`20260905-v11-fixed-action-baseline`, `20260905-v11-native-baseline`,
`20260905-v11-native-baseline-video`, `20260905-v12-current-sensor`,
`20260905-v13-smoke-complete`, `20260905-v13-intermediate150`. Initial raw-CAD binding-shape exception is
retained as incomplete, not a negative geometric conclusion.

## Historical v9 terminal result: collision gap took priority

V9 FINAL completed 18,432,000 new transitions in 3,913.2 s total.
Checkpoint `c79e02bc00dabca146b83592582926fc2053114cc5e44cdf822f95aa8ff8fb17`;
ONNX `dc27ad221d2519b40e1c06979d254fdc308a17cc7a8d3ec9592668d6d39e7ab1`.
All 35 training source files match retained bytes. Complete old / new legacy
clock / new current sensor protocols give respectively 12 / 15 / 12 of 21
motor-posture passes, 7 / 6 / 7 heading passes, and **5/21 combined each**.
Head posture passes all cases. Current-sensor has five falls and nine actual
joint-margin failures. Final Torch/native replay is also negative (11/21
motor-posture, 7/21 heading, 5/21 combined), not an ONNX-only problem.

The complete Genesis CPU final bank has no falls or stop/head failures, but
heading only 12/21. Heading remains a policy problem; native braking/joint
collapse adds a simulator mismatch. Actual videos were viewed, including
nominal forward12 braking failure. Do not select a better intermediate.

All-frame full-CAD floor clearance remains positive (current: 18,777 poses,
minimum 13.38 mm), but **this says nothing about self-collision**. Native
byte-identical float32 action replay with the bundled full-collision model
makes nominal slow forward fall at 1.94 s, whereas the reduced reference
finishes. Left-turn original input ends at a recorded fall after 857 actions;
the full variant falls after 109 actions. Partial input is preserved, not
padded. `20260905-v9-full-collision-replay-r2/audit.json` retains both negatives.
The initial audit rejected that partial input; its incomplete output and
`FAILURE.md` remain separately retained.

Important: full versus reduced also changes existing leg masks from 2/2 to
1/1 while adding the battery and other colliders. Body-name contact summaries
therefore do not identify equivalent mesh pairs. Neither collision model is
assumed calibrated physical truth. Diagnose masks, proxy geometry and exact
copied-state contacts before any new training. The conditional v10 persistent-
timing proposal is paused. All earlier thresholds and receipts remain intact.

Final receipts: `20260905-v9-training-complete`, `20260905-v9-old-regression`,
`20260905-v9-final`, `20260905-v9-current-sensor`, their separate `-heading`
reports, `20260905-v9-final-torch-native`, `20260905-v9-genesis-full-bank`,
`20260905-v9-body-clearance`, and `20260905-v9-full-collision-replay-r2`, all
under `receipts/walking/`. No hidden acceptance, policy activation or hardware.

## Previous completed result: v8 fixes trunk balance, regresses head posture

V8 completed 24,576,000 transitions in 4,179.3 seconds including setup.
Final checkpoint `348030128f56145a5172fe8ad8469394cb5afab3fd5a6911ac124373493e818f`;
ONNX `8f4f12a254fdd246e66306cd81ed3e25c56f7cbef2f2e7b41b537b33d2d66647`.
All three complete protocols are **0/21**: head posture fails all 21 each.
Current-sensor trunk stops are 6.30–6.77 degrees, no falls and no actual
joint-stop, torque, slip or stepping failures. Six cases fail yaw-rate tracking.
Heading separately passes 9/21 old, 7/21 legacy new, 9/21 current; zero combined.
Real-observation ONNX parity is <=1.67e-6 rad across the three protocols.

Actual final footage shows a normal moving head, then the neck tips far back
at stop (nominal slow forward: neck about -0.68 rad versus HOME +0.349 rad).
Genesis also exhibits the regression. This is physical joint behavior and a
reward trade-off, not a camera error. Full-CAD clearance has no penetrating
frames (18,900 per protocol; current minimum 14.36 mm). Two 18-second native
full-collision replays keep raw float32 actions and qpos byte-identical to the
reduced model, with no extra contact pairs. Scope is those two cases, not
universal collision or physical fidelity.

V8 checkpoint500 was 13/21 original, 5/21 heading, 3/21 combined; all stops
were upright with good head/motor margin. It was not eligible for promotion.
Offline reward sensitivity shows that persistent gyro drift can barely affect
the instantaneous yaw reward amid oscillation; removing recorded DC bias is
algebra, NOT a real control action or a learned improvement.

The yaw-only draft was not trained after final head regression appeared.
`VIABILITY-v9.md` freezes a combined objective-composition intervention:
posture conditions all positive return, negative costs are never gated away,
and a 1-second yaw-error EMA prices persistent drift. No changed physics,
model, action filtering, observation, timing, commands or acceptance gates.
Pretraining accounting over 2,000 actual Genesis samples and 183 landings
matches the independent reward-term sum within 5.4e-6. Fifty focused tests
pass. Smoke completed 7,680 transitions in 94.6 seconds and the bounded
1024x750 run is learning, all 35 source hashes matched. No v9 FINAL behavior
result exists yet; intermediate diagnostics are below. Full regression passes using `tests/run_all.py`, which isolates
Genesis initialization per process. An initial incorrect one-process unittest
discovery failed on module initialization/import isolation; its failed log is
retained separately, not reported as a physics failure or silently overwritten.
The viewer now exposes recorded failure reasons beside videos and in the
table. It also joins the separately manifested heading report by exact parent
input/policy/checkpoint identity, displaying combined results first without
rewriting original motor/posture scores. Missing, stale, partial or inconsistent
heading evidence stays unknown. All 109 current workspace tests pass and the
actual viewer shows v8 at 0/21 combined, 0/21 original and 9/21 heading.
This is reporting correctness, not a gait improvement.

Evidence: `20260905-v8-training-complete`, `20260905-v8-old-regression`,
`20260905-v8-final`, `20260905-v8-current-sensor` and their `-heading` reports;
`20260905-v8-body-clearance`, `20260905-v8-full-collision-replay`,
`20260905-v8-genesis-full-bank`, `20260905-v8-final-yaw-objective`,
`20260905-v9-reward-decomposition` under `receipts/walking/`.

Native MuJoCo/BAM feasibility measured 2,663/5,250/10,110 control transitions/s
with 1/2/4 local workers under concurrent v8 training. No PPO/reward/batched
inference measured and no native trainer implemented. All own workers exited.
This supports a later scoped option, not a simulator-calibration or training
throughput claim. Evidence: `20260905-native-worker-feasibility`.

## Temporal delay randomization can hide persistent steering bias

The same v8 FINAL mean was tested in Genesis CPU with the seven exposed
commands under the actual training delay process (motor 0..6 physics ticks,
resampled every 64 ticks; independent 0..1 sensor-control-tick buffers every
64 control ticks). All seven yaw MAEs are 0.125–0.163 rad/s. Its straight-walk
signed biases are -0.0026, -0.0102 and +0.0004 rad/s. Under constant device
profiles, the same controller's slow-forward biases are -0.0918 (20/20 ms),
+0.0546 (zero), and -0.0989 (30/20 ms). Head posture remains bad in both modes.

This is one seeded diagnostic, not a generalization result or a fixed-action
physics isolation. Nonetheless it shows that quickly changing random delays
can average away a bias that persists with one device's delay. More jitter is
not automatically better coverage of physical device uncertainty. Keep v9
unchanged; if its final still fails fixed-delay buckets, test episode-persistent
delay sampling as a separate temporal-domain intervention, not an action
correction or a reason to discard fixed-profile tests. Do not simultaneously
change mass, contact or commands and claim the delay hypothesis is isolated.
Evidence: `20260905-v8-genesis-training-jitter` versus
`20260905-v8-genesis-full-bank`.

## V9 first diagnostic, checkpoint50

All 21 head-posture checks are restored and trunk stops are 3.1–6.9 degrees.
No falls, actual-motor/step/slip failures. However stopping yaw fails all 21,
stop speed 14, moving yaw six; heading 5/21, combined zero. This is an early
diagnostic, not a selected controller: changing the head balance configuration
has not yet produced a quiet stop. Keep the fixed run unchanged.
Evidence: `20260905-v9-probe50-full-bank`.

## V9 intermediate150: gait and quiet posture restored, drift unresolved

The complete exposed current-sensor bank is **17/21 motor/posture, 6/21
heading, 6/21 combined**. Head posture, actual joint/torque limits, stepping,
slip, falls and quiet stopping pass all 21. Stop torso tilt is 3.3–3.6 degrees.
Only original-gate failures are yaw-rate accuracy at zero-delay fast-forward
and arc-right, and longest-delay fast-forward and arc-right. Cumulative drift
still fails 15 cases and is not forgiven by passing mean speed.

Actual four-case footage shows normal head configuration through moving and
stopping, foot lifts and quiet upright stops. Copied full-CAD geometry checks
all 18,900 full-bank poses, minimum non-foot clearance 14.28786 mm and zero
penetrating frames. This is geometry, not all-case dynamic collision proof.
The controller is a Torch-mean intermediate, never a selected ONNX final.

Evidence: `20260905-v9-probe150-full-bank`, `20260905-v9-probe150-video`,
`20260905-v9-probe150-body-clearance`, `20260905-v9-probe150-genesis-full-bank`.
The fixed 750-iteration run remains unchanged. A separate conditional
`PERSISTENT-TIMING-v10.md` proposal changes only delay resampling time if the
v9 final still shows fixed-delay control failures; it has no active run.
Seven pure CPU FIFO/inheritance tests pass after a test-only dtype fixture
fix. The initial test harness lacked Genesis's initialized dtype; no active
training source was changed and no simulator was initialized for those tests.

## V9 intermediate500: long-delay stopping fall retained

Current-sensor full bank: **16/21 motor/posture, 9/21 heading, 7/21 combined**.
Head posture stays acceptable, but 30/20-ms fast forward falls at 13.88 s,
0.88 seconds after its required stop. This is not the v6 startup fall: at
1 s it is upright (5.60 degrees), and just before stopping at 13 s it is
2.61 degrees with 0.201 m/s forward speed. During braking the torso leans,
then accelerates forward again and falls (55.36 degrees, 6.21-cm base height).
Its actual joint margin remains 0.135 rad at the terminal frame. Four other
30/20-ms cases fail yaw rate. A partial stopped trajectory does not qualify
for stopping metrics or complete walking. Intermediate150's better stopping
coverage is not selected instead. The final-only fixed run continues.

The same-checkpoint Genesis CPU fixed-profile diagnostic completes all 21
without falls or head/stop failures. Its 30/20-ms fast-forward stop settles
at 4.43 degrees, 0.00148 m/s and 0.00516 rad/s. Three long-delay moving-yaw
cases fail the 0.20-rad/s threshold. Thus the specific braking collapse is
native-only in this check; timing-sensitive direction control remains in both
engines. Full-CAD geometry clears all 18,694 available native poses by at least
12.71 mm, including the failed case. The fall is not hidden floor penetration.
Offline application of the same immutable heading function to the verified
Genesis traces passes 12/21, so directional drift is not solely an engine-
transfer problem either. The diagnostic log records each trace hash and the
heading-function hash (`/private/tmp/walking-v9-probe500-genesis-heading.log`).
Future backend probes retain this heading calculation alongside their existing
response fields; no dynamics, observation or action change is made.

Evidence: `20260905-v9-probe500-full-bank`,
`20260905-v9-probe500-genesis-full-bank`, `20260905-v9-probe500-body-clearance`.
The conditional timing proposal must account for this non-yaw, cross-engine
failure before any activation; its success cannot be inferred from Genesis
stability alone. Native MuJoCo remains a required independent check.

## Historical v8 intermediate signal — not candidate acceptance

The new full-bank checkpoint150 diagnostic passes **12/21 motor/posture,
8/21 additive heading, 4/21 combined**. All 21 stop at 5.6–6.4 degrees and none
falls, including the longest-delay fast-forward start that failed in v6.
Remaining original-gate failures: yaw rate six cases, actual left-hip-yaw
margin three left turns (minimum -0.00468 rad). Cumulative directional drift
still rejects many otherwise passing cases. These cannot be averaged away.

All 18,900 copied full-CAD poses clear the floor, minimum 14.63 mm. Viewed
25-fps stepping frames and the stop clip show alternating foot lifts and an
upright final stance, not the old deeply leaning stop. These are intermediate
Torch-mean observations, not an ONNX-selected final or hardware claim. The
fixed 1000-iteration run subsequently completed as the rejected final above.

Evidence: `20260905-v8-probe150-full-bank`, `20260905-v8-probe150-video`,
`20260905-v8-probe150-body-clearance`. The full-bank diagnostic was first
validated on v6's final: it reproduces its 20 stop-tilt/seven yaw/one fall
failure counts. It is still not a replacement for final ONNX evaluation
(its heading count was 1/21 versus the ONNX run's 2/21).

## Earlier completed result: v6 rejected

V6 completed 36,864,000 new transitions in 4,600.1 seconds, including setup.
Final checkpoint `0f0cad5839cf22c492e69dfd1d1e41c26ce430a0363018bf5fa13faf6333afba`;
ONNX `948f6e601098845bf394c60de61cb38aa435d61934b86fc46dd39e4c9908c8cb`.
All three complete exposed protocols are **0/21**. Their additive heading
checks pass 0/21 old, 1/21 new-heading legacy-clock, and 2/21 current-sensor;
every combined result is still zero. Real-observation parity is <=1.91e-6 rad.

Current-sensor failures: all 20 completed stops lean 26.6–34.7 degrees,
seven cases fail yaw-rate tracking, and long-delay fast forward collapses at
2.06 s (base height 6.88 cm, tilt 29.1 degrees, actual joint margin -0.0258 rad).
All 21 head-posture checks pass, including that short trajectory, but this
does not forgive the fall. Legacy new headings also have a long-delay arc
fall; old headings have one fall and 20/21 head-posture passes. The short
four-case diagnostics did not cover this long-delay failure. Preserve it.

The final Genesis CPU diagnostic independently stops leaning 26–31 degrees.
Actual final videos show upright steps followed by the bad stopping lean.
Two native reduced/full-collision fixed-action replays are byte-identical and
add no contact pairs, but the all-trace CAD audit catches one terminal jaw
penetration in the already-failed legacy arc (minimum -17.5 mm). Old/current-
sensor traces have no penetration, minimum 9.14/14.41 mm. No hidden support,
fall, or partial trajectory is accepted; these are distinct scoped results.

Training, three original protocols, three additive heading reports, full-CAD
audit and full-collision replay are retained under `20260905-v6-*`. Full
regression tests pass; that is not behavior acceptance. V5 remains the
partially passing viewer baseline. The separate, now source-bound
`BALANCE-v8.md` reward-only correction passed 64x5 smoke (7,680 transitions,
59.3 seconds) and its bounded 1024x1000 run is learning only from the pinned
v6 final. All 29 captured sources match. No physics, action-filter or threshold
changes; only the declared final can be a candidate.

A command-start-time diagnostic reproduces the v6 longest-delay fast-forward
collapse: one second of initial standing leaves 24.0-degree lean at command
onset and falls 1.06 seconds later. Shortening only that initial stop to 0.24
or zero seconds avoids a fall through each complete 12-second motion plus
five-second stop, but both still finish leaning 29–35 degrees. This supports
initial stance as a contributor; it does not prove any changed schedule meets
the walking battery. Do not remove the required initial stand or use a startup
assist. V8 retains the original command/test schedules. Evidence:
`20260905-v6-startup-stance`.

## Earlier completed baseline: v5

V5 completed 18,432,000 new transitions in 2,677.2 seconds. Final checkpoint
`19fef3b5d443001f817169cecc660a2bef51b34791b5d84dfa59cc4e619a43c1`;
normalized ONNX `bec30f12672fe5b447d5aaf71b61bd2925719645d18c480591300c43ca7e2345`.
The three unchanged development protocols score **6/21 old regression,
5/21 v5-heading legacy-clock, 6/21 corrected-current-sensor**. Every head
posture gate passes; all actual-joint/torque/slip gates pass. The intermediate
hip-stop shortcut is repaired in the FINAL and must not be reported as current.

Corrected-sensor failures: yaw 15/21, stop tilt 5/21, and one zero-lag right
turn with no useful bilateral stepping. Motor saturation is at most 0.0913%;
minimum actual joint margin is 0.0904 rad. All stop speeds/yaw rates pass.
The viewed slow-forward clip and 25-fps step contact sheet show actual foot
lifting with a normal head, not sliding/stop parking. This passing case does
not erase the remaining directional and stop-posture failures.

Both complete 18,900-frame new-heading body-clearance audits pass, minimum
13.17 mm over all eight non-foot meshes. Real-observation normalized ONNX
parity is below 1.91e-6 rad. Sources and full regression tests are retained in
`20260905-v5-training-complete`; final protocols are `20260905-v5-old-regression`,
`20260905-v5-final`, and `20260905-v5-current-sensor` under `receipts/walking/`.
Current next intervention is `CONTACT-v6.md`: the independently measured native
contact default, with rewards and thresholds unchanged. No physical acceptance.

V5 deterministic playback on **Apple Metal**, not only Genesis CPU, also
has forward yaw error about 0.255–0.257 rad/s and a zero-lag left-turn no-op
(yaw error 0.486 rad/s; neither sole meaningfully lifts). It agrees qualitatively
with the CPU diagnosis. This is a one-environment backend diagnostic, not
bitwise CPU/Metal equivalence or a 1024-environment replay. Evidence:
`20260905-v5-metal-response`. V6 checkpoint150 corrected-sensor diagnostic
is 1/4, head posture 4/4: heading and stop tilt still fail, but actual joint
stops/torque/slip do not. Its final is not yet available; keep training fixed.
Evidence: `20260905-v6-probe150-sensor`.

V6 checkpoint500 remains diagnostic and is **0/4** on current-sensor native
cases. Turning yaw improves to 0.148/0.160 rad/s with real steps, but all stops
lean 26–29 degrees; forward yaw remains 0.210–0.223 rad/s. No actual joint-stop,
torque or slip rejection occurs. The same checkpoint's Genesis CPU probe also
steps on its formerly static zero-lag turn. This is not a completed candidate;
the frozen training continues, and body posture remains an explicit failure.
Evidence: `20260905-v6-probe500-sensor`, `20260905-v6-probe500-genesis`.

V6 checkpoint750 is also **0/4**, but now every diagnostic's only rejection
is stopping tilt (30.24–33.96 degrees). Yaw MAE is 0.095–0.195 rad/s; movement,
step, slip, torque and joint gates pass. The run remains immutable and its
final result is pending. A separate conditional reward-only correction is
prepared in `BALANCE-v8.md`: price trunk lean beyond ten degrees without
prescribing exact HOME leg positions. It cannot launch before completed v6
final evaluation, and cannot select an intermediate. Four isolation/math tests
pass. Evidence: `20260905-v6-probe750-sensor`.

Checkpoint1000 still stops at 32.8–37.4 degrees; all four are rejected and one
nominal forward yaw error also fails. Actual rendered frames show upright
walking followed by the lean after the stop command. At checkpoint750, moving
torso tilt was below 6.1 degrees in all four probes: the prepared ten-degree
lean deadband does not penalize those measured moving motions. This is a
stop-posture trade-off, not an assumption that normal stepping needs no sway.
Evidence: `20260905-v6-probe1000-sensor` (videos retained); final remains pending.

A v5 feedback ablation confirms that its mean-policy zero-lag right-turn
no-op is not a normalizer/export bug (mean/export parity exactly zero).
Sampling the trained Gaussian yields steps in three completed trials but
poor yaw/stopping in all; a fourth seed falls. Learned action std is
0.204–0.439 rad, and the normalizer stays unchanged. Exploration can initiate
movement here but is not a valid deployed fix or evidence of proper control.
V6's deterministic turn already improves this case family without adding
deployment noise. Evidence: `20260905-v5-exploration-gap`.

An offline v5 symmetry diagnostic finds approximately mirrored sole hulls
(maximum containment discrepancy 6.5 micrometres) and whole-CoM discrepancy
under 68 micrometres in 30 nearby joint poses, but about 0.188 rad RMS action
disagreement on 945 reflected observations. This is a possible future
regularization diagnostic, not causal proof of drift; no symmetry loss or
inference averaging is enabled in v6. Evidence: `20260905-v5-symmetry-diagnostic`.

Workspace reporting now separates explicit planned transitions, terminal
recorded completed transitions and ambiguous legacy counters. A running
unfinalized zero counter is not displayed as a zero budget. Logged iteration
remains separate from process liveness and acceptance. Current status is
separate from preserved history; the running record is prioritized in the list.

The slow-forward nominal corrected-sensor case has 39/39 qualified swings,
100% alternating landings and normal head posture, but its heading still drifts
about -35 degrees over the 2–13 s window. A yaw-rate MAE pass is not proof of
precise straight-line navigation. Keep this explicit rather than treating its
single-case pass as the whole functional goal.

`HEADING-v1.md` now specifies an additive, explicitly exposed heading-fidelity
check: <=15-degree endpoint and <=20-degree maximum cumulative heading error
over the existing 2..13-second window. It preserves all old scores. Five
synthetic tests cover signed turns through angle wrap, no-op turns, persistent
drift and fail-closed telemetry. The retained v5 current-sensor baseline passes
3/21 heading checks and only **2/21 combined** old-plus-heading checks. This
new check was declared before any v8 candidate; it is not a hidden test or
physical tolerance. The repeated manifest-coverage-hardened run has identical
scores; six tests now include missing/tampered receipt coverage. Evidence:
`20260905-v5-current-sensor-heading-r2` (original result preserved).

An additional **dynamic** native reduced-versus-full-collision replay uses
the exact original float32 actions for nominal slow forward and left turn.
Both 18-second trajectories have byte-identical qpos (maximum difference zero),
no falls and no added non-foot-floor or self-contact pairs at sampled control
boundaries. Raw kinematic/inertial/limit/armature fields and BAM-configured
armature/damping agree. This rules out exploitation of the omitted collision
meshes in those two motions, not all cases or calibrated physical contact.
Evidence: `20260905-v5-full-collision-replay-r2`. The earlier incomplete setup
is separately labeled; no alternate-model result was produced by that attempt.

## Why the earlier demo was accepted incorrectly

The pursuit evaluator rewarded reaching targets, stopping and avoiding gross
falls. It did not require actual alternating sole clearance or reject loaded
sliding and mechanical-stop parking. A reward score and a rendered moving robot
were treated as stronger evidence than they were. Separately, the render CAMERA
pointed into the head, and the native control loop omitted training latency.
Both obscured interpretation. These are different failures, not one cosmetic
problem. Keep target success, gait, timing robustness and physical transfer apart.

## Immutable negative results

- Old pursuit policy: target 4/4, gait 0/4 under the frozen laser-gait battery.
- Wrong-axis gait-v3: stopped/quarantined; physical forward is +X.
- Gait-v4: target 1/4, gait 0/4 at the old zero-lag protocol. Explicit 20/20-ms
  timing allows forward steps, but the stricter walk/turn/stop battery is 0/21.
- Walking-v1: 64×5 smoke passed. Long run intentionally stopped after 8,773,632
  logged completed transitions, plus an unknown partial iteration. Do not read
  its original planned `new_transitions` field as completed work.

V1 checkpoint250 diagnostic (Torch CPU, not selected ONNX candidate):

| Timing / command | Yaw MAE rad/s | Motor saturation | Final stop max speed m/s | Median swing air s |
|---|---:|---:|---:|---:|
| 20/20 ms forward | 0.266 | 7.61% | 0.090 | 0.10 |
| 20/20 ms left turn | 0.244 | 5.97% | 0.093 | 0.10 |
| Zero-lag forward | 0.304 | 8.13% | 0.104 | 0.06 |
| Zero-lag left turn | 0.208 | 4.12% | 0.093 | 0.06 |

All four fail. Nominal turning has sustained bilateral steps and 4.6 cm maximum
XY wander: partial progress, but torque/slip/stop failures make it unacceptable.
The flat event reward paid rapid tapping; v2 shapes landing duration and prices
actual effort, practices stops and increases action-rate cost. See its frozen
`CONTROLLED-v2.md`; evaluator thresholds do not change.

## Model and domain audit

Matched total mass: 0.73724318 kg. All 15 matched link masses agree, and the
largest sorted principal-inertia difference is about 1.00e-11 kg m². This does
not prove full COM/frame/contact or hardware fidelity, but it does not support
changing mass/inertia to improve the animation.

The compiled HOME audit additionally checks all link transforms, local COMs
and full inertia tensors, and the sole vertices composed through Genesis link
frames. Maximum link-position error is about 1.1e-8 m; sole-height error is
below 1.8e-9 m. A real mask mismatch exists: Genesis's implicit plane uses
65535/65535, while the native floor is 1/1, activating three otherwise
self-only body geometries against the Genesis floor.

The new `microduck/walking_ground_env.py` changes only those explicit plane
masks. It is separately versioned, not injected into running v3. Runtime
readback confirms 1/1; an AST regression checks that the rest of the scene
builder is unchanged. A 100-step fixed-input Genesis A/B replay has identical
action and state bytes (maximum state difference 0). The three extra geoms
also stay at least 14.7 mm clear of the floor across all 3,600 v2 probe rows.
This is a latent conformance fix, not an explanation of those failed walks or
a dynamic Genesis-versus-MuJoCo equivalence/physical-transfer claim.
Evidence: `20260905-compiled-home-audit`, `20260905-aligned-home-audit`,
`20260905-v2-floor-mask-activation`, `20260905-floor-paired-replay` under
`receipts/walking/`.

The native reduced walking model has only two floor-capable robot geometries:
the feet. Its non-foot-floor-force check alone is therefore vacuous. The
existing full-collision model has eight additional floor-capable non-foot
meshes, with identical masses, inertias, COMs, joint order and limits. A copied-
state kinematic audit of all 3,600 nominal v2/v3 probe frames finds no omitted
body penetration; minimum non-foot clearance is 14.95 mm. This rules out
hidden floor support in those sampled poses, not all self-collisions or the
dynamic effects of the full model. Retained evidence:
`receipts/walking/20260905-body-clearance-diagnosis/`. Require this geometry
audit and a separately scoped full-collision dynamics check before stronger
model/transfer claims; do not misreport absent collision pairs as observed
contact-free physical behavior.

The v1/v2 cfg phrase "timing variation only" is incomplete: the rigid model and
startup physical DR are nominal, but inherited BAM construction still samples
supply 6.5–8.2 V and voltage-drop resistance 0–0.2 ohm. The unchanged native
evaluator uses 7.35 V / 0 ohm, within this envelope. Preserve the source-bound
cfg/plan bytes; this note corrects their shorthand rather than rewriting history.

## Controlled-v2 result and active posture-v3

V2 smoke passed: 7,680 transitions, 59.7 seconds. The long run was stopped
after 7,962,624 logged transitions plus an unknown partial iteration. Its
checkpoint250 nominal forward probe has 0.04% motor saturation, 0.16 s median
sole air time and 0.0019 m/s final stop speed; stepping/slip/torque/stop gates
pass there. Direction still drifts. Zero-lag turning remains a no-op.

Visual inspection plus qpos exposes a folded neck: v1 mean neck error -86.7°,
v2 -87.8°; mean physical face pitch -80.8° / -83.1°. Both spend all of the
measured moving window more than 45° from horizontal. A fresh HOME render is
correct. This is learned behavior, not a reason to rotate the rendered robot.
The bounded averaged Gaussian head reward sacrifices one joint. V3 adds a
summed, non-saturating command-error cost and separately frozen posture gates
while retaining every old motor gate. See `POSTURE-v3.md`; no acceptance yet.

V3 checkpoint150 diagnostic: nominal head posture now passes (mean absolute
physical face pitch 12.7° forward / 14.7° turn). Both feet step, torque stays
far below saturation, and forward/lateral speed improve. Zero-lag posture is
still outside the declared joint-error gates; yaw tracking still fails in all
four probes, and nominal stopping regresses. Continue the fixed bounded run;
do not select this intermediate checkpoint. On v2's earlier straight command,
net body heading changed 118.8° over the 2–13 s scoring window, so the yaw
failure is not merely harmless periodic wobble.

## V3 final and next tracking correction

The 750-iteration run completed 18,432,000 new transitions in 2,496.7 seconds.
Final checkpoint SHA256 `29eb856aa48bfbb2191e77279f9f90fc8ce82772f815727a7b834e8e4bee41c2`;
normalized ONNX `54a597dd711c451e6d0395dd5752e94f1c94a17ba3df590294f68be700269ffa`.
Real-observation action parity is 1.67e-6 rad.

Result: **posture 21/21, composite 0/21**. Every case has at least 40 qualified
swings per foot. All step/slip/joint/torque gates pass; maximum saturation is
0.024%, versus the 2% limit. Mean absolute face pitch is at most 13.63 degrees.
Yaw tracking fails all 21, stopping 11 and lateral speed 9. The viewed final
forward clip shows the robot gradually turning despite a straight command.
These are genuine control failures, not rendering artifacts or accepted gait.

The training-engine diagnostic also fails yaw (0.28–0.49 rad/s MAE), but all
four Genesis stops settle below 0.0016 m/s. A native ablation of only the
initial motor FIFO history (HOME versus first target) does not fix turn/stop.
All 18,900 final poses clear the eight full-CAD non-foot floor meshes by at
least 14.27 mm; no body-through-floor support explains the result.

V5 therefore adds a non-saturating command error cost, not another posture or
mass fix. Its frozen plan is `TRACKING-v5.md`; fresh visible headings and all
old regressions keep numerical gates unchanged. No acceptance before results.
Evidence: `20260905-v3-final`, `20260905-v3-training-complete`,
`20260905-v3-smoke-complete`, `20260905-v3-genesis-response`,
`20260905-v3-motor-startup`, `20260905-v3-final-body-clearance` under
`receipts/walking/`.

## Contact-default mismatch found by fixed-action replay

The original saved v3 float32 action array was replayed byte-identically in
both engines, with the same HOME motor history, voltage, floor masks and
200-Hz actuator loop. Free-flight states stay close, but at the first impact
(45 ms) Genesis loads sum to about 59.96 N versus native 32.28 N. Root position
differs by 0.95 mm immediately and exceeds 1 mm at 50 ms. Static geometry and
pure actuator-equation tests had not exercised this contact response.

Genesis's MJCF importer replaces omitted solver timing with its own default;
our scene left that at 10 ms, whereas the native compiled model uses 20 ms.
`microduck/walking_contact_env.py` explicitly uses the native 20-ms value.
An AST test proves this is the only scene change on the aligned-floor base.
Runtime readback matches all seven floor/foot solver parameters. With the same
action bytes, first-impact load becomes 31.66 N and root difference 0.049 mm;
the first 1-mm difference moves to 125 ms. This is a real contact-default fix,
not an outcome-fitted mass or action correction.

It is NOT complete dynamic agreement: five-second maximum root separation is
still about 19 cm. The separate solver-configuration gap remains to inspect.
Keep current v5 training immutable; do not silently insert a different contact
model halfway through its run. The contact-aligned version has not trained or
accepted a policy. Evidence: `20260905-v3-fixed-cross-engine` and
`20260905-v3-contact-aligned-replay` under `receipts/walking/`.

## Solver and sensor phase: separate measured issues

Copying native Euler/Newton settings and enabling Genesis's MuJoCo-compatible
mode does not resolve five-second dynamics divergence. That mode also changes
the timestamp of derived link fields: `get_pos()` is pre-integration while raw
`get_qpos()` is current. A corrected raw-state replay retains the negative
result (first 1-mm root difference at 115 ms; maximum five-second difference
20.8 cm). Do not infer physical alignment from a compatibility flag or compare
states from different ticks. These variants are diagnostics, not trained models.
Evidence: `20260905-v3-solver-aligned-replay` and
`20260905-v3-solver-qstate-replay`.

The native controller has a separate timestamp bug: after `mj_step`, IMU
sensors still describe the pre-integration state while joints use current
qpos/qvel. Declared 20-ms IMU delay was actually 25 ms; declared zero was 5 ms.
`ConsistentSensorWalkingWorld` in `experiments/walking/sensor_world.py` samples
the IMU after `mj_forward` on a **copied** data object, never on physical state.
Tests verify physical integration/constraint arrays and friction are unchanged,
and identical fixed actions produce byte-identical trajectories over 50 steps.

With the same v3 final policy in a closed-loop nominal left-turn diagnostic,
fresh IMU sampling changes final stop max speed from 0.09498 to 0.001634 m/s
and yaw from 0.9538 to 0.0272 rad/s. Yaw tracking still fails. Across the full
fresh-heading bank, corrected-sensor v3 remains **0/21, posture 21/21**: yaw
fails 21, lateral velocity 9, stopping 6, turn wander 4. This is a real feedback
bug fix, not successful walking or calibrated real sensor latency. The new
sensor evaluator is separately frozen; original results stay immutable.
Evidence: `20260905-v3-sensor-phase`, `20260905-v3-current-sensor-baseline`.

## V5 in-progress diagnostic: no candidate accepted

The bounded v5 run is still active and its source is unchanged. Its smoke
completed 7,680 transitions in 62.0 seconds. Checkpoint150 improves command
response/stopping but fails all four diagnostic cases: left hip pitch reaches
its -90-degree actual stop, and stopping torso tilt reaches 22–24 degrees.
Head posture passes all four. Current-state IMU sampling does not cure this
regression (4/4 fail actual margin, yaw and stop tilt). This is real joint
behavior, not a rendering error, and is caught by unchanged independent gates.
Finish the fixed bounded run before interpreting its final-only candidate.
Evidence: `20260905-v5-smoke-complete`, `20260905-v5-probe150-posture`,
`20260905-v5-probe150-sensor`.

The same checkpoint150 also parks its left hip pitch at approximately -90
degrees in Genesis CPU (nominal and zero-lag forward), with stop tilt 21–22
degrees. Nominal yaw error is 0.28–0.31 rad/s. The zero-lag left turn falls
at 2.64 seconds. Thus this posture shortcut is present in the training engine;
sensor sampling or a rendering change cannot explain it away. The actual-
joint boundary penalty and consecutive hard-stop termination already exist,
but other positive objectives remain payable in invalid poses. Training uses
sampled Gaussian actions (left-hip-pitch standard deviation 0.279 rad at this
checkpoint), whereas deployment uses the deterministic mean. Long stochastic
training episodes are not evidence that the deployed controller avoids joint
stops. This is not yet an isolated claim that exploration noise caused the
shortcut. Evidence: `20260905-v5-probe150-genesis`. The full regression suite,
including copied-state sensor and contact-default tests, passes in
`/private/tmp/walking-v5-full-tests-sensor-contact.log` (retain with final run).

## HOME targets are not a standing controller

A separate constant-zero-action diagnostic (HOME servo targets, not policy
assistance) falls forward in 1.16–1.34 seconds from five initial trunk tilts
of 0 or +/-0.02 rad. Actual joints retain at least 0.288 rad margin. The
initial center of mass is within the geometric foot bounds, but position
targets with the modeled actuator compliance do not maintain equilibrium.
Do not use nominal HOME as an assumed stable stop or impose exact HOME leg
tracking as the solution. V3's measured balanced stops demonstrate that valid
standing is achievable with active control. Evidence:
`receipts/walking/20260905-home-equilibrium/`. This is a model diagnostic,
not a claim that the real robot has the same uncalibrated standing response.

Pollen's [walking reference](https://pollen-robotics.com/microduck/) is visual
context only, not joint/contact ground truth or an executed third-party policy.

Sources: `receipts/walking/20260905-timing-diagnosis/`,
`20260905-v4-baseline/`, `20260905-v1-stopped/`, and the retained intermediate
probe/smokes. Current queue remains `TRAINING_ACTUALIZATION.md`.
