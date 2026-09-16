# Training actualization plan

## Active owner priority — document, publish, then review the approach (September 16)

The owner requested a complete repository/evidence synchronization before a
process review covering progress, tools, frameworks and methodology. This
priority supersedes automatic continuation of the experiment sequence below.
No new training or simulation is part of the publication task.

- [ ] Reconcile current documentation, preserve experiment evidence, verify the
  publication snapshot, and push to `origin/main` with accessible bulk evidence.
- [ ] Review the full process using
  [PROCESS_REVIEW_20260916.md](docs/workspace/PROCESS_REVIEW_20260916.md), then
  choose whether to continue, simplify or replace the proposed next experiment.

The older dated sections retain historical results and proposed next steps.
Their use of "active" or "next" does not override this owner priority.

## Owner-directed task complete — moving laser course (September 13)

- [x] Diagnose old laser gait versus retained V21/V15 walking evidence.
- [x] Build solid course geometry and continuously moving target adapter.
- [x] Run a 12-second physics smoke; retain partial/negative setup evidence.
- [x] Evaluate the full frozen course and six declared development conditions.
- [x] Verify exact motor actions, collider coverage and observer invariance.
- [x] Film one continuous recorded run from several angles; retain wide reference.
- [x] Report all gait/contact/course results and remaining physical/camera limits.

Plan: `experiments/laser/COURSE-v1.md`. This is scoped owner-requested local
simulation work; prior walking/terrain prerequisites and protected banks remain
unchanged. The ordered foundation tasks below remain the long-term queue.
Result: `experiments/laser/COURSE-RESULTS-v2.md`; all six exposed conditions pass
the stronger v2 gate-crossing/course and unchanged physical rejection checks.
Delivered the checked 76-second film plus 66-second continuous wide reference.
This closes the scoped demonstration request, not behavior-library admission.


This is the execution queue for turning the working Genesis/MPS pipeline into a
reproducible, independently evaluated policy-production system. Work is judged
by closed gates and durable receipts, not by reward movement or a visually
plausible rollout.

## Work mode

Advance this queue directly in one Codex task. Do not create
Executor/Reviewer/Manager cycles, fork review tasks, or run an autonomous goal
loop. Historical role logs are retained as evidence only; they are not active
instructions. Implement, test, review, and update this task list in the same
task.

## Workspace support delivered — 2026-09-05

- [x] Index 126 local historical sessions and 307 repository log documents;
  preserve coverage metadata and evidence-backed lessons in
  `docs/workspace/RETROSPECTIVE.md`.
- [x] Add `./scripts/duck status`, `doctor`, `new`, `check-spec`, and `studio`;
  reuse the existing queue and receipt formats rather than creating a role loop.
- [x] Add a repository skill and behavior/physics workflow; materialize the
  exact pinned BAM dependency under ignored `.workspace/bam`.
- [x] Verify the read-only viewer with retained videos, synchronized
  trajectories, negative case results, training telemetry and focused tests.
- [x] Add source-bound metadata exchange with Sim2Claw, shared rejection
  fixtures, and native-reader conformance; retain evidence under
  `docs/workspace/exchange/`. Link the separately integrated offline diagnostics.
- [x] Review the requested three parallel cleanup, performance and agent-DX
  passes; remove redundant JSON traversal and report state, and reduce selected
  receipt inspection work with measured baseline/candidate equivalence.
- [x] Share `duck verify` across local use and CI, reject empty discovery, retain
  explicit skips/results, and verify all 94 tooling tests plus browser flows.
  Existing full-suite registrations and all 25 running v6 source bindings remain
  intact. Review and evidence: `docs/refactor-opportunities.md`.

This is workspace tooling evidence. It does not advance M2/M5/M6, accept a
new behavior, grant physical authority, or replace the active L2/L1 work.
Validation: `docs/workspace/VALIDATION.md`.

## Historical foundation boundary — September 1 (not current status)

| Gate | State on 2026-09-01 | What is established |
|---|---|---|
| Public Apple code | Present | Metal physics and MPS learner selection are committed on `main`. |
| Apple model preflight | Observed | Genesis 1.3.3 loaded a real Microduck MJCF and completed one finite Metal step. |
| Walking/backflip pipeline | Clean-clone reproduced | Receipt `20260901T215219Z-2ce72a94` passed both 64x5 smokes, two normalized ONNX exports, two randomized parity checks, and two real-observation parity checks from committed state. |
| Canonical contract | Closed M1 contract evidence | Interface/model/BAM locks, pinned BAM fixtures, official mjlab consumption, six model variants, walking/backflip semantics, and the local versioned-divergence decision are frozen. The tasks record 28 and 32 classified fields respectively and do not claim identical training trajectories. |
| Task success | Open | No frozen success battery has accepted an Apple-trained walking or backflip policy. |
| Held-out C MuJoCo | Open | No independent frozen-ONNX acceptance suite exists yet. |
| Physical validation | Open | No policy from this repository has physical authority. |

The only promotable statuses are `artifact_validated`, `sim_previewed`,
`reference_evaluated`, `hardware_observed`, and `physically_accepted`. Each
status requires its own receipt; no earlier status implies a later one.

## Ordered task queue

Only one milestone should be promoted at a time. A checked implementation item
does not close its milestone until every exit gate and receipt is present.

### L2 — Dynamic pursuit and domain randomization (active user priority, 2026-09-05)

Owner gait objection supersedes delivery: the counts below are **target-only**
development results, not credible walking. Do not promote the current policy.

- [x] Measure actual stepping, loaded-foot slip, non-foot contact, face/command
  alignment and servo limits on visible cases; identify the causal mismatch.
- [x] Correct the smallest evidenced root cause in a versioned lane and add
  reward-independent gait rejection tests before any new training.
- [x] Verify the intervention with fixed-scale close-up footage and measured
  simulator contact/clearance/actual-joint telemetry. Stop parking is corrected,
  but sustained stepping is absent: a terminal negative, not a walking pass.
- [x] Complete bounded gait-v4 training and the target-AND-gait development
  suite. Preserve the quarantined wrong-axis v3 attempt and do not resume it.
  Correct physical forward is +X; the legacy render camera pointed inward.
  Completed 14,745,600 new transitions; final target 1/4, gait 0/4, combined 0/4.
  Old policy under the same frozen evaluator: target 4/4, gait 0/4. Reject both.
  See `experiments/laser/GAIT_DIAGNOSIS.md` and `receipts/laser-gait/`.
- [x] Freeze basic locomotion before pursuit in `experiments/walking/PLAN.md`
  and `suite-v1.json`: seven walk/turn/arc-and-stop cases, three explicit timing
  profiles, no hidden-bank use. A timing factorial identifies a missing
  motor/sensor latency model in the old evaluator; old results stay unchanged.
- [ ] **Active: establish basic locomotion before pursuit.** Pass nominal
  command-conditioned walk/turn/stop cases with useful tracking, sustained
  bilateral stepping, slip, actual joint/torque margin and settling gates.
- [x] Pass command-only walking-v1 64×5 smoke with collision-sole reward checks.
- [x] Stop and preserve walking-v1 when checkpoint250 diagnoses an unsafe
  reward tradeoff: 8,773,632 logged transitions; four diagnostic failures on
  torque/slip/stop, not an accepted walking candidate. The old v4 baseline is
  0/21 on the frozen walking command/timing suite.
- [x] Pass controlled walking-v2 smoke and retain its deliberate early stop
  after 7,962,624 logged transitions. Nominal gait/torque/stop improve, but
  zero-lag turning fails and the neck stays about 88 degrees off neutral.
- [x] Complete walking-v3 neutral-head control smoke and 18,432,000-transition
  run. Final posture 21/21, but composite 0/21: yaw 21 failures, stopping 11,
  lateral speed 9. Stepping/slip/joint/torque gates pass in all cases. Retain
  the failed candidate and exact training under `receipts/walking/20260905-v3-*`.
- [x] Complete walking-v5 command response. Add only the
  non-saturating command-error objective on the tested native-floor base;
  pass 64×5 smoke then at most 1024×750 training. Fresh visible headings plus
  all old regressions, same thresholds, final-only candidate. See
  `experiments/walking/TRACKING-v5.md`. Completed 18,432,000 new transitions;
  final 6/21 old, 5/21 fresh-heading legacy clock, 6/21 corrected sensor.
  Head 21/21; joint/torque/slip pass. Remaining heading, stop tilt and one
  no-op turn mean no complete walking acceptance.
- [x] Retain v5 64×5 smoke: 7,680 transitions, 62.0 s. The unchanged bounded
  1024×750 run is completed; no intermediate checkpoint is eligible for promotion.
- [x] Complete walking-v6 native contact-default intervention. Apply the
  separately tested 20-ms native constraint default to training, preserving
  every v5 reward/action/timing function. Pass 64x5 smoke then bounded
  1024x1500 training from v5 FINAL. Require all three unchanged exposed
  visible batteries, body clearance, real-observation export parity and video.
  See `experiments/walking/CONTACT-v6.md`. All three complete protocols are
  0/21: stop lean remains, plus a long-delay fast-forward fall. Retained,
  rejected final; this checked implementation item is not walking acceptance.
- [x] Complete and reject walking-v8 trunk-balance final after v6 evaluation:
  `experiments/walking/BALANCE-v8.md` adds a non-saturating torso-lean cost.
  Checkpoint750 improves all four diagnostic motion/stepping/motor cases but
  stops at 30–34 degrees tilt. The final confirms stop lean and longest-delay
  falls. V8 64x5 smoke and bounded 1024x1000 run completed;
  preserve v6 source and allow only its completed retained final as initializer.
  Full-bank checkpoint150: all stops 5.6–6.4 degrees, no falls, 12/21 old and
  4/21 old-plus-heading passes. Still diagnostic; yaw drift and three actual
  hip-yaw margin violations remain. No intermediate selection or hot patch.
  FINAL: 24,576,000 transitions, 0/21 in each protocol. Trunk stops/falls and
  actual-motor gates improve, but all 21 cases fail head posture at stop.
  Current-sensor yaw fails six; heading 9/21 and combined 0/21. Retain the
  regression and final videos; do not promote the earlier intermediate.
