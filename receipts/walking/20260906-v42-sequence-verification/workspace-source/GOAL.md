# GOAL

## Work Mode

Work directly in one Codex task. Do not create Executor/Reviewer/Manager
cycles, spawn review tasks, or run an autonomous goal loop. Historical role
records are evidence only.

## Active Mission

Turn the working Genesis Metal/MPS pipeline into a reproducible,
backend-conformant, independently evaluated policy-production system by
advancing `TRAINING_ACTUALIZATION.md` in order. Preserve the 61D observation,
14D action order, 50 Hz unfiltered control loop, normalized ONNX export, exact
model variants, and BAM behavior boundaries. Promote only evidence-backed proof
classes; reward movement or a plausible rollout is never task success.

## Current Milestone

Solve command-conditioned walking, turning and stopping across explicit timing profiles

## Current Status

**September 6 sequence completed through failed prerequisite gates.** V31–V40
isolate a collision-hull import discrepancy: retaining authored hulls reduces
sampled support mismatch from up to .654 mm to 22 nm, but softer robot-level
cross-engine agreement remains unresolved. V38 slower STOP is rejected.
Native standing V41/V42 each complete 384,000 transitions; V42 preserves all
63 flat gates but passes only 1/4 downhill/composition sessions and 3/14 exposed
surface sessions (11/28 windows). Its first long composition falls at 140.16 s;
both downhill sessions fall. Keep V30 and original V21/V15 actors. Fresh terrain
and protected final banks remain unopened; physical calibration stays unmet.

All 19 source freezes and 15 diagnostic/evaluation manifests verify; training
finals, reset-state coverage and finite learning telemetry are retained. 135
workspace tests and five focused tests pass. Compressed traces are inspectable
with bounded reads and stored-byte manifest checks. All local jobs from this
sequence are complete. Next measure coverage of candidate-induced handoff states
before another frozen refinement. Report: `experiments/walking/SEQUENCE-RESULTS-v41.md`.

**V30 closes the limited heading improvement; broad surfaces remain unmet
(September 6).** Exact V21/V15 actors with the new motion-established course
reference and .80-rad/s correction headroom pass all 21+42 original flat gates
and both complete 180-second compositions. Heading endpoints improve from
64.04/86.44 degrees to 6.24/8.95; maxima are 15.88/14.45. STOP remains zero,
physical dynamics and gates unchanged. The .05-rad/s command extrapolation is
explicit local development, not raw-policy learning or physical acceptance.
Both downhill sessions still fall. Final V30 surface result is 5/14 sessions,
12/28 windows with five falls; no new surface family fully passes.

Three full public-surface refinements completed 18,432,000 transitions. Under
fixed V24 heading, baseline is 5/14; V25 walker 1/14, V25 stander isolation 5/14,
full V25 pair 4/14, conservative V27 walker 5/14. All new actors are rejected
for promotion. Public studies/ISRD were collected with provenance; incompatible
features and static means were not invented into Ducky calibration. Passive
numeric checks pass 24/24 and primitive cross-engine checks 8/8; robot-level
identical-action comparisons pass only 2/5 under 2-mm/5-degree limits, with up
to 4.09-mm discrepancy. Match contact representations and applied dynamics
before further broad surface training; physical calibration remains open.

V24/V28 heading regressions and V29's arithmetic-induced endurance fall remain
retained. V30 restores exact nonsaturating float32 behavior: all 24 V28 diagnostic
action files and 19,382 qpos/action rows match, including negative downhill cases.
The disk-interrupted V30 run is retained separately; its unchanged completed
retry matches all 32 previously completed action files. 132 workspace and 13
focused tests pass. All local runs are complete; no hardware, paid compute,
policy activation or library admission. See `experiments/walking/PUBLIC-SURFACES-RESULTS.md`.


**V23 complete; locomotion remains unaccepted.** Terrain passes 4/14 sessions
including controls: 2/2 flat and 2/2 uphill; all other terrain buckets 0/2.
That is 2/12 new-terrain sessions and 9/28 windows. Five sessions fall; four later
windows are explicit unrun failures. Four uninterrupted 180-second walks pass
nominal/combined physics gates and whole-session heading. Both 180-second
compositions pass their short windows but fail the additive cumulative-heading
audit (64.04/86.44 degrees endpoint error). Thus complete-audit endurance is 4/6,
while original V23 window scores remain 24/24. The STOP intervals consistently
add yaw; downhill failures occur just after switching to standing. Next isolate
heading preservation and standing transitions, including slopes, with a newly
frozen protocol; no automatic training extension. See `experiments/walking/V23-RESULTS.md`.

