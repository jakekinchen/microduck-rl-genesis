# V52 braking complete and rejected; retention correction is next

**September 8 V51/V52 braking activity complete; V52 rejected.**
All three recovery demonstrations became eligible after one 384-candidate
retargeting search. One 2,000-update supervised residual run now survives
both successive stops in both 36-second downhill sessions. All four downhill
windows still fail absolute yaw (.202257–.207138 rad/s versus .20).
Flat retention drops from 63/63 to 38/63; both 180-second compositions fall
at 15.10/158.58 s; surface sessions drop from 5/14 to 3/14. Keep V30.

The first nominal stop already receives a .019819-rad correction on an exact
zero-label training input, grows to 1.102263 rad, and falls at 14.42 s.
All 73,242 evaluated actions and 36,952 pre-braking prefix controls verify;
292,968 load samples, all replay labels, losses and frozen sources are retained.
140 workspace and four focused tests pass. No new PPO transitions, activation,
fresh/protected evaluation or physical calibration. Report:
`experiments/walking/BRAKING-RESULTS-v52.md`.

Next target braking retention: fit the exact successful-stop zero labels more
strictly and collect verified recovery targets on learner-visited diverging
states before one newly frozen run. Preserve downhill stop gains, V15 steady
standing and every existing acceptance gate. Remaining yaw correction, broader
terrain acceptance and measurement-based carpet transfer are still unmet.

The active packet now binds the actual failed V52 nominal forward-0.08 flat
case. The offline audit compares it with the V50 passing reference; this
packet selects only the failed case. First divergence is
the braking action at 13.02 seconds; first fall is 14.42 seconds. The V52
composite includes its separately retained braking ONNX as well as the V50
base walker and original V15 stander. Read the receipt's `braking/` manifest
entries and `braking_policy_sha256`; the base walking digest alone is not the
full controller identity. `duck prepare` verifies the retained source and
trace bindings and starts no training. No new run has been frozen or launched.

The following records describe completed earlier activity.

# V50 correction complete; braking transition is next

Read `experiments/walking/RETENTION-RESULTS-v50.md`. FINAL749 lowers downhill
mean absolute yaw by 16–17% to .202639/.202257 rad/s, still above the unchanged
.20 gate. Both first stops fall (13.98/13.84 s). All 63 flat cases, both full
180-second compositions and exactly the five original passing surfaces remain.
One additional surface window passes; whole-session heading still fails there.
V50 is not promoted. Original V21/V15 with V30 remains retained.

The packet binds V50's verified passing flat reference only. Inspect the
2–13-second downhill prefix and failed stops in
`receipts/walking/20260908-v50-retention-endurance` for the remaining failure.
A narrower yaw error or partial window cannot replace complete acceptance.
All 341,008 paired controls, 56,655 replay labels, 864,000 learning rows,
1,988 switch histories and 9,638 finite scalars verify. Original standing,
teacher and parent normalizers remain fixed. 140 workspace and three focused
tests pass. Training and all four exposed evaluations are complete.

Next freeze a bounded state-conditioned braking correction from the three
clean V49 witnesses. Revalidate or retarget them on V50 incoming states before
learning: the old search is not proof of unchanged-action recovery after the
walking update. Preserve V15 steady standing and retain the remaining .20 yaw
gate. Require successive stops/restarts and all flat, 180-second and passing
surface gates. Fresh/protected banks remain closed while prerequisites fail.
Physical calibration, general terrain acceptance and carpet transfer remain
unmet. Check storage and the process guard before any newly frozen compute.

The following records describe completed earlier activity.

# V49 recovery diagnostic complete; downhill walking yaw is next

Read `experiments/walking/RECOVERY-RESULTS-v49.md`. Original V15 standing
recovers both V48 late-failure states through the full 180-second composition.
The bounded search finds four surviving first downhill stops, three satisfying
the stopping, posture, joint and contact checks. All full downhill cases fail:
the original pre-stop walk has .244/.241 rad/s absolute yaw error versus .20,
all second stops fall at 31.78–31.90 s, and one selected first stop also fails
face pitch. Keep V30; no actor was trained or activated in V49.