- [x] Complete and reject **walking-v9 posture-conditioned return** in
  `experiments/walking/VIABILITY-v9.md`. Positive rewards are conditioned on
  head/trunk posture; safety penalties stay active and persistent yaw bias
  gets an explicit cost. No physics/action/timing/threshold change. Reward
  decomposition passes 2,000 actual samples/183 landings; 50 focused tests pass.
  64x5 smoke completed 7,680 transitions in 94.6 seconds; all 35 source hashes
  match. The bounded 1024x750 run completed 18,432,000 transitions from exact
  v8 FINAL in 3,913.2 seconds; all final protocols/videos are retained.
  Final old/new/current motor-posture: 12/21, 15/21, 12/21; heading: 7/21,
  6/21, 7/21; combined 5/21 each. Current-sensor has five falls and nine joint-
  margin failures despite normal head posture in all 21. Reject the candidate.
  Full process-isolated regression and 109 current workspace tests pass.
  Intermediate150: 17/21 motor/posture, 6/21 heading and combined; all head,
  stop, actual-motor/step/slip gates pass. Four yaw-rate cases and cumulative
  direction drift remain. Full-CAD 18,900 poses clear by >=14.29 mm. No
  intermediate selection; conditional v10 timing proposal is not active.
  Intermediate500: 16/21 motor/posture, 9/21 heading, 7/21 combined; longest-
  delay fast-forward braking falls at 13.88 s despite normal head posture.
  Diagnose that stop transition and retain it; do not average away the fall.
  Require all old and additive heading gates unchanged.
- [x] **Isolate and correct collision-model semantics before retraining.**
  Native Torch reproduces control failure while the complete Genesis bank
  has no falls. Same-action full-collision replay makes nominal slow forward
  fall at 1.94 s; reduced completes. Audit exact mesh pairs and masks: the
  bundled full model also changes existing leg masks, not just added geometry.
  Copied full-CAD floor clearance cannot certify self-contact. Preserve all
  old gates and model hashes; do not activate the conditional v10 timing draft.
- [x] Confirm actual raw-CAD battery/leg triangle intersections (six witnesses),
  not merely convex-hull cavities. Add complete-contact-v11 model and 1-mm
  all-frame self-interference rejection. Mass/joints/visuals unchanged. All
  21 old v9 traces fail; corrected closed-loop baseline: self-contact 21/21,
  no falls/head/stop/joint failures, motor/posture 17/21, full combined 6/21.
- [x] Test explicit v12 IMU heading command controller with unchanged v9 actor:
  heading 21/21, combined 17/21. Preserve both requested and policy commands;
  no post-policy action edits or raw-actor success claim. Four long-delay
  forward/arc yaw-rate failures remain; thresholds are not relaxed.
- [x] **Complete and reject v13 persistent device delays on corrected geometry.**
  `experiments/walking/PERSISTENT-CONTACT-v13.md`. Thirty correction tests,
  115 workspace tests and the 64x5 smoke pass; 7,680 transitions in 82.12 s,
  all 123 bound source/mesh files match. Bounded 1024x750 training completed
  18,432,000 transitions from exact v9 FINAL. Final controller 20/21, raw 4/21
  combined; long-delay fast forward falls at 14.98 s after STOP at 13 s.
  Five complete final protocols/videos retained. Separately evaluate
  the fixed v12 command controller; keep complete body/heading/motor gates.
  Neither v11 model-only training nor the old v10 draft was run. No fresh
  development or hidden-bank opening until all current complete gates pass.
  Intermediate150 diagnosis: 21/21 in every component and combined, with the
  fixed v12 command servo; worst yaw MAE .1674 rad/s. Actual videos show
  alternating foot lifts and upright braking. Not ONNX acceptance or selection;
  finish and evaluate the predeclared final, retaining any later regression.
  Intermediate500 is 20/21: long-delay arc-left yaw MAE .21777 > .20, with
  every other gate passing. The negative is retained, not rounded into a pass.
- [x] Diagnose hidden internal bracing with 200-Hz applied-load replay. V13
  loads legs against the battery at stand/stop despite small penetration;
  three moving intervals have no self-load. Original action/qpos bytes replay
  exactly. V5 FINAL has zero load throughout the same three comparison cases.
- [x] Test unbraced standing and safe walk/stop transitions with a fixed pair.
  `experiments/walking/STAND-SWITCH-v14.md`: fixed V5 standing / V13 walking
  command-selected pair, same V12 heading servo, no blending or action edits.
  Freeze and baseline-test the new 200-Hz load gate before evaluating the
  pair. Preserve every motor/posture/heading/body-geometry threshold. Eight
  focused tests pass. Baseline 0/21; V14 pair 13/21, no falls or internal loads
  across 75,600 physics samples. Eight stop tilts exceed the unchanged limit
  by 0.0712–1.5418 degrees. Full videos retained; not accepted walking.
- [x] **Complete and reject V15 upright standing pair on fresh transitions.** Keep V13 walking fixed;
  train only a standing component from V5 FINAL with zero commands, V9 posture
  reward and additive internal-load gating/cost. Five reward tests pass;
  64x5 smoke completed 7,680 transitions in 83.18 s; all 118 sources match.
  Exactly 1024x250 local standing training completed all 6,144,000 transitions
  in 1,416.893 s; retained FINAL249 and all matching source files. Evaluate
  only FINAL249 in the unchanged pair architecture: all 21 full gate cases
  now pass, with no falls and worst stop tilt 6.7963 degrees. One allowed
  20-ms internal-contact transient, not sustained bracing. Fresh 42-window
  development is 33/42: four fast-forward stop falls, four later windows not
  run after terminal falls, one repeated right-turn startup braces. Full
  simulation regressions and 120 expanded-reader workspace tests passed.
  See `experiments/walking/STANDING-v15.md`; no physical or pursuit acceptance.
- [x] Retain V16 command-ramp diagnostic: 5/6, tested fast-forward handoffs
  fixed but repeated right-turn startup still braces for 245 ms.
- [x] **Reject gentler turn acceleration at actor handoff (V17).** One fixed
  change: yaw slew .75 rather than 2.5 rad/s^2; translation .75 m/s^2, both
  actors and all physics/gates unchanged. Run the same six diagnostic windows;
  result is 4/6: both right-turn startups brace, 240 and 420 ms continuous.
- [x] **Complete and reject internal-load-aware walking refinement (V18).** Same V15 load
  objective on all V13 walking commands; no reset/command/model/action change.
  Freeze seed26090618, LR2e-4, 64x5 smoke then 1024x250, FINAL249 only. Three
  focused tests pass; schema-only preflight rejection retained, r2 smoke
  completed 7,680 transitions in 83.06 s, all 140 sources match. Full bounded
  run completed 6,144,000 transitions in 1,398.282 s; declared FINAL249 only.
  Native original result is 18/21: no falls and all heading/geometry/internal
  load/standing gates pass; three long-delay yaw-rate MAEs are .20701–.21839
  against .20. Expanded repeated bank is 41/42, no falls or sustained internal
  load. One arc-left startup has 1.04004-mm battery/leg penetration in one
  frame at 1.44 s versus 1 mm. Preserve all four residual failures. User-requested
  54-second actual progress video includes two passes and a labeled failure.
  Fixed V15 stander and V16 ramp; require all 21+42 exposed cases and
  separately new development before any pass. See `UNBRACED-WALKING-v18.md`.
- [x] Isolate V18 residuals from retained traces and startup witnesses. Mean
  yaw bias is small; dominant yaw motion is 3–6 Hz, corroborated by IMU heading
  derivative. Correction is unsaturated; closed-loop correlation is not cause.
  Receipt: `20260906-v18-residual-analysis` (no new physics).
- [x] **Retain partial improvement and reject V19 filtered course correction.**
  Frozen seven-window diagnostic with exact V18/V15 actors, V16 slew, unchanged
  physics and gates: 5/7 versus selected V18 baseline 3/7. Only outer heading
  correction is low-passed at tau=.12 s; motor actions remain unfiltered.
  Forward12 and the failed startup now pass; long forward20 yaw .21639 and
  arc-right .20257 still exceed .20. All seven heading/geometry/load gates pass,
  no falls. Six controller tests pass. Full 21+42 V19 regression was not opened.
- [x] Correct the V18 recipe record without rewriting frozen evidence: the
  effective V2 sampler and recorded run config use 25% stop, not the frozen
  prose's 5%. Three deterministic bucket/bounds/metadata tests pass; both new
  test modules are registered. All 122 workspace tests also pass. V19 integrity
  audit verifies 165 files, 147 source bindings and 6,300 complete trajectory rows.
- [x] **Localize the remaining high-frequency yaw failure across engines.**
  Freeze a bounded Genesis diagnostic for the exact paired V18/V15 policies
  and controller, with long-delay forward20/arc-right and a nominal control.
  Verify effective command/sensor/motor timing, reset and observation history
  before comparing closed-loop traces. Keep this distinct from fixed-action
  causal isolation. Select one evidenced intervention, not an open-ended PPO
  extension or softened gate. Require all original 21 and exposed 42 before
  a separately frozen new development bank.
- [x] V20 exact V18/V15/V16/V19 pair in Genesis CPU: both long-delay yaw failures
  reproduce (.23446 forward20, .20235 arc-right), nominal control .17279.
  All 2,700 actor inputs and 10,800 motor-delay targets verified; three complete
  cases, heading passes. Corrected scalar-adapter r2 receipt retained alongside
  pre-physics failed first attempt. Engine agreement is diagnostic, not calibration.
- [x] **V21 bounded instantaneous-yaw refinement.** Smoke and full run completed;
  6,144,000 transitions in 1,100.319 s, FINAL249 only, all 149 sources matching,
  finite actor/telemetry and learning curves. Original 21/21 and exposed repeated
  42/42 pass every unchanged gate. All 63 videos retained; no falls or bracing.
  Long forward20 yaw .16366 and arc-right .14331, below .20. Fixed V15 standing,
  V16 ramp and V19 heading. No protected bank or physical acceptance.
- [x] Verify imported physical parameters: 15 bodies' mass, COM and inertia
  match the authored MJCF within float32 tolerances; .737243-kg total mass.
  This is import consistency, not measurement calibration.