Physical calibration intake is implemented and tested, but **real Ducky-specific
measurements are missing** from the inspected corpora. The unfilled bundle
returns `blocked_inputs`; no values were fitted/applied. Collection schema and
separate remaining dynamics stages are in `experiments/walking/PHYSICAL-CALIBRATION-v1.md`.
At V23 closure, 132 workspace and 16 focused tests passed; its sources/receipts
are retained. That stage finished its compute without hardware, paid compute,
policy activation or library admission.

Retained motor-policy baseline: **V21 FINAL passed all 63 exposed native gates** — original
21/21 and continuous repeated 42/42. No falls, internal bracing or excessive
body penetration; every task, torque, joint, posture and heading gate passes.
Long-delay forward20 yaw MAE is .16366 (V19 .21639), arc-right .14331
(V19 .20257), with the unchanged .20 limit. Real-observation ONNX/Torch error
is at most 1.79e-6 rad. All 63 actual case videos and raw traces are retained.

V20 first reproduced both residual failures in Genesis with all 2,700 actor
inputs and 10,800 delayed targets checked. V21 then doubled only the moving
instantaneous yaw penalty from exact V18 FINAL initialization. The single
1024x250 run completed 6,144,000 transitions in 1,100.319 s; FINAL249 SHA
`7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322`.
Actor/telemetry and every logged scalar are finite; all 149 sources match.
All 56 timing combinations are materialized in initial/final snapshots.
Permanent stdout, source capture, final checkpoint and learning curves are
retained in `receipts/walking/20260906-v21-training-complete`.

All 15 imported body masses/COM/inertias match the authored model within
float32 tolerances (total mass .737243 kg); this is import consistency, not
physical calibration. Separate final-standing posture checks pass all original
21 cases. Four reward/contract tests and 131 workspace tests pass.

**V22 new physical development passed 24/24**, frozen only after 63/63.
Nominal, .6x sliding friction, 1.1x mass+inertia and combined profiles each pass
6/6 new command/pose/repeated windows. Actual runtime mass is .737243 or
.810967 kg; contact friction is measured as 1.0 or .6. Parameter arrays/hashes
and all 24 videos are retained. Three application/reset/isolation tests pass.
Separate final-standing posture audits also pass all 87 exposed windows.

The full simulation regression with pinned BAM completed with no failures.
One legacy ONNX check is not applicable without its old checkpoint; V21
ONNX/Torch agreement is separately verified on all 78,300 control observations. All 87 windows
are exposed development, not broad generalization or physical acceptance.
Next prerequisites: independent terrain/layout families, verified broader
randomized learning, longer endurance/dropout/composition, timestep/solver
validation as applicable, and held-out measurement-based calibration. No new
training is scheduled; freeze the next scoped experiment before execution.
No protected bank, library admission, policy activation or physical authority.

Retained baseline evidence follows; it does not describe the active process.

Proper walking is **not yet accepted**. Latest V18 FINAL passes **18/21**
original cases. All 21 avoid falls, sustained internal body bracing and excess
body penetration; all heading endpoints and standing posture pass. Three
long-delay cases still exceed yaw-rate MAE .20 rad/s: forward12 .20701,
forward20 .21839, arc-right .21617. Keep these failures, not a rounded pass.