The active packet still binds a verified passing V48 flat reference. It is not
the remaining failure: inspect V49 comparisons/search and the original downhill
2–13-second prefix. Original, V46 and V48 prefixes all have excessive absolute
yaw error despite near-zero signed mean rates. A passing average course or a
late recovery cannot substitute for that walking gate.

Next freeze one walking-only correction targeting downhill yaw oscillation,
keeping original V15 standing and V30 command control fixed. Preserve all 63
flat cases, both 180-second compositions, five original passing surface sessions
and every gait/contact/actuator gate. A passing prefix is development evidence,
not full downhill promotion. Retain the three clean searched stopping sequences
as later braking demonstrations; a repeatable transition must cover successive
stops and gait phases after walking retention is established.

The twelve states, 18,296 source controls, 600 reset controls, 34,068 repeated
comparison controls and 245,794 search action/observation rows verify. The
1,536-candidate search is complete with no extension. 140 workspace and two
focused tests pass. All activity compute is finished. Fresh/protected banks,
physical calibration and carpet transfer remain unmet. Read current storage
and process inventory before launching new compute.

The following records describe completed earlier activity.

# V47 diagnosis and V48 standing correction complete; V30 remains retained

Read `experiments/walking/STANDING-RETENTION-RESULTS-v48.md`. V48 keeps 63/63
flat gates but fails both downhill sessions at 13.86/13.78 s with internal-load
failures. One long composition now falls at 86.28 s; the other completes 180 s.
Surface sessions regress from five to four because soft-low-traction-start-1
ends with 17.03 degrees of heading error against the 15-degree limit. Reject V48.

The active packet binds its passing nominal flat reference, explicitly separate
from the unresolved downhill and new composition/surface failures. Inspect
`receipts/walking/20260908-v48-standing-retention-endurance` and the surface
receipt before new work. The first flat case cannot establish retention of
longer sequences. The original V21 walker is byte-frozen, but changed standing
can still change incoming walking states; actor mode alone does not establish
failure causation.

Next freeze a bounded recovery-feasibility diagnostic using complete incoming
state histories. Compare original and V48 standing from identical downhill and
late-composition states, with constrained action search as a separately labeled
privileged diagnostic. Keep the actual delays, actuator limits and all old
quality gates. A finite unsuccessful search is unresolved, not proof that
recovery is impossible. Future learning needs full 180-second candidate-state
retention, beyond static replay from successful reference compositions.

The one 576,000-transition run and all four exposed evaluations are finished.
All 79,984 paired conformance controls, recorded learning rows, 1,447 switch
histories, source freezes and fixed walker/teacher tensors verify. 139 workspace
tests and two focused tests pass. Fresh sequence and protected terrain banks
remain unrun; calibrated physics and carpet transfer remain unmet.

Storage recovery is recorded in `docs/workspace/STORAGE-RECOVERY-20260908.md`.
Time Machine has no destination. The latest raw backup directory and separate
offloads remain; the inactive earlier checkpoint has a verified external copy
and local compatibility symlink. Check live disk/process state before compute.

The following records describe completed earlier activity.

# V45 isolation and V46 retention correction complete; downhill stopping was next

Read `experiments/walking/RETENTION-RESULTS-v46.md` and
`experiments/walking/COMPONENT-RESULTS-v45.md`. V46 restores 63/63 flat gates,
both uninterrupted 180-second compositions and exactly the five passing V30
surface sessions. It adds no passing session over V30. Both downhill sessions
fall at 13.84/13.78 s after standing starts at 13.16 s, with continuous internal
bracing failures. V46 is rejected for promotion; V30 remains retained.

The active packet binds V46's passing nominal forward-08 reference to show the
resolved knee regression. That case is not the remaining failure or evidence of
terrain acceptance. The downhill failures and full raw traces are in
`receipts/walking/20260907-v46-retention-endurance`. Compare the incoming physical,
actuator, sensor and controller state around braking before choosing one
retention-constrained correction; actor mode at the fall does not establish cause.