- [x] **V22 new physical-combination development**, frozen after all 63 passed:
  24 windows across nominal, .6x traction, 1.1x mass+inertia and combined profiles,
  new commands/poses and two continuous repeats. Three factor application,
  reapplication and model-isolation tests pass. All 24/24 windows pass every gate;
  measured contact friction .6/1.0, runtime mass .737243/.810967 kg, all videos
  retained. This is new parameter-combination development on flat terrain, not
  broad unseen-environment or physical acceptance. No automatic retraining.
- [x] Close verification: 131 workspace tests and the full 61-group simulation
  runner complete without failures using pinned BAM. The legacy default-checkpoint
  ONNX check is not applicable; exact V21 parity is verified on 78,300 actual
  observations. Separate standing posture passes all 87 windows. No compute remains.
- [x] **V23 terrain/endurance executed and reviewed.** New terrain 2/12 sessions
  pass, plus 2/2 flat controls; 9/28 windows, five falls, four explicit unrun
  windows. Four sustained 180-second walks pass complete audits. Both long
  compositions fail whole-session heading (64.04/86.44-degree endpoint errors),
  although original short-window scores remain 24/24. Retain every original
  score and the additive audit; no broad terrain/composition acceptance.
- [x] Implement passive measurement intake, split/uncertainty/residual checks and
  missing-input rejection. Six synthetic tests pass; no measurements invented.
- [x] **V24 heading persistence diagnostic:** both 180-second compositions pass
  all windows and whole-session heading (6.15/9.74-degree endpoints). The
  maximum in one case is 19.937/20 degrees. Both downhill sessions still fall;
  standing transition repair and broader regression remain open.
- [x] **Public-data development V25–V30 executed and reviewed.** Three full
  refinements completed 18,432,000 transitions. V25 walker/stander/both and V27
  fail the surface admission rule; no trained actor is promoted. Final V30
  controller passes all 63 flat gates and both 180-second compositions, with
  6.24/8.95-degree endpoint error, but surface results remain 5/14 and downhill
  remains 0/2. Preserve all prior negatives and the source-identical disk-error
  retry. Research, numerical audits and commands: `experiments/walking/PUBLIC-SURFACES-RESULTS.md`.
- [ ] Isolate the 2/5 robot-level cross-engine comparison using matched support
  representations and fixed actions before more broad surface training. Public
  static means and unrelated sensor features do not close Ducky calibration.
  Then repair slope/soft-surface standing and continuous transition failures;
  keep V30's improvement limited to its passed flat/endurance scope.
- [x] V31–V40 bounded contact diagnosis: match native support boxes, audit actual
  collider hulls and test detector, pruning, integration and compatibility
  properties separately. Original controls reproduce. V34 closes the sampled
  collider support mismatch (22 nm maximum); softer robot-level numerical
  disagreement remains open. Preserve original and changed-lane results.
- [x] Reject V38 slower STOP deceleration: downhill no longer falls, but all
  four sessions fail required gates and long compositions acquire falls.
- [x] V41/V42 focused native standing refinements completed and rejected:
  384,000 transitions each, exact template/reset checks and finite telemetry.
  V42 preserves 63/63 flat but passes only 1/4 diagnostic sessions and 3/14
  exposed surface sessions. Preserve V30, all failures and the unopened fresh
  bank. Report: `experiments/walking/SEQUENCE-RESULTS-v41.md`; full verification
  and permanent training evidence: `receipts/walking/20260906-v42-sequence-verification`.
- [x] V43 full-state handoff diagnosis: 36,622 replay controls, 65 captured/reset
  states, 130 paired branches and 9,987 exactly reproduced source-branch controls.
  V42 fails known uphill training starts; both standers fail the late composition
  state. Reset diversity/horizon alone is not a sufficient evidence-based next
  intervention. All failures and original gates remain. Full snapshot storage
  is lossless, deduplicated and covered by the 138-test workspace suite.
  See `experiments/walking/HANDOFF-RESULTS-v43.md`.
- [x] V44 native joint full-sequence experiment completed: one 768,000-transition
  run from V21/V15, full observation/action and switch-history coverage, original
  physics/controllers and frozen fresh sequence bank. FINAL499 rejected at 0/63
  flat, 0/4 diagnostic sessions and 0/14 exposed surface sessions. Keep V30;
  fresh/protected banks remain unrun. All seven freezes, five evaluation/conformance
  manifests, exact component exports and 5,888 finite learning scalars verify.
  Report: `experiments/walking/SEQUENCE-RESULTS-v44.md`.
- [x] V45 component isolation completed on the frozen small exposed bank. All
  27,703 original/joint action rows and poses reproduce. Walker replacement
  reproduces knee occupancy; stander replacement causes long-composition falls.
  Both mixed pairs survive the selected zero-delay case, unlike joint V44.
  Neither mixed pair passes all gates. See `experiments/walking/COMPONENT-RESULTS-v45.md`.
- [x] V46 retention correction completed: one 360,000-transition walker-only
  run with original standing frozen, three timing profiles and normalized margin
  cost. FINAL249 restores 63/63 flat and both 180-s compositions, retaining the
  same five passing surfaces (5/14 sessions, 12/28 windows). Downhill remains
  0/2 with falls and internal bracing; reject promotion and retain V30. All
  56,398 conformance controls, recorded learning data and source bindings verify.
  See `experiments/walking/RETENTION-RESULTS-v46.md`; fresh banks remain unrun.
- [x] V47 diagnosis and V48 standing correction complete. V47 reproduces
  2,763 downhill controls and 400 continuations from sixteen complete states.
  V48 completes one 576,000-transition run with the original walker frozen,
  flat/long-composition replay and complete pre-brake resets. FINAL499 retains
  63/63 flat gates, but downhill remains 0/2, long compositions regress to 1/2
  (fall at 86.28 s), and surfaces regress to 4/14 (one lost heading gate).
  Reject V48; retain V30. All 79,984 paired conformance controls, recorded
  learning rows and source bindings verify. Storage headroom is restored by
  authorized snapshot removal and verified archival offload. See
  `experiments/walking/STANDING-RETENTION-RESULTS-v48.md`.
- [x] V49 recovery diagnostic complete. Twelve full states reproduce exactly.
  Original V15 standing recovers both V48 late-failure states through 180 s.
  A bounded 1,536-candidate search produces four surviving first downhill stops;
  three pass stopping/posture/contact checks, but all first windows retain
  pre-stop yaw error above .20 rad/s and all second stops fall at 31.78–31.90 s.
  One candidate additionally fails final face pitch. No full downhill admission;
  retain V30. All 245,794 search action/observation rows and full continuations
  verify. See `experiments/walking/RECOVERY-RESULTS-v49.md`.
- [x] V50 bounded walking-only yaw correction complete. One 864,000-transition
  run reduces downhill absolute yaw by 16–17% to .202639/.202257 rad/s, still
  above the .20 gate. Both first stops fall at 13.98/13.84 s. All 63 flat cases,
  both 180-second compositions and the original five passing surfaces remain.
  All 341,008 paired controls, 56,655 replay labels and recorded learning rows
  verify. Reject promotion; keep V30. The experiment is complete, not walking
  acceptance. See `experiments/walking/RETENTION-RESULTS-v50.md`.
- [x] V51/V52 bounded braking activity complete. Three first-stop demonstrations
  admitted after 384 retargeting candidates; one 2,000-update supervised run
  survives both successive stops in both downhill sessions. All still fail yaw.
  Flat retention is 38/63, endurance 0/2 and surface sessions 3/14. Reject V52;
  keep V30. Every action, source, label and load trace verifies. See
  `experiments/walking/BRAKING-RESULTS-v52.md`.
- [x] V53 bounded retention experiment complete; rejected. Nine original-actor
  continuations supply 930 verified recovery labels. One 8,000-update fit
  restores 63/63 flat and the original five surface passes. Both 180-second
  sessions survive, but one fails heading (1/2 accepted). Downhill start 1 falls
  at 14.24 s; start 2 fails yaw/posture/heading. Keep V30; do not extend V53.
  See `experiments/walking/BRAKING-RESULTS-v53.md`.
- [x] Review capability feasibility against primary robotics research and the
  pinned official MicroDuck recipe. The evidence supports staged locomotion
  development; it does not prove arbitrary-terrain feasibility. Record upstream
  model/command/curriculum differences, local V44/V50/V52/V53 limitations and
  the proposed next comparison in
  `docs/workspace/CAPABILITY_FEASIBILITY_RESEARCH.md`. Research only; no new
  training, policy promotion, physical work or protected-bank inspection.
- [x] **V54 locomotion-recipe comparison frozen, September 9.** Audit pinned
  upstream command, actuator and collision compatibility; compare the existing
  routed walking/standing design with a shared command-conditioned actor under
  declared transition curricula and retention constraints. Freeze initialization,
  actual experience-coverage requirements, budget, seeds and decision rules before
  launch. Preserve native physics and every existing gate. Critic/history changes
  are separate ablations; a preferred recipe is not yet established. Require all
  old flat/endurance/surface retention plus both complete downhill sessions before
  broadening terrain evaluation. Protocol: `experiments/walking/RECIPE-COMPARISON-v54.md`.
  Static upstream audit, 83,700 retained examples, 140 workspace tests and three
  focused tests pass. The design item is complete; execution/acceptance is below.
- [x] **Complete and review both V54 recipes.** Both bounded main runs, smokes,
  initialization, all 72 conformance reports and all eight evaluation banks
  complete. Routed: 63/63 flat, 1/2 full compositions, 0/2 downhill, original
  5/14 surfaces. Shared: 63/63, 2/2, 0/2 and original 5/14 respectively; both
  downhill sessions now survive repeated stops, but yaw and one final face-pitch
  gate fail. Both arms have long completion in 18/24 training cells. Combined
  artifact/action/physics-load verification passes; advancement is false.
  Research/results reassessment: `experiments/walking/RECIPE-RESULTS-v54.md`.
  Broader terrain and adaptation stages remain unexecuted, not implicitly passed.