Completed: `experiments/walking/UNBRACED-WALKING-v18.md`, retained negative. Bounded
`walking-20260906-v18` completed 6,144,000 transitions in 1,398.282 s; FINAL249
SHA `922bd58e2ad2d6657dc7797f28b638f8294ab57ab9963c458569130b4d13e70b`.
All 140 source files match. Original run record, all checkpoints and TensorBoard
iterations 0–249 are intact; temporary training stdout was unavailable at the
follow-up and is not reconstructed. No trainer or evaluator remains active.
The 42 exposed repeated-start windows are **41/42**, no falls and every
internal-load gate passes. Arc-left117/448 at motor25/sensor20, first startup,
has one 1.04004-mm battery/leg penetration frame at 1.44 s versus 1 mm.
Overall all 63 cases avoid falls and sustained internal loading, but three
yaw-rate failures and one geometric failure remain. Do not weaken the gates.
V19 fixed-weight course-correction diagnostic is **5/7**, versus **3/7** for
the same selected V18 windows. Low-pass only the outer heading correction,
not motor actions: long-delay forward12 and the failing arc-left startup
now pass. Long-delay forward20 yaw MAE .21639 and arc-right .20257 still
exceed .20 rad/s. All seven avoid falls and pass heading/geometry/load gates.
This is a retained partial improvement, not full-bank or walking acceptance.
See `experiments/walking/FILTERED-HEADING-v19.md` and its diagnostic receipt.
The pre-intervention traces show mainly 3–6-Hz yaw motion with small mean
error; controller correlation does not prove causality. The required paired
Genesis comparison is now complete as V20; V21 above is the selected bounded
reward intervention. No gain sweep is active.
No new closed bank, physical or pursuit acceptance.

Recipe erratum: frozen V18 prose says 5% standing commands, but the inherited
V2 sampler and retained run config both specify **25% stop** (40% forward,
25% turn, 10% arc). Frozen sources/artifacts are unchanged; a new deterministic
contract regression checks the effective sampler and its metadata.
All nine focused tests and 122 workspace tests pass. The V19 receipt audit
verifies all 165 files, 147 source bindings and 6,300 complete trajectory rows;
no full simulation regression or walking admission is implied.

Owner direction: build a capable, context-aware behavior library. The roadmap
is `docs/workspace/BEHAVIOR_LIBRARY.md`; ordered future work is B1 in
`TRAINING_ACTUALIZATION.md`. Require perception, bounded execution, safe
transitions and explicit capability availability. Walking remains the one
active prerequisite; no catalog/planner or new behavior is claimed implemented.

Mandatory owner requirement for EVERY behavior: thorough independent tests,
effective domain randomization, unseen-environment generalization and validated
physics. `docs/workspace/BEHAVIOR_VALIDATION.md` defines operating envelopes,
factor coverage, split/repeat/uncertainty rules, transitions and calibration
evidence. New v2 behavior drafts require that six-part quality plan; the checker
is planning lint, not capability admission. Existing walking remains unaccepted
and physics/transfer uncalibrated. Do not turn these requirements into claims
that the tests, broad randomization or physical validation have already happened.
Earlier quality-plan tooling verification: seven new regressions and all 129
workspace tests passed, zero skips/errors. That requirements-only update did
not change policies or simulators. V21 above is the subsequent training work;
the retained V19 result remains unchanged.

User-requested actual video: `outputs/walking-progress-20260906/duck-progress.mp4`
(54 s, 1x). Complete latest walk/stop and turn/stop examples, then a labeled
failing long-delay stress case. No generated robot frames. Local video link:
`http://127.0.0.1:8950/duck-progress.mp4`. That video remains V18, not V19.
Duck Lab's source-bound focus is the V18 long-delay forward20 failure.

## Historical Walking Evidence

Snapshots below are retained history, not active instructions. The current
status immediately above and the ordered task list govern the next action.

Core collision coverage is corrected in the versioned v11 model: the prior
policy's legs intersected actual battery CAD, hidden by the reduced model.
The new model preserves mass, joints and visuals; it adds body contacts and
restores support/leg collision masks. All 21 old v9 traces fail the new 1-mm
self-interference rejection. The corrected-model CLOSED-LOOP baseline has
no falls, normal head/stops and self-contact 21/21; motor/posture 17/21,
heading 7/21, complete result 6/21. Fixed-action fall diagnostics are not
closed-loop scores. Actual full-bank v11 baseline videos are retained.

Explicit v12 IMU heading COMMAND feedback (same v9 weights, unfiltered motor
outputs) raises combined performance to 17/21, heading 21/21. This is a
controller-plus-actor result, not better raw-policy tracking. Four 30/20-ms
forward/arc cases still exceed the unchanged yaw-rate MAE limit: .209–.225
versus .20 rad/s. No falls or other motor/head/stop/self-contact failures.
The fresh development bank remains closed; no physical acceptance.