V45's controlled replacements separate the knee regression from long-composition
falls, but its zero-delay fall requires both replacements in the tested bank.
The frozen V46 protocol's introductory shorthand is corrected in the result
report. Do not edit frozen sources to rewrite that history.

One 360,000-transition run, 56,398 exact paired conformance controls, complete
stored learning rows, frozen teacher/standing tensors and all five V46 source
freezes verify. 139 workspace tests and two focused tests pass. All jobs from
this activity are complete. Fresh sequence and protected terrain banks remain
unrun; physical calibration and general carpet transfer remain unmet.

The following records describe completed earlier activity.

# V44 completed and rejected; component isolation was next

Read `experiments/walking/SEQUENCE-RESULTS-v44.md`. Joint sequence learning
completed 768,000 transitions, but FINAL499 passes 0/63 flat gates, 0/4 diagnostic
sessions and 0/14 exposed surface sessions. Both 180-second compositions fall;
all five previously passing surface sessions regress. V30 stays retained.

The active packet now binds the first V44 flat failure: nominal-delay forward
0.08 m/s has excessive right-knee near-limit occupancy during walking. Compare
the two updated actors separately with their original counterparts before another
bounded refinement. Walking-phase association alone does not prove which actor
caused the incoming state or regression. Keep the original gates and dynamics.

Conformance, complete recorded observation/action data, switch histories, exact
component splits, seven source freezes and finite training scalars verify. Use
r2 flat/surface adapters; the initial surface adapter's wrong walker selection
was corrected before evaluation with unchanged scoring. 139 workspace tests and
two focused tests pass. All jobs are complete. Fresh sequence/protected terrain
banks remain unrun; physical calibration and general carpet transfer remain unmet.

The following records describe completed earlier activity.

# V43 handoff diagnosis complete; full-sequence learning is next

Read `experiments/walking/HANDOFF-RESULTS-v43.md`. Eight original sessions and
49 source branches reproduce with exact action/observation bytes and poses.
The 65 captured/reset states and 130 paired standing trials show a known uphill
training-state regression, a late handoff that both standers fail, and a separate
V42 downhill failure during walking before stopping. No observed branch fall
occurs only after the original three-second episode horizon.

Next freeze one native full walk–brake–stand–restart learning experiment with
repeated turns, actual training state/history coverage and separate fresh
sequence evaluation. Preserve every old flat/endurance/slope and physical-quality
gate. V30 remains retained; V43 trains or promotes no policy. Fresh terrain and
physical calibration remain unmet.

The active packet still binds V42's passing flat reference and exact paired-policy
sources, explicitly labeled as rejected overall. The new diagnostic plot and
full-state bank are linked from the V43 report. Complete snapshots now share
verified data blocks; earlier incomplete attempts and their original bytes remain
retained. 138 workspace tests pass. All jobs from this activity are complete;
check live activity before any new compute.

The following snapshots are historical evidence, not current launch instructions.

# Historical V21 walking foundation

V21 FINAL now passes all 63 exposed native cases: 21 original plus 42 repeated.
Its one reward-only refinement completed 6,144,000 transitions with finite
outputs and 149 source bindings matching. Long-delay forward20 yaw .16366,
arc-right .14331; all physical-quality gates pass. Actual candidate video:
`outputs/walking-progress-20260906-v21/duck-progress.mp4`.

V22 physical-combination development passed 24/24 after that regression gate:
24 windows, exact V21/V15 actors and V16/V19 controllers, lower traction,
increased mass/inertia and their combination. See
`experiments/walking/PHYSICAL-DEVELOPMENT-v22.md`. These are exploratory flat-floor
conditions, not measured hardware calibration or broad terrain generalization.
The imported-physics audit passes all 15 bodies. Full simulation regression
completed without failures; its old default-checkpoint ONNX check was not applicable.
V21 parity was verified separately on all 78,300 observations. Library admission remains blocked
on the rest of `BEHAVIOR_VALIDATION.md`. Do not duplicate computation or retrain.