- [x] **V55 yaw-focused shared-policy refinement frozen, September 12.** Use V54 shared
  as the development starting point and a matched control, with one changed
  objective group, exact budget/selection rules and unchanged physics. Reduce
  downhill walking yaw oscillation while retaining all flat, full-composition,
  surface and newly observed stop behavior. Require yaw <=0.20 rad/s, face pitch
  <=30 degrees, every other original gate and all 24 long training cells before
  replication across two further training seeds and terrain expansion. Keep V30
  retained until prerequisites pass; critic/history interventions remain separate.
- [x] **Execute and review V55; neither final accepted.** Two final-only 2,592,000-transition arms,
  control yaw weight 3 and intervention 6, identical V54 shared actor/critic.
  Read every old regression and both new heading-interpolation sessions; verify
  all stored action/reward/coverage evidence before selecting the next step.
  Protocol: `experiments/walking/YAW-REFINEMENT-v55.md`.
  Both full runs and all 11 banks complete; 63/63 flat and 5/14 surfaces retained
  by both. Full compositions control 2/2, yaw6 1/2. Yaw6 survives four downhill
  sessions but all eight windows fail yaw/final face pitch; both arms have
  long completion in 22/24 training conditions. 201,838 ONNX actions and
  807,352 load samples verify. See `experiments/walking/YAW-RESULTS-v55.md`.
- [x] **September 15 community and X research complete.** Trace current posts to
  pinned primary sources; distinguish simulation results from physical trials.
  Current upstream VelStand selects its full-collision model, unlike the pinned
  September 8 audit, and the runtime documents a real-daemon simulator.
  Findings and capability priorities: `docs/workspace/COMMUNITY_RESEARCH_20260915.md`.
  No candidate, training run or physical capability was admitted.
- [x] **September 15–16: upstream comparison and standing feasibility complete.**
  Audit the new VelStand contact/impact configuration against complete-contact-v11;
  floor-impact sensors do not replace internal-load rejection. Check local
  compatibility of the official real-daemon simulator and specify an exact-actor
  walk/turn/stop rehearsal. Check standing target feasibility under the active
  downhill physics. Keep source freezes, gates and runtime contract unchanged.
  Owner explicitly authorized bounded subagents in this request. All simulator
  launches are serialized in the current task. V56 feasibility protocol:
  `experiments/walking/posture-feasibility-v56.json`; planned paired ablation:
  `experiments/walking/POSTURE-REFINEMENT-v56.md`. Upstream source audit lives
  in `experiments/walking/upstream-audit-v56/`; runtime work in
  `experiments/runtime-rehearsal-v1/`. No model or policy is promoted by these audits.
  Thirty complete standing/assisted diagnostic cases do not supply an all-case
  25-degree witness; 15,000 action rows and 60,000 load samples verify.
  See `experiments/walking/POSTURE-FEASIBILITY-RESULTS-v56.md`.
- [x] **Full-CAD static diagnosis and bounded proxy experiment complete.**
  V11 has 11 active colliders, current upstream 70. The separately versioned
  V57 model with jaw/neck enabled overlaps in 201/201 copied poses, while the
  upstream exclusion hides those contacts. Eight original-surface checks locate
  false-filled cavity witnesses, without proving global clearance. V58's one
  frozen decomposition configuration generates all four meshes but all fail the
  0.25mm sampled excess-material limit; bearing part 52 prevents compilation.
  Eight posthoc cavity-point checks pass without satisfying the missing compiled
  gates. No retry, dynamics or model admission occurred. Keep the frozen partial report
  and missing compilation-dependent gates explicit.
  Evidence: `experiments/walking/contact-reconciliation-v57/README.md`.
  Negative proxy result: `experiments/walking/contact-reconciliation-v57/proxy-experiment-v58/README.md`.
- [x] **V59 compiler prerequisite and independent material regression complete.**
  One fragment's mesh-inertia attribute resolves compilation, preserving all 62
  checked physical/actuator arrays, names and contact coverage. All 256 compiled
  proxy shapes preserve source world vertices within 3.740nm; 201 copied poses
  show no internal overlap. V58's material rejection remains unchanged. The
  compiler-independent validator reproduces 44 old metric fields exactly and
  passes nine synthetic tests. `experiments/walking/contact-reconciliation-v57/proxy-diagnostics-v59/README.md`.
- [x] **V60 bearing cap comparison complete; component gates pass.**
  One cap-only 64-to-256 change reduces sampled excess from .343090 to .217129mm.
  Material checks pass; separately frozen assembly preserves all 62 checked
  physical/actuator arrays. The partial robot still contains other unrepaired
  shapes. `experiments/walking/contact-reconciliation-v57/bearing-hull-cap-v60/README.md`.
- [x] **V61 remaining-shape comparison complete; no complete model admitted.**
  One fixed attempt each produces convex/watertight proxies, but sampled excess
  remains bracket .286053mm, shell .939718mm and jaw .663937mm against .25mm.
  All eight cavity-point checks pass; all three excess-material failures remain.
  No retry, complete assembly or dynamics follows this failed material gate.
  `experiments/walking/contact-reconciliation-v57/head-hull-cap-v61/README.md`.
- [x] **V62 remaining collision geometry repaired and verified.**
  Source-aware bracket/jaw partitioning and a bounded local hybrid shell produce
  614/1,781/4,875 parts; V60's 256-part bearing remains unchanged. All .25mm
  material limits, eight cavity checks and 4,664,668 additional samples pass.
  A separately versioned query-unit correction resolves a demonstrated numerical
  shell false failure; the raw V59 negative is preserved. Complete assembly:
  7,592 colliders, all 62 physical/actuator arrays exact against V57, unchanged
  names/contact settings/required pair coverage, no explicit exclusions, 2.884nm
  maximum vertex discrepancy, zero internal penetration in all 201 copied poses.
  All 36 V62 tests and 141 workspace tests pass. No dynamics or physical claim.
  `experiments/walking/contact-reconciliation-v57/surface-refinement-v62/README.md`.
- [x] **V63 startup/load/performance probes executed; diagnostic gates fail.**
  Twelve terminal cases and 11,412 physics samples independently verified; all six
  repeat pairs have identical arrays/dynamics. Both V11 replays reproduce 900
  retained intervals and 3,600 torque vectors exactly. Fixed HOME falls on both
  models (~1.24 s); V62 passive stops at 0.540 s on 10.336 mm floor penetration, and
  its frozen-action replay falls at 2.505 s. The new 3 mm floor gate also rejects
  the V11 control at 3.975 mm; historical actor scores stay unchanged. Candidate
  replay p99 is 2.400–2.612 ms over its prefix, not full-duration acceptance.
  Seven focused tests and 141 workspace tests pass. No new walking/physical claim.
  `experiments/walking/startup-load-v63/README.md`.
- [x] **V64 foot–ground and integration diagnostics executed; gates remain negative.**
  Verified 28 cases, 33,616 physics samples and 14 exact repeat pairs. Eight
  controls reproduce V63. Matching 27 physical arrays to V11 falls at 2.505 s;
  disabling only two shell/floor pairs falls at 2.485 s. Sixteen CAD support
  checks agree. At 2.5/1.25 ms integration V11 falls at 1.705/1.64125 s; V62 also
  falls. None of four finest-step agreement screens passes. The original 3 mm
  floor gate stays unchanged. Seven focused and 141 workspace tests pass.
  Premature isolation attempts are quarantined; fresh cases followed verified
  controls. `experiments/walking/contact-isolation-v64/README.md`.
- [x] **V65 force-feedback timing and matched sole impact investigated.**
  Verified 56 cases, 56,302 physics samples, 21,744 BAM input records and 28 exact
  repeat pairs. Sixteen controls reproduce V64. Fixed 5 ms force-input age preserves
  clocks/action bytes/solver state but does not rescue the finer-step replays;
  all four robot numerical screens fail. All 32 guided CAD ankle drops pass
  diagnostic checks and eight cross-asset screens agree, but all four finest-step
  contact screens fail: 0.159468 mm position and 0.126729 mm penetration-peak
  differences exceed 0.1 mm. Nine focused tests pass. Prior V62–V64 evidence is
  unchanged. `experiments/walking/feedback-contact-v65/README.md`.
- [x] **V66 guided first-impact numerical gate passes across all timing buckets.**
  All 96 cases, 358,400 physics samples and 48 repeat pairs verified; eight
  controls reproduce V65. Every diagnostic and analytic audit passes. All sixteen
  0.3125/0.15625 ms buckets meet the frozen 0.1 mm limits: worst position
  difference 0.064698 mm, penetration-peak difference 0.061970 mm. All 24
  cross-asset comparisons pass. The coarser pair still fails P2 for every model
  (12/16 pass), so do not promote it from nominal-phase agreement. Seven focused
  tests pass. This admits only the fine guided-bench candidate reference.
  `experiments/walking/impact-convergence-v66/README.md`.
- [ ] **Proposed; pending process review: isolate full-robot impact integration from BAM feedback.**
  Reproduce the nominal prefix; capture complete solver/warm-start, BAM target/
  previous-torque, applied friction/damping and FIFO state at 0.035 s, before
  both models' first loaded floor interval at 0.040 s. Freeze 0.035–0.135 s
  windows with exact 5 ms clone controls against V65 before fine-step cases.
  First replay the same recorded motor/friction/damping schedule at 200 Hz to
  isolate plant integration; live BAM feedback follows as a separately frozen
  stage. Keep the robot's numerical limits and physics-rate internal/floor load
  telemetry. Do not reconstruct complete solver state from qpos/qvel alone.
  No retained actor/controller changes or full-robot reference admission from
  the guided bench alone. Open-loop diagnostics are not closed-loop scores.
- [ ] **Then runtime integration and a new walk/turn/stop rehearsal.**
  Connect the tested command adapter to the actual BAM evaluator with exact
  command/actor routing and delay states. Use an explicitly tested immediate
  standing-policy handoff; fixed HOME has failed in V63. Resolve HOME_RAMP
  before treating a rollout as a policy score. The existing 3,300 inference rows
  and 19,800 adapter intervals prove components, not daemon/body compatibility.