Active: `PERSISTENT-CONTACT-v13.md`. Hold the same randomized device delays
through each episode on the corrected contact model. Same v9 reward/actions;
fixed v12 heading servo is evaluated separately, never injected into training.
30 focused correction tests and 115 workspace tests pass. The 64x5 smoke
completed 7,680 transitions in 82.12 s; all 123 source/mesh files match.
The bounded 1024x750 local run `walking-20260905-v13` completed all 18,432,000
new transitions in 4,214.939 s including setup and concurrent diagnostics.
Its declared FINAL is `model_749.pt`, SHA-256
`f31d47a5343b1283a1bbd28c2f7efb78f95ddd6940554b9c755b73d337c2b7f8`;
all 123 live/captured source files match and complete training is retained.
Final ONNX evaluation is complete and rejected: controller 20/21, raw actor
4/21 combined. Long-30-20ms forward20 falls at 14.98 s, 1.98 s after STOP;
both user/policy commands are zero. Heading passes all 21 with the controller.
Old reduced-model sensitivity results are 2/21, 1/21 and 1/21, not acceptance
of the corrected model. All five final protocols and actual videos are retained.
V11 model-only training and the old v10 draft were not run. No policy is
accepted yet; no trainer remains active.

Completed diagnosis: `STAND-SWITCH-v14.md`. Exact replay exposes a new
blind spot: no deep penetration does not mean no internal body bracing.
V13 nominal slow-forward stop has ~14.93 N mean summed internal normal load,
with the largest pair >1 N at every settled-stop sample. Three moving
intervals have zero internal load. V5 FINAL has zero load in all phases of
the same three diagnostic cases. This is not proof that bracing caused the
V13 fall, or that V5 is an accepted standing controller.
V14 freezes an additive 200-Hz sustained-self-load rejection gate and tests
the exact V5 FINAL for zero commands / V13 FINAL for nonzero commands, with
unchanged V12 heading control and raw unfiltered actions. Eight unit tests
pass. The unchanged V13 baseline is 0/21 under the additive load gate;
all 18,749 original poses and all 21 action files remain byte-identical.
V14 pair: **13/21 combined; 21/21 heading, geometry and unbraced load; no
falls**. All 75,600 physics samples have zero internal load. Only eight stop
tilts fail, 15.0712–16.5418 degrees against 15. Actual stop footage inspected.

Active: `STANDING-v15.md`. Refine only the V5-initialized standing actor on
zero commands with the existing V9 upright/head objective and an additive
internal-force gate/cost. Preserve V13 FINAL walking weights, complete model,
persistent delays and the fixed command-only switch. Five reward tests pass;
120 workspace tests pass (one earlier fixture-setup error fixed). Frozen
64x5 smoke completed 7,680 transitions in 83.18 s, with finite rewards/loads
and zero commands verified. All 118 bound sources match. Bounded 1024x250
standing training completed as `standing-20260906-v15`: all 6,144,000 new
transitions in 1,416.893 s including startup. Declared FINAL249 SHA-256 is
`acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46`.
Complete training and all 118 matching source files are retained. No trainer
remains active. Final paired ONNX evaluation/video is **21/21 across every
motor/posture, heading, geometry and sustained-load gate**, with no falls.
Worst stop tilt 6.7963 degrees, speed .0034783 m/s, moving yaw MAE .177884
rad/s and heading endpoint 2.3443 degrees. One case has a brief 20-ms internal
contact (peak 5.299 N); there is no sustained bracing, not a claim of zero
contact in all cases. Standing ONNX SHA is
`2fddc9a9bc4ff9a17a34af51215a31c43503cbe68a1b815a97b3042abf248db8`.
The full regression suite passed (official-artifact and legacy-export
non-applicability remain explicit); the expanded-reader 120 workspace tests
also passed. Fresh development is **33/42**, therefore V15 is rejected overall:
four fast-forward cases fall after STOP, four subsequent windows cannot run,
and one second-cycle right-turn startup has sustained internal body loading.
All footage and loads are retained. The 42 windows are now exposed development,
not a closed or hidden bank. No pursuit integration or physical acceptance.