The V19/V18 baseline history below is retained context, not active launch state.

Historical V19 update: its frozen selected diagnostic is **5/7**, up
from V18's 3/7 on the same windows, but still rejected. Filtering only the
outer course correction fixes the selected forward12 and arc-left startup
failures. Long-delay forward20 yaw MAE .21639 and arc-right .20257 still exceed
.20 rad/s. All seven finish without falls and pass heading/geometry/load gates.
Exact actors, V16 slew, physical model, raw motor actions and gates are unchanged.
This is not a full-bank pass. Receipt: `20260906-v19-filtered-heading-diagnostic`.

V18 full results remain 18/21 original and 41/42 exposed repeated. Duck Lab now
focuses the source-bound V18 long-delay forward20 yaw failure. The unchanged
54-second user video at `outputs/walking-progress-20260906/duck-progress.mp4`
shows V18, not V19. No trainer or evaluator remains active. Next freeze a
bounded same-pair Genesis diagnostic to localize the remaining 3–6-Hz motion;
check actual timing/observation-history semantics before a reward intervention.
See `experiments/walking/RESULTS.md` for the V18 command-mix erratum: actual stop population is 25%,
not the frozen plan's mistaken 5%. Do not alter frozen sources or artifacts.
The future smart library roadmap is `BEHAVIOR_LIBRARY.md`; B1 in the main
queue is blocked on this walking foundation. No accepted walking or hardware.

## Historical standing and walking snapshots (not current instructions)

Authoritative current status (supersedes historical text below): V13 FINAL
is completed and rejected, not training. Original controller gates are 20/21;
long-delay fast forward falls at 14.98 s after STOP. The new applied internal-
load gate rejects 21/21 for leg/battery bracing. The observing evaluator
reproduces all 18,749 original qpos frames and all 21 original action files
byte-identically; observing forces did not change the behavior.
Completed intervention: `experiments/walking/STAND-SWITCH-v14.md`, fixed V5 FINAL
for exactly zero user command and V13 FINAL for nonzero command. Same V12
IMU heading servo, model, BAM, delays and unfiltered actions. Eight focused
load/routing tests pass; complete baseline is 0/21 and pair is 13/21. All 21
cases avoid falls and internal loading; eight stop tilts remain just beyond
the 15-degree limit. Videos are recorded with the selected actor mode.
Completed: `experiments/walking/STANDING-v15.md`. Refine only the standing actor;
five reward tests pass and 64x5 smoke completed in 83.18 s. All 118 sources
match; the bounded 1024x250 standing-only run completed all 6,144,000 new
transitions in 1,416.893 s. Final paired ONNX/video passes 21/21 original cases,
but fresh repeated development is 33/42: four fast-forward stop falls, four
later windows not run after terminal falls, one right-turn restart braces.
Full simulation and expanded-reader workspace regressions passed.
No trainer remains active. V13 walking stays fixed.
V16 command ramp passes 5/6 diagnostic windows; turn restart still braces.
V17 gentler yaw is rejected at 4/6; both right-turn startups brace. Active:
`experiments/walking/UNBRACED-WALKING-v18.md`, apply the V15 internal-load
objective to walking, exact V13 initializer, unchanged command/reset/model.
64x5 smoke completed in 83.06 s, 7,680 transitions and all 140 source files
matching. Bounded 1024x250 training is now running; FINAL249 only. Three focused
tests and 122 workspace tests pass; a schema-only preflight error was rejected
before training and corrected in a retained r2 freeze. Full 21+42 exposed regression
and separately new development are still required; no activation or hardware.

## Historical status snapshots (not current instructions)

Current: `PERSISTENT-CONTACT-v13.md`. Battery/leg interference was confirmed
on original CAD and repaired in the v11 collision model without changing mass,
joint geometry or visuals. The corrected-model v9 actor finishes all 21 with
no falls or body interference, 17/21 motor/posture and 6/21 fully combined.
Explicit v12 IMU heading command control lifts heading to 21/21 and full result
to 17/21. Four long-delay forward/arc yaw-rate failures remain. It is not a
raw-policy success claim; commands and motor actions are kept distinct.