- [x] **Sensor-driven following baseline evaluated.** V3 in
  `experiments/visual-follow-v1/RESULTS.md` completes 18 sessions and passes 11/16
  required cases; two stationary negatives correctly reject. Independent
  RGB/timestamp replay verifies 27,000 commands and 27,000 exact actor outputs.
  All fault-stop checks pass; combined conditions lose view and three
  reacquisition cases fail yaw. Original reflection/visibility failures remain.
- [ ] **Then isolate the first sensor-following failures.** Restore one active
  property group at a time at combined-case clipping at 1.6 s; separately inspect
  camera/face pose during stop→reacquire. Freeze a new candidate before rerunning
  every exposed case. Fresh layouts remain closed and the unused offset-bay
  factors need a supported, versioned amendment. Proximity-aware navigation,
  unfamiliar layouts and broader physical admission remain later stages.
- [ ] **Prepared; blocked on feasibility: neutral-standing face-posture ablation.**
  Start from the retained V54 shared development state; test a standing-only
  objective aligned with the physical world-space face metric, with headroom
  below the unchanged 30-degree gate. Leave yaw, physics, 61D/14D ABI,
  curriculum and other objectives unchanged. Require all four original/new
  downhill sessions, all 63 flat cases, both compositions, retained surfaces
  and every original component gate. V55 yaw6 is an unaccepted survival
  comparator, not an imitation source. Diagnose remaining yaw/coverage before
  replication; keep critic/history/advantage interventions separate.
- [x] **Recovery readiness assessed; non-actuating handoff preview implemented.**
  `experiments/recovery-readiness-v1/README.md` records 16 synthetic tests,
  source-pinned official artifact metadata and six missing admission inputs.
  Contact availability is unknown; sensor quiescence is not ground-support proof.
- [ ] **Recovery capability gate:** bind or train a first-party seated-to-stand
  candidate after the full-CAD surface/load gate. Require an admitted sitting
  endpoint, continuous state, actual loads, no-op/V15 comparisons and separate
  support rules before extending to prone/supine/side starts or walking handoffs.
- [ ] **Deferred diagnostic, if selected by that comparison:** freeze one
  offline fit-feasibility experiment with separate maximum-error
  gates for successful-stop retention and downhill recovery, including each
  stop onset. V53 reduces zero-label errors but leaves .077870–.206272 rad
  errors on the four downhill onset labels. Require both fitting gates before
  full rollout evaluation; do not call a dataset fit behavior success. Only
  consider changing this residual's architecture/inputs after diagnosing an
  infeasible joint fit; this restriction does not select the separate locomotion
  recipe above. Missing observability is not established. Preserve V15 standing, all 63 flat,
  both 180-second and five original surface gates, successive downhill stops
  and the .20 yaw limit. Fresh/protected banks remain closed.
- [ ] Expand the shared walking capability through the staged carpet/terrain
  strategy in `docs/workspace/TERRAIN_GENERALIZATION.md`: measured contact
  models, verified mixed training, unfamiliar physical specimens/layouts,
  whole-session surface transitions and separate physical admission. Carpet
  is a curriculum/test family; no carpet-trained or carpet-validated claim yet.
- [ ] **Physical calibration:** collect/recover Ducky-specific raw measurements,
  freeze fit/validation identities, calculate uncertainty and held-out residuals.
  Empty intake currently returns `blocked_inputs`; actuator, inertia, sensing
  and contact stages remain missing. Local tooling cannot replace measurements.
- [ ] Before admitting locomotion to the behavior library, execute the complete
  `docs/workspace/BEHAVIOR_VALIDATION.md` matrix: effective randomized training
  and testing, unseen terrain/environment families and combined shifts,
  repeated transitions, preregistered per-bucket statistical decisions, and
  physics audits/calibration with explicit unresolved gaps. Existing 21+42
  flat-floor timing cases do not establish broad environmental generalization.
- [x] Retain v8 64x5 smoke: 7,680 transitions, 59.3 seconds, all 29 source
  hashes match. Added balance and admission tests pass; full regression suite
  also passes. Neither smoke nor tests establish behavior acceptance.
- [x] Add a separate exposed cumulative-heading diagnostic without changing
  any old score: `HEADING-v1.md`, six tests, retained v5 baseline 3/21 heading
  and 2/21 old-plus-heading. A yaw-rate MAE pass alone is not straight walking.
- [x] V6 contact smoke passed: 7,680 transitions, 58.4 seconds, 25 source
  hashes unchanged. Retained with contact and process-inventory tests in
  `receipts/walking/20260905-v6-smoke-complete/`. Bounded 36,864,000-transition
  consolidation run completed; the exact final is retained and all three
  complete evaluations are retained as 0/21. Preserve source/final-only selection.
- [x] Isolate native IMU sampling phase on copied state: old IMU was one 5-ms
  tick stale beyond its declared FIFO. `ConsistentSensorWalkingWorld` refreshes
  only a separate data copy; fixed motor commands retain byte-identical physics.
  V3 nominal turn stop improves from 0.095 to 0.0016 m/s, but current-sensor
  baseline is still 0/21 (head posture 21/21). Preserve old results/protocols.
- [ ] Reconcile training/evaluator foot clearance and contact semantics with
  closed-loop traces in both engines; separately audit inertia/contact handling
  and missing body-floor contacts. Change models only from measured evidence,
  in a versioned lane, preserving the frozen reference model and action ABI.
- [x] Add a bounded full-collision native fixed-action check. V5 slow forward
  and left turn have byte-identical 900-frame poses between reduced and full
  collision models, with no new sampled contact pairs or falls. Raw and BAM-
  configured model checks are separate. This does not prove all-case/physical
  contact fidelity. Evidence: `20260905-v5-full-collision-replay-r2`.
- [x] Audit compiled HOME link frames, COMs, full inertia tensors and sole
  geometry; identify Genesis floor masks 65535/65535 versus native 1/1. Add
  the separately versioned `MicroduckGroundAlignedWalkingEnv`: AST test proves
  the masks are the only scene-builder change, runtime masks match, and paired
  100-step replay keeps action/state bytes identical in the tested prefix.
  Extra body-floor geoms stayed clear in 3,600 retained v2 probe frames; do not
  misattribute those failed walks to this inactive discrepancy. The already
  running v3 is not hot-patched; use aligned floor for a future training version.
- [x] Expose the reduced native model's non-foot-floor rejection blind spot:
  only feet can contact the floor. Cross-check 3,600 nominal v2/v3 poses against
  the identical-inertia full-collision CAD variant; no hidden body penetration,
  minimum clearance 14.95 mm. Keep this copied-state geometry result separate
  from full-collision dynamics and physical proof.
- [x] Check v3 final full-body clearance: 18,900 frames, zero penetrations,
  minimum non-foot mesh clearance 14.27 mm. This is copied-state geometry.
- [ ] Before any transfer claim, independently evaluate full-collision dynamics,
  not only foot-contact physics; repeat clearance checks for later candidates.
- [ ] Before a physical handoff, reconcile the exact installed hardware/runtime
  with this unfiltered actor and explicit IMU heading controller. The current
  upstream runtime has different default filtering/action scaling and its
  relative IMU yaw can drift; do not silently change either side. See
  `experiments/walking/DEPLOYMENT-GAPS.md` for pinned sources and required
  measured frame/timing/geometry checks. No hardware has been operated.
- [x] Localize cross-engine divergence with original byte-identical action
  arrays at 200 Hz. Identify a 10-ms Genesis versus 20-ms native default
  constraint-timing mismatch; implement a separately versioned 20-ms model.
  First-impact root mismatch drops from 0.95 to 0.049 mm and load from 59.96
  to 31.66 N (native 32.28 N), without changing action bytes. Five-second
  drift remains about 19 cm: this does not close dynamic/physical fidelity.
- [ ] Reconcile remaining solver configuration/contact-response differences
  with source-backed fixed-action diagnostics before another model intervention.
- [ ] Train and pass that bounded basic-locomotion lane before reintroducing
  laser pursuit/DR. Keep the v4 reserved bank unopened; do not weaken failed
  thresholds or promote the no-step candidate.

- [x] Freeze waypoint jumps, circles, figure eights, target loss/reappearance,
  development seeds, reserved development seeds, and fixed thresholds.
- [x] Build a local interactive simulation with drag/keyboard target control,
  real robot/target trails, explicit pause/reset, and fresh-domain trials.
- [x] Add a separate robust curriculum without changing frozen L1 training:
  full-direction retargeting, curved motion, dropouts, grip/mass/COM/motor
  randomization, sensor noise/delays, and gradually introduced small pushes.
- [x] Pass a 64-environment × 5-iteration smoke.
- [x] Finish bounded 1024 × 400 PPO, retain checkpoint/export/config/learning log.
- [x] Diagnose persistent turn-in-place stagnation (first DR pass remains 1/6);
  retain the negative and run one frozen 1024 × 250 turn-reward correction.
- [x] Compare fixed candidate against L1 on dynamic development and old
  regression cases; freeze choice before reserved development evaluation.
- [x] Preserve all negatives and report randomized comparison, export parity,
  complete trajectories, actual videos, browser QA, and checksums.
- [ ] Isolate the early startup fall on development seed 75003 with property
  ablations and a bounded new intervention; reserve a fresh test bank before
  further tuning. Do not train against consumed reserved seed 75109.
- [ ] Extend perception robustness only after the camera loop is connected;
  do not call floor-color changes visual generalization.
- [ ] Separately specify obstacle/uneven-terrain tasks and physical validation.

Build record: `experiments/laser/DYNAMIC_BUILD.md`. Current trials are flat-ground,
privileged-target development, not canonical held-out or physical acceptance.
Historical target-only result: nominal dynamic 3/3; randomized development 5/6;
reserved development 11/12 versus the old policy's 2/12; original regression
6/6. One development and one reserved case fall early. That previously selected
policy is now explicitly rejected for gait; walking and robustness exit gates
remain open. Repeated development
replay matches all 12,078 semantic rows exactly, excluding inference timing.

### L1 — Laser-following RL (target-only simulation result; gait and camera open, 2026-09-04)

This explicit local-development request takes priority over waiting for
official upstream provenance. It does not close M2/M5/M6 or authorize hardware.
Work remains in this single task; do not revive reviewer/executor cycles.