Completed diagnostics: `COMMAND-RAMP-DIAGNOSTIC-v17.md`. V16 command slew fixes
the tested fast-forward transitions but only passes 5/6 diagnostic windows;
second-cycle right-turn startup still braces for 245 ms. Test one gentler
yaw acceleration (.75 rather than 2.5 rad/s^2), with translational slew,
both exact ONNX actors, physics and every gate fixed. Full 21+42 regression
and newly frozen development remain required. V17 is rejected at 4/6: both
right-turn startups brace (240 and 420 ms continuous), so gentler yaw is not
the repair. Keep the useful V16 stopping ramp, not the V17 yaw change.

Historical V18 training snapshot (now completed; current evidence is above):
`UNBRACED-WALKING-v18.md` applied the V15 internal-load objective to
V13 walking, leaving command sampling/reset/model/timing/actions unchanged.
Warm-start exact V13 FINAL; bounded seed26090618, LR2e-4, 64x5 smoke then
1024x250 (6,144,000 transitions), FINAL249 only. Three focused tests pass.
Preflight r1 rejected a diagnostic using the wrong receipt schema before any
physics/training; sources/error retained. r2 checks the diagnostic's real
required files without promoting its proof class. Smoke completed 7,680
transitions in 83.06 s; all 140 source files match. Full 1024x250 training
`walking-20260906-v18` was running locally at that snapshot and is now complete.
Evaluate with fixed V15 standing and V16 ramp against all 21+42 exposed cases.
122 workspace tests pass. The read-only viewer now focuses on the actual
V15 fresh fast-forward stop fall, not an older passing preview.

V15 intermediate50 is diagnosis only: all three fixed problem cases pass
every gate with the unchanged V13 walking actor. Stop tilt is 6.61–7.07
degrees with zero internal load, versus the earlier 15–16.5-degree stops.
The long-delay fast-forward yaw MAE is .19790 against .20, so margin is thin.
Keep the bounded final249 requirement; no checkpoint selection or fresh-bank
opening follows this small Torch diagnostic. Receipt:
`receipts/walking/20260906-v15-standing-intermediate50/`.

V13 intermediate150 diagnosis is 21/21 for each motor/posture, cumulative
heading and self-contact gate, and 21/21 combined with the fixed v12 command
controller. Worst moving yaw MAE .1674 rad/s (limit .20); all cases alternate
qualified foot landings and stop upright. Actual stepping/braking videos were
inspected. This is normalized Torch diagnostic evidence, NOT final ONNX or
checkpoint selection. Retained at `20260905-v13-intermediate150` under walking
receipts; the fixed run subsequently completed and its final was rejected above.
The same intermediate without the heading servo is 21/21 motor/posture and
self-contact but only 9/21 heading/combined; the controller is still required.
Intermediate500 regresses to 20/21 combined: long-delay arc-left yaw MAE
.21777 rad/s exceeds .20. All heading, body contact, head, stop, joint, torque
and step/slip checks still pass. Retain this negative; do not select150 or
weaken the yaw gate. Neither intermediate tested the later self-load gate.

### Retained v9 terminal result and diagnosis

V9 FINAL is rejected. All 18,432,000 new transitions completed; current-sensor
native evaluation is 12/21 motor/posture, 7/21 heading, only 5/21 combined,
with five falls and nine joint-margin failures. Head posture is normal in all
21. The complete Genesis diagnostic has no falls and only 12/21 heading;
native Torch also fails, ruling out an ONNX-only explanation.

At that earlier stage, the next task was to isolate the collision-model gap
before more training. Exact
float32 action replay of nominal slow forward finishes in the reduced model
but falls at 1.94 s with the bundled full-collision model. Those models change
both geometry availability AND existing leg contact masks; neither is assumed
physical truth. The earlier floor-clearance checks do not test self-collision.
See `receipts/walking/20260905-v9-full-collision-replay-r2/` and `RESULTS.md`.
The conditional v10 timing-only proposal was paused. This paragraph describes
the retained v9 stage, not current process activity; current v13 status is above.
No physical transfer is claimed.

### Retained v8/v9 development history

V8 FINAL is rejected: 0/21 in all three complete protocols. It repairs trunk
stopping tilt (current-sensor 6.30–6.77 degrees), falls and actual motor/step
failures, but every case tips the head far back at stop. Current-sensor also
has six yaw-rate failures; separate heading is 9/21, combined 0/21. Actual
videos and Genesis playback confirm the head regression. The earlier 150/500
checkpoint posture improvements were not selected and are not current proof.