The bounded v13 training run has started after 64x5 smoke, 30 correction tests
and 115 workspace tests; all 123 sources/meshes matched. Hold delays throughout
episodes on corrected collision geometry. Same reward/action interface,
final-only candidate and unchanged gates. V11 model-only training and the old
v10 draft were not run. Current visible video is the v11 unassisted baseline,
long-delay forward12 failure; do not present it as v12/v13 progress footage.
No full walking, hidden-bank or physical acceptance yet.

V13 intermediate150 passes all 21 unchanged motor/posture, heading and
self-contact checks with the fixed v12 command controller. Its actual step
and braking videos were inspected; worst moving yaw MAE .1674 rad/s. This
retained Torch diagnostic does not replace the declared final or authorize
opening a fresh/hidden bank. Training continues unchanged to iteration749.
The later intermediate500 is 20/21: longest-delay left arc yaw MAE regresses
to .21777 rad/s. Every other gate passes. This retained failure takes priority
over the earlier positive diagnostic; neither checkpoint is selected.

## Earlier v9 diagnosis

V9 FINAL is completed and rejected: current-sensor motor/posture 12/21,
heading 7/21, combined 5/21, five falls and nine joint-margin failures.
All heads are normal. Genesis completes all 21 without falls, whereas native
Torch also fails. The visible case is V9 nominal forward12 braking failure.

Active work is collision diagnosis, **not more training**. Same float32 actions
for nominal slow forward finish with the reduced model but fall at 1.94 s in
the bundled full-collision model. Full/reduced also change existing leg masks;
inspect actual mesh pairs, not body names alone. Positive floor-clearance
audits do not certify self-contact or physical fidelity. Preserve every old
gate and receipt. Conditional v10 timing-only training is paused.
See `experiments/walking/RESULTS.md` and
`receipts/walking/20260905-v9-full-collision-replay-r2/`.

## Retained development history

Current: `experiments/walking/VIABILITY-v9.md`. V8 FINAL is rejected:
0/21 in all three protocols because head posture regresses at stop, even
though trunk stopping tilt is now 6.30–6.77 degrees and no cases fall.
Current-sensor yaw fails six and separate heading passes only 9/21.
The objective-composition correction conditions positive return on posture,
keeps every negative penalty and prices persistent yaw bias. Numerical audit
and focused/full tests pass; 64x5 smoke completed and the bounded 1024x750
run is learning, all 35 source hashes matched. No physics/model, action-filter,
threshold or command-schedule change. Read `RESULTS.md`.

Visible active failure: V8 nominal 20/20-ms slow forward and stop, with exact
final video and joint trajectory. Earlier partially passing baseline V5 is
retained separately. Neither is accepted walking or hardware authority.

Retained viewer baseline: V5 FINAL completed 18,432,000
new transitions: 6/21 old regression, 5/21 v5-heading legacy-clock, 6/21 copied-
current-sensor. Head posture passes all; joint-stop/torque/slip failures are
absent. Remaining corrected-sensor failures are yaw 15, stop tilt 5 and one
no-op turn. Full-CAD clearance passes. This is genuine partial progress, not
full walking or transfer. The UI opens its slow-forward passing case.

V6 applies only the measured contact-default correction (10 -> 20 ms) to
training, preserving every v5 reward, action, observation and timing function.
The 64x5 smoke passed (7,680 transitions, 58.4 s); the bounded 1024x1500x24
local training run completed all 36,864,000 new transitions from v5 FINAL.
Its exact rejected final and all three evaluations are retained. V8 uses only
that declared final as initialization, never an intermediate selection.
Read the frozen plans for details.
Keep all three exposed visible batteries and numerical limits unchanged.

Historical lineage below is not an instruction to restart an earlier run.