- [x] Research the Microduck laser demo and primary runtime/training sources.
- [x] Add a separate 61D-compatible laser command/reward environment; preserve
  the frozen walking/M5 source bindings and unfiltered 14D actions.
- [x] Run a 64-env × 5-iteration smoke; test steering parity, target loss,
  detection, ambiguity, and distractor rejection.
- [x] Freeze six visible C MuJoCo/BAM development cases before inspecting the
  trained result; baseline is 2/6 (stop/loss only), 0/3 target acquisitions.
- [x] Finish local 1024-env × 500-iteration PPO fine-tuning (12,288,000 new
  transitions) from the digest-verified first-party baseline.
- [x] Retain final checkpoint, config, source hashes, stdout, normalized ONNX,
  export parity, full evaluator records, videos, and checksums.
- [x] Inspect behavior and compare target acquisition, stopping, loss, moving
  target tracking, and falls against baseline; iterate on measured failures.
- [x] Diagnose the first failed result and preserve it: trained v1 stopped
  25.1–25.6 cm away (2/6 C MuJoCo cases); v2 strengthens only the approach
  velocity command, with unchanged policy bytes and thresholds, and passes 6/6.
- [x] Audit the locked head-camera frame and retain its HOME image; forward
  positive-X targets are behind that camera. Do not silently alter frozen assets.
- [ ] Connect camera pixels to metric targeting and validate the actual vision
  control loop. Current targets are privileged simulator coordinates.
- [ ] Separately authorize and validate physical laser following.

Implementation/reproduction: `experiments/laser/README.md`.
Receipts: `receipts/laser-follow/`; completed run: `logs/laser-follow-20260904-v1/`.
`20260904-v2-steering/` is a 6/6 visible-development simulated target-following
result: 20.9–21.4 cm stand-off on distant stationary dots, settled near/lost
targets, and 100% moving-target tracking within 28 cm after the 4 s warmup.
No falls occurred. This is not camera-loop, blind held-out, or physical proof.

### B1 — Capable behavior library (future owner direction; blocked on L2 foundation)

This is the ordered library backlog, not a second active milestone. Architecture
and claim boundaries: `docs/workspace/BEHAVIOR_LIBRARY.md`.

- [x] Define behavior contracts, perception/decision/execution boundaries,
  staged capability families and continuous-state transition acceptance.
- [x] Make per-behavior testing, domain randomization, generalization and
  physics validation mandatory in AGENTS/workflow/validation standard. Add
  v2 draft quality-plan completeness checks; these do not admit capabilities.
  Seven new lint regressions and all 129 workspace tests pass, without physics.
- [ ] For each behavior, freeze and execute its applicable six-part validation
  plan, retain materialized parameter coverage and disjoint environment splits,
  and show per-bucket/repeat outcomes plus actual success/failure footage.
  Deterministic controllers and compositions receive randomized tests too.
  No "fully tested" or "accurate physics" claim beyond the verified envelope.
- [ ] After walking passes its development gates, implement a small catalog
  and validator: unavailable by default, exact model/controller/policy IDs,
  actual inputs, bounded parameters, lifecycle, evidence and failure reasons.
- [ ] Implement one tested stand/walk/turn/stop composition with one actuator
  owner, interruption/cancel/timeout handling, and no hidden simulation or
  action-history resets between behaviors. Test invalid and stale inputs.
- [ ] Establish safe head attention and the verified camera/sensor contract;
  the current neutral-head actor is not proof of arbitrary head-motion control.
- [ ] Restore laser/visual-target following through actual rendered pixels,
  with target loss, persistence and reacquisition; require pursuit AND gait.
- [ ] Expand to approach/park, waypoints and obstacle avoidance within measured
  sensing and physical envelopes; evaluate complete transitions and sequences.
- [ ] Add recovery and expressive/dynamic behaviors only after reachable states
  and mechanics are established. Never equate zero actions with safe stopping.
- [ ] Grow timing/sensor/physics/terrain/visual variation in declared stages;
  retain worst-bucket outcomes and actual success/failure videos. Keep physical
  validation separately authorized and calibrated.

### M0 — Freeze and reproduce the Apple baseline (P0)

- [x] Separate the Apple dependency lane from vendor-PyTorch ROCm/CUDA installs.
- [x] Pin Genesis 1.3.3, PyTorch 2.9.1, and rsl-rl 5.4.2 in a hash-locked macOS arm64 environment.
- [x] Provide explicit Metal/MPS walking and backflip 64-env x 5-iteration commands.
- [x] From a clean clone, run `./scripts/setup_apple.sh` on Apple Silicon.
- [x] Run `python tests/run_all.py`; record every skip, especially missing BAM/checkpoint coverage.
- [x] Run `./scripts/run_apple_smokes.sh` for both bounded tasks.
- [x] Retain clean-run stdout, configs, checkpoints, and SHA-256 manifests.
- [x] Export both smoke checkpoints and run Torch-versus-ONNX randomized and real-observation checks.
- [x] Record machine model, macOS, Python, Torch, Genesis, MuJoCo, rsl_rl, commit, and dirty-tree state without recording a hardware serial.

Exit gate: a second clean Apple checkout reproduces both 64x5 smokes and ONNX
checks from the committed lock. Receipt root: `receipts/apple-baseline/<run-id>/`.

Local readiness verification on 2026-09-01 (current dirty checkout): the locked
environment installed and selected Genesis Metal plus Torch MPS; the full test
runner passed after updating two stale Genesis 1.2 API references. BAM formula
and full MuJoCo+BAM-loop tests skipped because the optional authoritative BAM
checkout was absent. Walking ran at 560–785 env-steps/s and backflip at 622–910
over five iterations. Single-file ONNX randomized parity was at most 3.695e-6
rad; both real-observation checks were 1.341e-7 rad. This is pipeline evidence,
not gait, backflip-success, held-out, or physical evidence.

M0 closed on 2026-09-01 with clean-clone receipt
`receipts/apple-baseline/20260901T215219Z-2ce72a94/`, bound to source commit
`2ce72a9492789c23d2191c7517e28a5b6bb12678`. All 20 manifest entries are
tracked and verified. Walking randomized/real-observation ONNX parity was
2.146e-6/1.341e-7 rad; backflip was 4.768e-6/1.043e-7 rad. This promotes only
reproducible `artifact_validated` pipeline evidence.

### M1 — Establish the shared semantic contract (P0)

- [x] Freeze repo-local model/asset, observation, action, control, and BAM input snapshots.
- [x] Fail CI when generated snapshots drift from their source.
- [x] Add BAM open-loop golden vectors and reset/internal-state fixtures from the authoritative BAM implementation.
- [x] Add short 14-servo closed-loop trajectory fixtures.
- [x] Make the official mjlab/MuJoCo Warp adapter consume and pass the same fixtures.
- [x] Reconcile Genesis/MuJoCo model counts, collision variants, masses, inertias, keyframes, joint limits, and actuator ordering.
- [x] Define the walking semantic file, including training-only curriculum state, 28 classified backend fields, and a preregistered zero-assistance success battery.
- [x] Define the backflip semantic file, including assistance/reverse-curriculum state and ordinary-start zero-assistance success definitions.
- [x] Submit the backend-independent contract upstream or record an explicit versioned divergence decision.

Exit gate: Genesis and official mjlab pass byte-identical interface fixtures and
thresholded BAM/model conformance tests. Model variants remain distinct.

M1 closed on 2026-09-02 with a local, not-submitted versioned divergence
decision covering all 45 non-exact walking/backflip semantic fields. The
deployed 61D/14D/50 Hz interface and BAM/model conformance are retained; no
training-trajectory equivalence, task success, held-out result, transfer, or
physical authority is claimed.

### M2 — Build the independent C MuJoCo evaluator (P0)

- [x] Create a CPU-only evaluator using official MuJoCo, BAM's C controller, ONNX Runtime CPU, 5 ms physics, decimation 4, and no action filter.
- [x] Import the observation builder and model lock by pinned authority; do not reuse a training backend's self-reported metrics.
- [x] Implement deterministic standing, command-grid, start/stop/reversal, perturbation, friction, joint-margin, NaN, deadline, and termination cases.
- [x] Emit `evaluation.json`, `trajectory.parquet`, `rollout.mp4`, `environment-lock.json`, and `attestation.json` bound to the exact policy digest.
- [x] Split visible development cases from held-out acceptance seeds/cases.
- [ ] Prove deterministic reports with the official walking ONNX when its immutable provenance arrives; this official-reference gate does not block separately admitted first-party development.
- [x] Evaluate one provenance-admitted first-party Genesis policy twice on a frozen visible-development suite with measured latency and no held-out seeds.

Exit gate: repeated evaluation of the same ONNX and suite ID yields identical
classification and stable numerical metrics within declared tolerances.

Core accepted on 2026-09-02: official MuJoCo C through Python bindings,
single-thread ONNX Runtime CPU, and pinned BAM `MujocoController` produced two
byte-identical 40-step infrastructure reports from the retained zero-policy
fixture. Both walking and backflip model lanes validate. This does not close M2
or evaluate task success; the full artifact bundle and designated official
walking ONNX repeatability proof remain open.

Development bundle accepted on 2026-09-02: two public non-candidate cases emit
all five required artifacts. Two same-host runs reproduced every artifact byte,
including 160-row Parquet and 40-frame decoded MP4 outputs. This remains
infrastructure-only; deterministic acceptance cases, held-out separation, and
the designated official walking ONNX proof remain open.

First-party learned-policy development completed on 2026-09-04 without using
the unavailable official checkpoint: two 800-step visible-development runs of
the exact new ONNX had identical semantic outputs, trajectory bytes, and video
bytes while retaining measured wall-clock inference latency. This satisfies the
separate first-party development item only. It does not satisfy the official
reference, success-classifier, or held-out acceptance gates.