Active correction: `experiments/walking/VIABILITY-v9.md`. Condition positive
reward on acceptable head/trunk posture so good speed cannot simply pay for
bad posture; retain all penalties and separately price persistent yaw bias.
No model, physics, action/observation, reset, timing or threshold changes.
Reward accounting passes 2,000 actual-state samples/183 landing events with
maximum error 5.4e-6. Fifty focused tests and the process-isolated full suite
pass. The 64x5 smoke completed 7,680 transitions in 94.6 seconds; the bounded
1024x750 run completed 18,432,000 transitions in 3,913.2 seconds including
setup and concurrent work. All 35 live/captured sources match. Retained final
checkpoint is `c79e02bc00dabca146b83592582926fc2053114cc5e44cdf822f95aa8ff8fb17`.
Its three complete final ONNX protocols and videos are retained and rejected.

V9 intermediate150: 17/21 motor/posture, 6/21 cumulative heading and 6/21
combined. Head, actual joint/torque/step/slip and quiet upright stopping pass
all 21; four moving-yaw failures remain. Viewed footage shows real foot lifts
and normal head/stop posture. All 18,900 full-CAD poses clear the floor by at
least 14.29 mm. This is diagnostic, not final selection or acceptance.
The conditional persistent-delay proposal in `PERSISTENT-TIMING-v10.md`
is not active and cannot replace evaluating v9 FINAL.
Intermediate500 is 16/21 motor/posture, 9/21 heading and 7/21 combined, but
30/20-ms fast forward now falls 0.88 s after the stop command. Head remains
normal. Preserve this braking regression; the earlier better stop is not
selected and v9 FINAL still requires the complete unchanged battery.

Proper walking is not solved yet. V6 completed 36,864,000 transitions and
fails all 21 cases in each complete protocol. Current-sensor: 20 stops lean
26.6–34.7 degrees, seven yaw-rate failures, one fast-forward fall at the longest
delay. Its separate heading check is 2/21, zero combined. All negatives and
final videos are retained. The stopping lean also occurs in Genesis.

Latest completed baseline v5 genuinely steps with a normal head and no actual
joint-stop parking: 6/21 old, 5/21 new-heading legacy clock, 6/21 current-sensor
cases pass. Its additional cumulative-heading check leaves only 2/21 combined
passes. Old scores are preserved; drift is not accepted as straight walking.
Full-CAD clearance and export parity pass, not physical transfer.

`BALANCE-v8.md` completed 24,576,000 new transitions in 4,179.3 seconds;
its exact final and all 29 training source files are retained. Full-CAD
clearance passes and normalized real-observation parity is <=1.67e-6 rad.
Active visible failure: `receipts/walking/20260905-v9-current-sensor/`.
Earlier partially passing baseline: `20260905-v5-current-sensor`.
Same original motor/posture thresholds; no hidden or hardware acceptance.

## Historical context

Historical v3-to-v5 diagnosis:
V3 completed 18,432,000 transitions. Its final result is posture 21/21 but
composite 0/21: yaw tracking fails all 21, stopping 11 and lateral speed 9.
All independent step/slip/joint/torque gates pass; no hidden body penetration
in 18,900 full-CAD clearance checks. The current correction is
`experiments/walking/TRACKING-v5.md`: non-saturating command-error cost,
unchanged motor/posture thresholds, fresh visible headings plus old regressions,
and the separately tested floor-mask conformance fix. Local 64×5 smoke completed
7,680 transitions; the bounded 1024×750 run completed from the retained v3 FINAL checkpoint. No full acceptance
or physical authority is claimed. The lineage below is retained diagnosis.
Two independent conformance defects were isolated while v5 stayed immutable:
Genesis contact time constant 10 versus native 20 ms, and native IMU samples
one 5-ms physics tick older than the declared sensor delay. Separate versioned
corrections improve first impact and one v3 turn/stop respectively, not overall
walking acceptance. Current-sensor v3 baseline remains 0/21. V5 checkpoint150
is diagnosis only: posture 4/4, but all four fail yaw, actual joint margin and
stop tilt; nominal stops park left_hip_pitch at -90 degrees and lean about 22.
Do not mistake this for a camera problem or promote that intermediate policy.
The fresh command-only timing probe finds that the old v4 policy steps in
Genesis and in MuJoCo with the existing training delays, but not in the old
zero-lag evaluator. At 20/20-ms motor/sensor timing it makes 33/33 valid swings
at +0.12 m/s; pure turns still fail. This is a versioned feedback ablation,
not hardware calibration or a rewrite of the old negative receipts.
See `experiments/walking/PLAN.md`: command-only training with dense sole-lift
feedback, timing range 0–30/0–20 ms, unchanged model/BAM/action interface.
The v1 64×5 smoke passed, but the long run was intentionally stopped after
8,773,632 logged completed transitions plus an unknown partial iteration.
Checkpoint250 stepped and turned in the nominal timing diagnostic, but all
four probes failed on torque/slip/stopping; zero-lag remained worse. Retained
terminal/source/checkpoint evidence: `receipts/walking/20260905-v1-stopped/`.
The old v4 policy also fails all 21 stricter walking-v1 suite cases.