The owner now requests proper walking. `experiments/walking/PLAN.md` and
`suite-v1.json` define the command-only walking-v1 intervention and fresh
visible timing cases. The v1 smoke passed, but its long run was deliberately
stopped after 8,773,632 logged transitions: intermediate diagnostic torque,
slip and stopping failures. `receipts/walking/20260905-v1-stopped/` retains it.
V2 improves nominal gait, torque and stopping, but was stopped after 7,962,624
logged transitions because of a persistently folded neck and zero-lag turn
failure. `experiments/walking/POSTURE-v3.md` freezes the additive posture cost
and rejection gate; the old motor evaluator and model stay unchanged. V3 is
complete: posture 21/21, composite 0/21, with yaw errors in both engines and
additional native stop failures. Active correction is `TRACKING-v5.md` and
the fresh `tracking-suite-v1.json`: non-saturating command error on the tested
native-floor base. The 64×5 smoke completed; bounded 1024×750 local training is
running unchanged. Final-only,
same motor/posture gates, old 21-case regressions also required. Proper walking
is not accepted. The user request authorizes local implementation;
these files do not create new hardware, publication or paid-compute authority.

Separate contact-default and IMU sampling-phase corrections are documented in
`experiments/walking/RESULTS.md`. Do not hot-patch active v5 training. Evaluate
its final candidate on both frozen original protocols plus the additive
current-state sensor protocol; retain failures rather than overwriting them.
Checkpoint150 remains a rejected diagnostic: better stopping/heading tradeoff,
but left hip pitch stop parking and excessive stop tilt. Not a camera artifact.

The gait-v4 timing factorial is important: 20-ms motor + 20-ms sensor latency
lets the unchanged policy take 33/33 qualified swings at 0.12 m/s in native
MuJoCo; zero-lag gives 0/0. Pure turns fail both. Fix the explicit timing model
and learn across the delay envelope, do not weaken old gait thresholds or
rewrite old negative receipts. No physical timing calibration is claimed.

`scripts/evaluate_walking.py` owns command tracking, stop and foot-contact
checks, plus 200-Hz torque telemetry. Freeze is
`experiments/walking/evaluator-freeze-v1.json`. The historical snapshot below
is retained context, not a direction to resume gait-v3 or the laser queue.

## Historical working brief: randomized laser startup

This is the working brief for the next investigation in the existing L2
queue. `TRAINING_ACTUALIZATION.md` remains authoritative for task ordering.
The active training task retains ownership of physics, reward and evaluator
changes. The workspace task supplies source-checked inspection and preflight.

## Current lane: versioned gait correction

Current authoritative correction: **gait-v4**, not v3. See
`experiments/laser/GAIT_DIAGNOSIS.md` and `gait-correction-v4.json` in that
directory. The physical mouth/head site points +X; the legacy CAMERA points
inward. The v3 opposite-axis attempt is stopped and quarantined, with exact
source/terminal evidence under
`receipts/laser-gait/20260905-v3-quarantined-final/`. Do not resume it.
The v4 evaluator is frozen in `gait-evaluator-freeze-v4.json`; it emits
`microduck.laser-gait-evaluation/v4`. The bounded run is now **complete and
rejected**: 1/4 target, 0/4 gait, 0/4 composite; actual stop parking is absent,
but all four cases have zero qualified swings on either foot. No training is
active. Basic measured walk/turn/stop learning now precedes more pursuit/DR.
Current status and final evidence are in `GOAL.md`, `TRAINING_ACTUALIZATION.md`
and `receipts/laser-gait/20260905-v4-evaluation/`. The snapshot history below is not
an instruction to reactivate v3 or reinterpret physical forward as negative X.

The training task has advanced to the versioned face-first gait correction in
`experiments/laser/gait-correction-v3.json`. The initially observed running record was
`laser-gait-20260905-v3`: 1,024 environments, 600 iterations, 14,745,600 planned
transitions. All ten source hashes matched at the recorded check; the updated
process guard recognizes `train_laser_gait.py`. A later snapshot detected a
gait-v4 starting record and source drift against the earlier gait-v3 record.
`duck prepare` lists these separately; exact process-to-run identity is not
asserted. Read the current records for the live version, preserve each version's
source bytes and terminal status, and do not interrupt or duplicate a run merely
to adopt this workflow.