Official walking authority search stopped on 2026-09-02 with durable result
`official_policy_authority_missing`. The exact project-owned runtime/Hugging
Face artifact is 61D-to-14D, contains a Sub/Div normalizer, and is immutable at
SHA-256 `e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
Neither its ONNX metadata nor the project-owned schema-v2 manifest binds a
checkpoint, training run, exact task-source commit, exporter invocation, or the
normalizer statistics to their source. It was not executed. M2 remains open;
only the official-policy repeatability sub-gate is blocked until upstream
supplies one of the acceptable authority paths recorded in
`microduck_contract/policies/official-walking-authority-v1.json`. Independent
local evaluator cases, held-out preregistration, and M3 classifier work remain
authorized.

BAM authority materialization corrected on 2026-09-02: fresh checkouts now
fetch and detach at the exact locked commit rather than the moved
`mjlab_frictionloss` branch. A local-git regression proves later branch movement
cannot repin the checkout; existing BAM fixtures and evaluator evidence were
not regenerated.

Deterministic case matrix accepted on 2026-09-02: ten visible zero-policy cases
cover all nine required infrastructure families with byte-identical repeated
reports. This is not held-out or task-success evidence.

Held-out protocol accepted on 2026-09-02: visible development data and public
acceptance definitions are distinct from an unrealized seed set derived only
from public randomness published after an immutable candidate freeze. No live
beacon, held-out seed, candidate, or result was inspected.

### M3 — Freeze task-specific success gates (P0)

- [x] Walking: predeclare command ranges, survival duration, tracking error, fall rate, stop drift, foot slip, orientation, and joint/torque margins.
- [x] Backflip: require ordinary standing start, zero assistance, takeoff, one uninterrupted airborne revolution, feet-first contact, landing orientation, and continuous stable hold.
- [x] Store curriculum start populations separately from acceptance start populations.
- [x] Test the classifiers against known positive, assisted, and failure trajectories.

Exit gate: success state machines classify fixtures correctly before any final
candidate results are inspected. PPO return is never a success definition.

M3 closed on 2026-09-02 with executable classifiers covering all 230 walking
cells and 20 ordinary-start backflip cells. Synthetic positive fixtures pass;
assisted, metric-failure, and incomplete-coverage fixtures fail closed. No
policy trajectory or candidate result was inspected.

### M4 — Characterize Apple scaling and stability (P1)

Harness implementation accepted on 2026-09-03 at commit `05c05e3`: it records
a real Metal/MPS PPO iteration, clean source/package/machine provenance,
finiteness, thermal-method limitations, and an explicit peak-RSS unified-memory
proxy. M4 remains active pending the preregistered sweep, sustained stability,
and CPU+MPS fallback crossover.

Primary scaling sweep accepted on 2026-09-03: all five sizes through 1024 were
finite, thermally nominal by the declared `pmset` warning-state method, and
above 97.75% RSS-proxy headroom. At 1024, total PPO iteration was 4.271 s and
total-iteration-derived throughput was highest at 345,246 samples/min. This
selects only the preregistered sustained-test candidate, not the default.

Sustained 1024-environment stability accepted on 2026-09-03: 120/120 measured
iterations were finite, all 15 declared thermal samples were nominal, RSS-proxy
headroom was 97.15%, and last/first median iteration slowdown was 0.9730 against
the frozen 1.25 ceiling. It remains eligible as the everyday default; M4 still
requires the CPU+MPS fallback crossover.

Matched fallback grid accepted on 2026-09-03: CPU+MPS is operational and had
lower median total PPO iteration than Metal+MPS at 64, 128, 256, and 512. The
honest frozen result is `>512`; one separately preregistered matched 1024 pair
will determine whether the on-grid crossover is 1024 or above the tested range.

M4 closed on 2026-09-03. The matched 1024 extension measured Metal+MPS median
total PPO iteration at 2.5271 s versus CPU+MPS at 3.0963 s, locating the grid
crossover at 1024. The everyday Apple default is therefore 1024 environments
with Metal physics and MPS learning; CPU+MPS remains the verified debug
fallback and was faster at 64-512. These are performance defaults only, under
the explicit `pmset` warning-state and peak-RSS-proxy limitations.

- [x] Benchmark 64, 128, 256, 512, and, if memory permits, 1,024 environments.
- [x] Record physics SPS, rollout time, PPO update time, synchronization, reset cost, peak unified memory, thermals, NaNs, and samples/minute.
- [x] Run sustained thermal tests and define the default everyday environment count.
- [x] Keep Genesis CPU + MPS as the debug fallback and record its crossover point.

Exit gate: a checked-in benchmark report selects defaults from measured total
iteration time and stability, not pure physics SPS.

### M5 — Run the decisive cross-backend training experiment (P1)

Immutable experiment contract accepted on 2026-09-03 at `b2a1ab6`: exact
sources/hashes, full actor/PPO configuration, public/candidate seeds, equal
transition budgets, predetermined checkpoints/normalized exports, evaluator,
held-out timing, decision rules, receipts, resumability, and a proposal-only
CUDA budget are frozen. Its 32-row dry-run executes nothing. M5 execution remains
blocked by official-policy authority, immutable CUDA container digest, and
explicit compute authorization.

Slice 026 amends only the execution-authority layer under dated Manager
authorization. It binds NVIDIA CUDA 12.8.1 cuDNN development Ubuntu 24.04 for
linux/amd64 at manifest digest
`sha256:3986465b3dd3b4d602c07061f2cff417e0bfb24810129408d4eb12e111015a6c`,
prefers one non-stoppable Brev `hyperstack_A100_80G` at $1.62/hour, and limits
the pilot to two hours/$3.24. The 32 experiment rows remain unexecuted and
unauthorized; an independent Reviewer must accept this amendment before the
pilot, and must separately accept the recovered pilot receipts before the
104-GPU-hour/$210 full CUDA envelope becomes eligible. Official-policy
provenance and held-out timing remain blocking gates.

Reviewer 026 returned `NO-GO`: the first amendment did not apply its digest in
the Brev create command, mislabeled `cloud=hyperstack` as the provider rather
than recording `provider=shadeform`, and left several safety rules mutable under
the semantic validator. Corrective slice 027 makes the actual container-mode
provisioning command digest-addressed, fixes the catalog fields, requires an
empty inventory and exactly one no-fallback workspace, and schema/validator
locks the pilot contents, recovery, independent checksums, deletion, and later
full-run Reviewer gate. Reviewer 027 returned `GO` for that bounded pilot.

The resulting slice-028 A100 pilot ended terminal-negative on 2026-09-03 before
any smoke training. The frozen Linux `requirements.txt` installed Genesis
1.2.2, but frozen validation/training source uses `RigidSolver.dyn_state`, which
is absent in that runtime; the authority-supplied suite therefore failed. The
failure receipt was recovered and independently checksummed, and Brev inventory
was verified empty after deletion. Reviewer 028 accepted closure only as
terminal-negative evidence; it did not accept the pilot as successful or
authorize another paid pilot/full CUDA execution. Any later CUDA route remains
blocked on a separately reviewed/refrozen Linux runtime reconciliation. No
candidate or held-out seed was executed.

Slice 029 locally refreezes that pairing to Genesis World 1.3.3 with exact
upstream release commit and wheel/source hashes. Its Python 3.12 linux/amd64
lock resolves 126 packages for Ubuntu 24.04/glibc 2.39 and Torch cu128; a
deterministic wheel probe proves 1.2.2 lacks and 1.3.3 exposes the required
`RigidSolver.dyn_state` assignment. The paid harness now validates the contract
before the suite and emits a terminal checksummed receipt on failure. Generic
receipt hygiene discovers every tracked manifest without altering the accepted
pilot-028 bytes. Local static/runtime checks and the full applicable Apple suite
pass; the Apple host cannot prove CUDA execution, and its linux/amd64 Colima
probe is blocked by absent QEMU. A precise second-pilot card exists only as
`proposed_not_authorized`; independent review plus a new durable Manager
authorization are required before any Brev creation.

Reviewer 029 returned `NO-GO / REDIRECT` because the refrozen lock named
`torch==2.9.1+cu128` while the harness install omitted the cu128 package-source
selection. Corrective slice 030 adds `--torch-backend cu128`, schema-binds that
install choice, and adds a standalone harness-equivalent regression using the
exact pinned `uv==0.8.19`, Python 3.12, and `x86_64-manylinux_2_39`. The replay
resolves all 126 hash-locked packages. This correction remains local evidence
awaiting independent review and grants no second-pilot or broader authority.

Reviewer 030 accepted slice 030 as local resolver evidence only. Fresh Manager
authorization 007 then opened exactly one second smoke pilot. On the A100, the
corrected Genesis 1.3.3 / Torch 2.9.1+cu128 runtime passed CUDA validation and
ran the full authority-supplied suite, which failed model-reconciliation,
evaluator-core byte, and evaluator-bundle determinism gates before any smoke
training. A Brev exec reconnect replay was interrupted before its suite and
overwrote the same receipt's terminal/cost metadata; Manager reconciliation 008
preserves that distinction and uses the conservative 1,515-second / `$0.681750`
create-to-empty bound. The final 24-file receipt was independently checksummed,
the non-stoppable workspace was deleted, and authenticated inventory is empty.
No checkpoint, candidate, held-out, ONNX, or task-success evidence was produced.

Slice 032 diagnoses the three terminal-negative suite gates without mutating
either pilot receipt or the frozen M5 experiment inputs. MuJoCo's compiled mesh
inertias differed between Darwin/arm64 and Linux/x86-64 only in 11 to 18
last-bit fields per variant (maximum absolute delta `1.0843e-19`); a 14-digit
semantic projection now compares the retained raw manifest instead of treating
its host-specific digest as cross-host authority. The evaluator report differed
only in truthful ONNX Runtime provenance and raw floating-point trajectory
bytes; an 11-decimal canonical row digest is byte-identical across measured
hosts while the raw provenance remains untouched. Development bundles now
exclude wall-clock inference jitter from their synthetic artifact bytes and use
single-sample offscreen rendering. Reviewer 032 correctly rejected the first
model projection because it rounded every float; follow-up `d741e60` limits the
14-digit projection exclusively to `bodies[*].inertia_kg_m2` and adds a
one-ULP mass negative probe that must remain visible. The focused gates and full
local suite pass again with pinned BAM and official MJLab authority. This is
local deterministic compatibility only; a third-pilot card exists with
`compute_authorized=false` pending re-review and separate Manager authorization.

After subsequent proposal corrections and independent acceptance, Manager
authorization 011 opened exactly one fifth-pilot workspace on the exact
`massedcompute_A100_sxm4_80G_DGX` row at `$1.656/hour`. The create command
briefly reported ready, but authenticated inventory remained or regressed to
`UNHEALTHY / BUILDING / NOT READY`; the sole SSH access operation exhausted 20
retries without obtaining a shell. Zero files were uploaded and the harness,
suite, training, smokes, and exports were never invoked. The exact-ID workspace
was deleted after 504 seconds create-to-empty, with a conservative estimated
cost of `$0.231840`; receipt
`receipts/m5/pilot/20260904T055749Z-i1bsb56r7/` is independently accepted and
authenticated Brev inventory is empty. This is terminal-negative provisioning/
connectivity evidence only. It proves no CUDA compatibility or M5 progress,
and Manager authorization 011 is consumed with no retry, replacement, or sixth
pilot authorized.

- [x] Freeze task semantics, reward, DR, actor/PPO configuration, transition checkpoints, seed list, and evaluator before candidate training.
- [ ] Development: at least three fixed public seeds per backend.
- [ ] Candidate comparison: five seeds per backend or a predeclared equivalent power analysis.
- [ ] Match Genesis Metal/MPS and official mjlab/CUDA by transitions, not iterations or wall time.
- [ ] Export every predetermined checkpoint through its canonical normalized ONNX path.
- [ ] Evaluate every frozen ONNX in the same held-out C MuJoCo suite.
- [ ] Compare time to threshold, task metrics, variance, and simulator/reference ranking consistency.

Exit gate: Genesis remains primary only if it is non-inferior on predeclared
reference outcomes. Higher training reward alone cannot close this milestone.

### M6 — Package immutable, attributable artifacts (P1)

Schema foundation accepted on 2026-09-03 at `973a204`: policy manifest v2 and
reference/hardware attestations bind all required artifact roles and keep
download, import, evaluation, approval, activation, task evidence, and physical
authority separate. Validation is byte-only against synthetic fixtures; no real
policy is accepted or executed.

File-level inventory accepted on 2026-09-03 at `e91ac2e`: 70 files are covered,
with 63 complete, 2 partial, and 5 missing. Exact negatives are retained for
`ball.xml`, the actuator parameter source path, three policy weights, and two
media files. No dataset files are present and none are invented. M6 remains open
for real fully attributable official/community artifacts and publication under
separate authority.

Real-candidate resolution attempted on 2026-09-04 in slice 047. Immutable
official and community downloads validate byte-for-byte, but both fail policy
manifest v2 completeness. The official candidate binds 2/10 roles and the
community candidate binds 6/10; exact missing roles remain fail-closed and no
formal manifest or artifact authority was emitted. M6 therefore remains open.

Slice 048 searched the community candidate's complete immutable Hugging Face
tree/history, exact training-source tree, 1,000 accessible ancestor commits,
and anonymously available W&B surfaces. No source checkpoint, separate
normalizer, evaluator, raw evidence, or artifact-specific exporter invocation
could be bound; the candidate remains 6/10. The adjacent BAM parameter source
was resolved exactly, moving the file inventory to 64 complete, 1 partial, and
5 missing without changing policy authority.

Slice 049 traced the remaining partial `ball.xml` entry to byte-identical public
official source commit `84790795...`. The later `priority="1"` difference was
introduced upstream by `7831c514...`; it is not an undocumented Genesis
transformation. Exact license/source closure moves the inventory to 65 complete,
0 partial, and 5 missing. Reachable Git history plus all public forks, branches,
tags, releases, action artifacts, and inert media metadata resolved no
checkpoint/run/export/normalizer/evidence or file-level license authority for
the two demo files or three original ONNX policies. Those five remain missing,
M6 remains open, and no policy action was performed.

Reviewer 049 substantiated those facts but withheld acceptance because the v1
validator did not bind several material license/remote/media fields and its
153-commit scope included transient refs. Slice 050 preserves that receipt and
adds a corrected v2: exact accepted-base ancestry is 150 commits, every decision
field is bound by value and key coverage, and new rehashed mutation probes cover
all reported blind spots. The working 65 / 0 / 5 inventory remains pending
independent re-review; no artifact authority changes before acceptance.

Reviewer 050 accepted the corrected 65 / 0 / 5 inventory. Slice 051 derives a
deterministic local distribution allowlist from that accepted inventory: all 65
complete, license-bound, byte-identical source records are included, while the
two legacy media and three legacy ONNX files are retained but quarantined. A
versioned archive validates byte-only and can reach `staged_not_imported`; both
official/community ten-role policy-manifest requirements and publication stay
open pending independent review.

Reviewer 051 accepted every semantic and safety property but rejected the first
archive because Python 3.12 emitted gzip OS byte `0x13` while Python 3.9/3.13
emitted `0xff`. Slice 052 preserves that failed receipt and adds a corrected v2
whose gzip header is fixed to `1f8b08000000000002ff`; system, project, and
Python 3.13 builds now reproduce exact bytes pending independent re-review.

Reviewer 052 accepted the portable distribution gate. Slice 053 freezes the
remaining external handoff: eight official and four community missing roles,
acceptable immutable evidence, two copy-ready unsent requests, a preregistered
but unauthorized source/Hugging Face publication plan, and a repo-owned closure
audit finding no honest local substitute. Pending review, the next boundary is
external input, third-party contact, or human-authorized public release.

On 2026-09-04, the project owner explicitly authorized only the prepared Pollen
Robotics request. It was posted by `jakekinchen` as
`https://github.com/pollen-robotics/microduck_rl/issues/40`; the checksummed
contact receipt binds the destination, timestamp, authenticated identity, exact
sent-body digest, and unchanged source-draft digest. A response is pending. This
contact closes no official role, the official candidate remains 2/10, the
community candidate remains 6/10, and the community request remains unsent. No
artifact was published, imported, parsed, evaluated, approved, or activated.