`experiments/walking/CONTROLLED-v2.md` freezes a new controlled-motion reward:
air-duration-shaped landing credit, all-200-Hz-substep near-limit torque cost,
more stop practice and action-rate cost. No model, action filter or evaluator
threshold changes. The new 64×5 smoke passed (7,680 transitions, 59.7 s).
V2 was deliberately stopped after 7,962,624 logged transitions plus an unknown
partial iteration. Its nominal checkpoint250 probe improves actual motor
saturation from 7.6% to 0.04%, sole-air duration to 0.16 s, loaded slip and
stopping (0.0019 m/s), but still drifts; zero-lag turning is a no-op. It also
folds the neck about 88 degrees away from the neutral command, facing down
about 83 degrees. The HOME model itself has normal head orientation.

`experiments/walking/POSTURE-v3.md` adds a non-saturating per-head-joint error
cost and separately frozen additive posture rejection. Every old motor gate
remains unchanged. The v3 64×5 smoke passed (7,680 transitions, 60.1 s).
The bounded 1,024×750 local run completed at `logs/walking-20260905-v3/`
from the named v2 diagnostic initialization; final-only candidate.
No paid compute, hardware or hidden-bank evaluation. Proper walking is not
yet accepted. Its final evaluation retains every old motor gate and the new
posture gate. A separate Genesis response diagnostic also fails yaw, but stops
below 0.0016 m/s; native startup-history ablation does not cure the native turn/
stop failure. Retained final and training: `receipts/walking/20260905-v3-final/`
and `20260905-v3-training-complete/`. Full regression
tests with pinned BAM and new body-clearance diagnostic tests pass. See
`experiments/walking/RESULTS.md` and retained v1/v2 attempts.

Previous result: the owner observed abnormal
walking in the live demo. Previous pass counts below measure target proximity,
stopping and gross falls only; they do not establish walking quality or transfer.
The audit measured contact/slip, stepping, face/command frames and actuator/model
alignment. Preserve the existing negative and positive
target-only receipts without rewriting their historical classifiers.

The current audit finds hip-yaw stop parking (both joints throughout the
post-startup 16-second sample), only one qualifying left-foot swing and no
right-foot swing, and loaded-contact slipping. Physical head/mouth forward is
**+X**; the legacy render CAMERA points inward (-X). The initial opposite-axis
v3 diagnosis/training was rejected and stopped, with full source/terminal
evidence in `receipts/laser-gait/20260905-v3-quarantined-final/`.
Current correction is **gait-v4**, preserving +X steering and physics, adding
actual-joint-stop/stepping objectives plus independent gait rejection. The
render-camera-only v2 adapter aligns optical forward/image-up to the physical
site. The 64×5 v4 smoke and bounded 1024×600 local run completed at
`logs/laser-gait-20260905-v4/`: 14,745,600 new transitions. The final checkpoint
passes only 1/4 target cases and **0/4 gait / 0/4 combined cases**, versus the
old policy's 4/4 target / 0/4 gait cases under the same frozen evaluator.
Actual joint-stop occupancy fell from 100% to 0%, but the candidate makes no
qualifying bilateral swings. It is rejected, not selected. That gait-v4 training
is finished; the fresh reserved bank remains closed. See
`experiments/laser/GAIT_DIAGNOSIS.md` and `receipts/laser-gait/`.