The evaluator now requires both target pursuit and measured gait rejection
gates. Its negative controls cover standing, backward motion, loaded-foot
sliding, one-foot hopping, mechanical-stop parking, and legitimate BAM target
overshoot. Candidate selection is the declared final checkpoint only. The
fresh reserved bank remains closed until all visible composite gates pass.
Current robot/world code differs from the old startup receipt, so `prepare`
correctly refuses direct reproduction through that changed source while
separately checking the running gait record's source hashes.

The retained startup comparison below is a negative control and an example of
the diagnosis process. It is not a direction to restart the old intervention.
Duck Lab reads the new `microduck.laser-gait-evaluation/v3` composite reports
under `receipts/laser-gait/` or `receipts/laser-dynamic/` when they are retained.

```sh
./scripts/duck prepare
./scripts/duck doctor
./scripts/duck-ops guard
./scripts/duck studio
```

`prepare` launches nothing. It verifies the selected development policies,
manifests, suite identity, matching randomized case, complete trace bindings
and current versus retained experiment implementation. It prints the exact
first-fall sample and the prerequisites for any next training intervention.
The process inventory is advisory; rerun `guard` immediately before launching
any separately authorized local job. A successful inspection does not reserve
the Mac or authorize a training budget.

Duck Lab now opens on `20260905-turn-dev` versus `20260905-robust-dev`, case
`75003-figure-eight`. Use **First fall** to inspect the 1.56-second sample and
expand **Recorded domain for this case**. The two recorded policies differ;
this comparison is a policy-intervention diagnostic, not fixed-action physics
replay. Refresh retains a user's selected experiment and case.

## What the retained evidence already tells us

- The selected policy falls at 1.56 s; the previous DR policy remains upright
  for the recorded 48-second case but fails tracking. Keep both negatives.
- The scheduled push is at 23 s. It cannot explain this startup fall.
- Sensor delay is zero in this draw. Delay injection is not active here.
- The first recorded action and position differences are already at 0.02 s;
  commands diverge at 0.04 s. Only 78 rows align before the selected policy
  falls, versus 2,400 rows in the previous policy's complete case. The offline
  comparison correctly labels the pair incomplete rather than asserting action
  identity. Contact telemetry is absent in both retained traces.
- Friction is about 1.342×, trunk mass/inertia 0.909×, and motor gain 0.906×.
  CoM shift, encoder bias and sensor noise are active. These are candidates
  for controlled property tests, not demonstrated causes.

## Next bounded diagnosis

1. Reproduce the selected policy on visible seed 75003 with unchanged source,
   reset and domain. Preserve the first-step state and first-fall row.
2. Keep policy bytes, target route, model/BAM and all other conditions fixed.
   Neutralize one active group per trial: friction; mass/inertia together;
   CoM; motor gain; encoder bias; sensor noise. Record actual applied values
   and fixed random schedules. Do not spend trials on the later push or the
   already-zero delay as explanations for this startup event.
3. Record pre/post-step qpos/qvel, actor inputs, commanded actions, realized
   actuator output and contacts where available. Missing telemetry stays
   unknown. A fixed-policy feedback test can measure a property intervention;
   causal claims about engine differences require original saved action bytes.
4. Choose one next intervention from the measured result. Freeze its hypothesis,
   bounded budget and a fresh evaluation bank before training. Do not tune on
   any consumed reserved seed, including 75109, or relax the old thresholds.
5. Run a smoke, then the bounded experiment, then independent development and
   original regression checks. Freeze candidate choice before fresh reserved
   evaluation. Report falls and incomplete episodes in every denominator.

Camera-driven behavior remains a separate next step. Ground-truth targeting
and floor appearance changes provide no camera robustness evidence.

Update `active-experiment.json` when the working candidate or case changes.
The selector fails closed on policy/suite drift instead of silently pointing
the agent or viewer at a different result. This brief adds no new agent loop.