The versioned first-party development amendment then removed the unnecessary
overall dependency on Pollen's unavailable checkpoint history without changing
the official-policy gate. From clean source `d050920`, public seed `26090401`
ran 1,024 Metal environments for 100 MPS PPO iterations from scratch: exactly
2,457,600 transitions, with no resume, tuning, seed search, or checkpoint
selection. Receipt
`receipts/first-party-development/20260904-walking-seed-26090401-v1/`
retains the source checkpoint, normalizer/order, fixed-batch normalized ONNX,
random and real-observation parity, two CPU MuJoCo/BAM/ORT evaluations,
trajectories, rollouts, real inference latency, and all digests. The policy is
`sha256:843d5d9aa788334d43e95607fb917af560c61550080c92357825d360fb5b690f`;
parity maxima are `3.338e-6` rad on 33 frozen probes and `5.365e-7` rad on 60
environment observations. Both 800-step evaluation passes have byte-identical
Parquet and MP4 plus canonical trajectory digest
`sha256:f8830fdfa416ba31174dfbcd2259e7e739de9eb71aa595db82e29856a6dde9af`.
Measured case displacement was only about 1.1 cm over two seconds and root
height fell about 6 mm, so this short smoke is not evidence of a useful gait.
It closes no official/community M6 role and does not open held-out, CUDA,
licensing/publication, transfer, activation, or hardware gates. The next local
work is additional preregistered visible-development diagnosis or a separately
frozen longer first-party run; Pollen issue 40 remains pending for exact
official-policy repeatability.

- [x] Add policy manifest v2 and reference/hardware attestation JSON Schemas.
- [ ] Validate one official and one community artifact without executing repository code.
- [ ] Bind ONNX, normalizer, source checkpoint, exporter, model, BAM, task, evaluator, evidence, and license files by SHA-256.
- [ ] Publish source on GitHub and immutable policy artifacts on Hugging Face.
- [x] Keep download, library import, evaluation, approval, and activation as separate actions.
- [ ] Resolve file-level MJCF/mesh, policy-weight, dataset, and media license provenance.

Exit gate: a fresh machine retrieves by exact revision/digest, validates locally,
and reaches the library without executing untrusted code or activating a policy.

### M7 — Optional NVIDIA and challenger lanes (P2)

- [ ] Use NVIDIA only for official-stack A/B runs, unported tasks, or large frozen sweeps.
- [ ] Before any cloud run, freeze commits, dependency/container digests, task/model/BAM hashes, seeds, and transition budget.
- [ ] Run a bounded MuJoCo-MLX-Cpp compatibility spike only after defining BAM-required mutation/state hooks.
- [ ] Eliminate any challenger that cannot reproduce model, BAM, observation, reset, and ONNX-loop conformance before PPO.
- [ ] Require about 2x time-to-held-out-threshold improvement or materially better MuJoCo agreement before replacing Genesis.

Brev cost gate: inspect authenticated inventory before provisioning; recover
checkpoints/evaluator outputs/checksums before teardown; then stop/delete idle
resources and verify disappearance with `brev ls --json` before ending the task.

### M8 — Staged physical validation (blocked until M0–M6)

- [ ] Bind the exact ONNX digest to robot hardware revision, runtime/firmware, operator protocol, and environmental limits.
- [ ] Require explicit user approval at activation time.
- [ ] Progress through quiet stand, small head/body command, very-low-speed walk, stop, and gentle recovery before dynamic tasks.
- [ ] Record synchronized observations, actions, servo telemetry, video, stops, and failure reasons.
- [ ] Issue `hardware_observed` or `physically_accepted` only for the exact artifact and declared protocol; preserve negative results.

Exit gate: the exact ONNX passes or fails the declared physical protocol. No
simulation or reference result grants physical authority.

## Official-only blocked continuation order

1. Ingest an upstream immutable manifest or reproducible checkpoint/export
   chain that closes `official_policy_authority_missing`.
2. Prove report repeatability with that official policy on visible development
   cases only.

That sequence applies to the official-policy reference gate, not to the
versioned first-party development lane. Visible and held-out definitions are
already split; no held-out seed has been realized. Further local work may use
the retained first-party policy only on preregistered visible diagnostics or a
separately frozen longer first-party run.

The BAM fixture, official-adapter consumption, and model-reconciliation runs
are complete and must not be reopened without new contradictory evidence.