Historical target-only result: local
400-iteration DR training and a separate 250-iteration turn-reward correction
completed 15,974,400 new transitions. The selected policy is
`7d634c6f64178f1bbb8cbe3a4129418ad8661dad6abfbaae3ac533244c3d0fed`.
It passes all three nominal dynamic routes, 5/6 randomized development cases,
and 11/12 reserved development cases (old policy: 0/3, 1/6, 2/12 respectively),
while retaining 6/6 original laser cases. Both retargeting development cases
acquire all six waypoints. One development and one reserved case fall early;
do not call this full robustness. Thresholds and routes were not relaxed.

The browser playground supports live drag/keyboard control, looping waypoint
jumps, circles, figure eights, dot loss/reappearance, and randomized flat-ground
trials. See `experiments/laser/DYNAMIC_BUILD.md` and `receipts/laser-dynamic/`.
Priority: establish measured basic walking, turning and stopping before
reintroducing laser pursuit and domain randomization. Then isolate the development
startup fall at seed 75003; keep reserved seed
75109 as a terminal negative, not tuning data. Camera integration remains
separate: target coordinates are still privileged. The frozen legacy camera
points inward; the versioned render-only adapter corrects its orientation without
changing policy actions or physics. No canonical held-out or physical acceptance.

- M5 is blocked after four distinct Brev provider/type provisioning failures.
- M6 has an accepted deterministic 65-file bundle, but the official candidate
  is missing 8 of 10 roles and the community candidate is missing 4 of 10.
- Five legacy files remain quarantined.
- The official request was posted as Pollen Robotics GitHub issue 40; its
  checksummed contact receipt records the exact body, identity, destination,
  and timestamp. No role is closed and a response is pending.
- A new first-party walking policy was trained from scratch at public seed
  `26090401` for 2,457,600 transitions, exported with a separately recorded
  normalizer, and evaluated twice on frozen visible-development cases. The two
  semantic trajectories match exactly; this is pipeline evidence, not gait
  success or held-out acceptance.
- The community request remains unsent. The prior recorded Brev inventory was
  empty; this local-only gait task did not use Brev. No third-party
  policy action, paid compute, publication, activation, or physical action is
  authorized or in progress. The completed local first-party run was explicitly
  authorized development work.
- Third-party artifact resolution still waits for immutable upstream inputs.
  Local first-party development may continue under the versioned development
  amendment; held-out, publication, activation, and hardware gates remain shut.

## Task List

`TRAINING_ACTUALIZATION.md` is the source of truth for ordered work,
acceptance gates, and durable receipts.

## Workspace Support

2026-09-05: the history audit, project skill, behavior-spec tools, readiness
checks and read-only Duck Lab viewer are implemented. Start with
`./scripts/duck status` or `./scripts/duck studio`. See
`docs/workspace/RETROSPECTIVE.md` and `docs/workspace/VALIDATION.md`.
This support work does not promote a policy or change the active behavior gates.
The workspace also has a read-only metadata exchange with Sim2Claw; the
contract, fixtures and conformance record are in `docs/workspace/exchange/`.
Offline diagnostics are available through `./scripts/duck-ops`.

The 2026-09-05 cleanup, performance and agent-DX review is complete:
`./scripts/duck verify` runs 94 tooling tests shared with CI. Selected receipt
requests now avoid unrelated integrity work; validation remains enforced.
See `docs/refactor-opportunities.md` for measured results and reviewed scope.
The v6 source bindings and behavior gates are unchanged by this work.

## Current Boundaries

- Do not reuse consumed compute authorizations or retry the failed Brev pilot
  types.
- Do not create an eighth Brev pilot without new user direction and fresh,
  exact authority.
- Do not begin the full CUDA seed matrix from historical smoke authority.
- Do not import, evaluate, publish, approve, or activate either incomplete M6
  candidate as a policy manifest.
- Stop when an authoritative upstream input is unavailable and no honest
  repo-local fixture can close the gate.
- Publication, policy activation, and physical operation require explicit user
  authority.
