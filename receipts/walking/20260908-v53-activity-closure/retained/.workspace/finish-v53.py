from pathlib import Path
import json,shutil
ROOT=Path.cwd();out=ROOT/'outputs/walking-braking-v53';r=json.loads((out/'verification.json').read_text());fit=json.loads((out/'fit-conflict.json').read_text());run=r['training']
for name in ['v53-initial-zero-errors.json','v53-original-zero-errors.json']:shutil.copy2(ROOT/'.workspace'/name,out/name)
summary='''**September 8 V53 retention experiment complete; candidate rejected.**
All 63 flat cases and exactly the five original passing surface sessions are
restored. Both 180-second compositions finish without falling; start 1 still
fails whole-session heading (21.4145 degrees versus 20), so endurance is 1/2.
Downhill start 1 falls at 14.24 s; start 2 finishes 36 s but fails yaw, final
head posture and endpoint heading. V52's downhill stopping gains are not fully
retained. Original V21/V15 with V30 remains retained; no policy is activated.

Nine learner-visited states recover under the original actors with all gates
passing. The single 8,000-update supervised fit used 500 successful downhill
braking rows and 12,555 zero-label rows, including 930 verified new recovery
examples. Worst original zero-label error drops from .209567 to .028361 rad,
but first-action downhill demonstration errors are .077870–.206272 rad.
All 94,660 evaluated actions, 36,952 unchanged prefix controls, 13,055 replay
labels, 8,000 finite losses and 160 hard-example pools verify. 140 workspace
and two focused tests pass. Report: `experiments/walking/BRAKING-RESULTS-v53.md`.

Next freeze an offline fit-feasibility experiment with separate maximum-error
limits for successful stops and downhill recovery, explicitly including all
stop-onset states. Do not let one group's mean loss hide the other's largest
action errors. Require both fitting gates before another full rollout bank;
then recheck all existing walking/contact/heading gates. Input/architecture
insufficiency is not established. Keep the remaining .20 yaw margin and all
physical calibration, terrain-generalization and carpet-transfer gates intact.

'''
p=ROOT/'GOAL.md';s=p.read_text();start=s.index('**September 8 V53 retention');end=s.index('**September 8 V51/V52',start);p.write_text(s[:start]+summary+s[end:])
p=ROOT/'TRAINING_ACTUALIZATION.md';s=p.read_text();start=s.index('- [ ] Freeze a retention-constrained braking correction.');end=s.index('- [ ] Expand the shared walking capability',start);s=s[:start]+'''- [x] V53 bounded retention experiment complete; rejected. Nine original-actor
  continuations supply 930 verified recovery labels. One 8,000-update fit
  restores 63/63 flat and the original five surface passes. Both 180-second
  sessions survive, but one fails heading (1/2 accepted). Downhill start 1 falls
  at 14.24 s; start 2 fails yaw/posture/heading. Keep V30; do not extend V53.
  See `experiments/walking/BRAKING-RESULTS-v53.md`.
- [ ] Freeze one offline fit-feasibility experiment with separate maximum-error
  gates for successful-stop retention and downhill recovery, including each
  stop onset. V53 reduces zero-label errors but leaves .077870–.206272 rad
  errors on the four downhill onset labels. Require both fitting gates before
  full rollout evaluation; do not call a dataset fit behavior success. Only
  consider a bounded architecture/input diagnosis if the joint fit is infeasible;
  missing observability is not established. Preserve V15 standing, all 63 flat,
  both 180-second and five original surface gates, successive downhill stops
  and the .20 yaw limit. Fresh/protected banks remain closed.
'''+s[end:];p.write_text(s)
p=ROOT/'docs/workspace/ACTIVE_EXPERIMENT.md';p.write_text('''# V53 retention complete; joint fitting feasibility is next

'''+summary+'''The active packet binds V53's passing nominal forward-0.08 flat reference.
It is a retention witness, not the remaining failure. Inspect
`receipts/walking/20260908-v53-braking-endurance` and the recorded downhill
video in `outputs/walking-braking-v53/downhill-start-1.mp4` for the actual
14.24-second fall. Full-session heading also fails after all 180 seconds in
composition start 1; passing every short window does not waive that failure.
The separately retained braking ONNX digest is
`d0c2e4accc07364cd588a93713ef7f65acc92f7bf39283fb2889b058e45d98fa`.
The V50 base-policy digest alone does not identify this composite controller.
No further experiment is frozen or running. The records below are historical.

'''+p.read_text())
p=ROOT/'docs/workspace/active-experiment.json';a=json.loads(p.read_text());a.update(id='v53-retention-complete-joint-fit-next',phase='joint_braking_fit_feasibility_next',primary='receipts/walking/20260908-v53-braking-flat',question='V53 is complete and rejected. All 63 flat and five original surface passes return; both 180-second sessions survive, but one fails whole-session heading. Downhill start 1 falls at 14.24 s; start 2 fails yaw/posture/heading. This packet binds a passing flat retention reference only; read the V53 endurance receipt for failures. Next establish joint fitting feasibility with separate retention and recovery error gates. Keep V30.',boundary='Exposed retention improvement with remaining downhill and full-session heading failures. Not accepted walking, calibrated physical accuracy or carpet transfer.')
a['source_paths']=[x.replace('_v52','_v53').replace('-v52','-v53').replace('BRAKING-DISTILLATION-v53.md','BRAKING-RETENTION-v53.md') for x in a['source_paths']]
a['before_training']=['Read experiments/walking/BRAKING-RESULTS-v53.md. The nine-state collection, single 8,000-update learner and all four exposed evaluation banks are complete. No extension or checkpoint reselection.', 'The selected flat reference passes. Actual failures are in 20260908-v53-braking-endurance: downhill start 1 falls at 14.24 s; start 2 fails yaw, final posture and endpoint heading. Composition start 1 finishes 180 s but maximum heading error 21.4145 degrees exceeds 20.', 'The primary manifest binds braking/policy.onnx SHA-256 d0c2e4accc07364cd588a93713ef7f65acc92f7bf39283fb2889b058e45d98fa in addition to the frozen V50/V15 base actors. Do not identify the composite by the base walker digest alone.', 'Next freeze one offline joint fit-feasibility experiment: independent maximum-error limits for successful-stop and downhill-recovery labels, with every stop onset explicitly checked. Onset errors .077870-.206272 rad remain despite better zero-label fitting. Require both fitting gates before full rollout evaluation, then preserve all original behavioral gates. Do not infer missing observability or physical accuracy.', 'V30 remains retained. Fresh/protected banks stay closed; measured calibration, terrain generalization and carpet transfer remain unmet. Check storage and guard immediately before any newly authorized compute. No paid compute, activation or hardware authority is implied.'];p.write_text(json.dumps(a,indent=2)+'\n')
lines=['# V53 retention correction: completed, not promoted','',
'V53 restores all 63 flat cases and exactly the original five passing surface sessions. Both 180-second compositions finish without falling, but one fails whole-session heading. Downhill recovery regresses from V52. The bounded experiment is complete; the candidate is rejected. Keep the original V21/V15 actors with V30 retained.','',
'| Complete all-gate evaluation | V50 | V52 | V53 |','|---|---:|---:|---:|','| Original flat timing bank | 21/21 | 13/21 | **21/21** |','| Repeated flat windows | 42/42 | 25/42 | **42/42** |','| Downhill whole sessions | 0/2 | 0/2 | **0/2** |','| 180-second compositions | 2/2 | 0/2 | **1/2** |','| Whole surface sessions | 5/14 | 3/14 | **5/14** |','| Surface windows | 13/28 | 8/28 | **13/28** |','',
'All 20 short windows within the two 180-second compositions pass. Start 1 nevertheless fails the separate full-session heading gate: maximum error **21.414506 degrees**, above **20**; its endpoint error is 5.760180 degrees. Start 2 passes, including maximum/endpoint heading errors 18.100903/10.175197 degrees. Neither composition resets or falls. Do not reduce the denominator to short-window success.','',
'Downhill start 1 falls at **14.24 s**, with actual joint-margin, body-interference and sustained/continuous internal-load failures. The second window is unrun and remains failed. Start 2 survives both stops through 36 s, but its windows have mean absolute yaw errors .202257/.215905 rad/s versus .20, and final mean absolute face pitch 30.108382/31.392713 degrees versus 30. Its whole-session endpoint heading is 16.879942 degrees versus 15. V52 survived both starts with stop checks passing; that gain is not fully retained.','',
'The five surface passes are exactly `rigid-control-start-1`, `rigid-control-start-2`, `soft-low-traction-start-1`, `soft-low-traction-start-2`, and `unseen-low-medium-start-1`. Historical `unseen-*` case names are now exposed development cases. No unfamiliar specimen or protected bank was evaluated.','',
'## Verified data collection and one training run','',
'The frozen collection selected nominal forward-08, nominal forward-12 and zero-lag arc-left, each at controls 655, 670 and 690. All **2,223 original V52 controls** reproduce original float32 actions/observations, qpos/qvel and braking age/active state. Full physics/BAM, sensor/motor histories, command-ramp, heading and braking-event states are retained.','',
'For all nine states, the original V50/V15 actors recover and pass every complete 18-second flat gate. Each original-actor and unchanged V52 branch repeats exactly, including physics-rate load telemetry: **5,358 repeated continuation controls** total. No reset occurs inside a continuation. The unchanged branches retain their original failures; the collector does not assign zero labels to arbitrary unvalidated states.','',
'The dataset contains **13,055 rows**: 11,625 prior successful-stop zero labels, **930 new verified recovery rows**, and **500 actual V52 downhill braking examples** from the four previously successful stop events. Those four source windows retain their yaw failures. The mixed V51 time-knot examples are replaced rather than relabeled. Every replay observation and target reconstructs byte-for-byte from its bound source.','',
'One seed-26090853 supervised run completed all **8,000 updates**, using 3,072,000 sample presentations. It starts from V52 FINAL and keeps its 61-64-64-14 architecture, normalization tensors, 125-control event router, V50/V15 base weights, V30 controller and complete-contact-v11 physics fixed. The changed loss penalizes average and worst-joint zero-label errors, with 128 positive, 128 random zero and 128 hard zero examples per update; hard pools refresh every 50 updates. All 160 pools and 8,000 finite losses are retained. There are zero new PPO/RL transitions. FINAL only; no extension, clipping, terrain switch, policy activation, paid compute or hardware operation.','',
'On the identical original 11,625 zero-label inputs, RMSE decreases from .008877 to **.002735 rad**, the worst action error from .209567 to **.028361 rad**, and the 95th percentile of per-row maximum errors from .040455 to **.011027 rad**. The focused nominal first braking correction shrinks from .019819 to **.009238 rad**; its formerly failed rollout now passes all gates through 18 s. Fitting improves, but it is not exact zero preservation.','',
'## Why the next task is joint fitting feasibility','',
'V53 still has **.015697-rad RMSE** and **.206272-rad maximum error** against the downhill demonstrations. More revealingly, the four first braking actions have maximum errors **.141180, .077870, .206272 and .133775 rad** on their exact training inputs. A small average fitting error therefore hides large corrections at the transition onset.','',
'The positive and weighted zero-label losses have locally opposing gradient directions (cosine -.242560 at FINAL; norms 6.47152 and 51.61537). This is a local optimization diagnostic, not proof that the 61D input is ambiguous, that the network lacks capacity, or that any particular optimizer will solve the robot. Physics was unchanged, and these same-input errors precede any closed-loop distribution shift.','',
'**Next best step:** freeze an offline joint-fit feasibility experiment with independent maximum-error gates for successful-stop retention and downhill recovery, explicitly covering every stop onset. Do not trade one group away through an aggregate mean loss. Require both fitting gates before another full rollout battery. If a bounded fit cannot meet them, inspect conflicting labels/representation and test one preregistered capacity change; do not assume missing observability. A passing fit still requires all 63 flat, both full endurance, five surface retention, successive downhill-stop, posture, contact, load and yaw gates. Keep the .20 yaw and 20-degree whole-session heading limits unchanged.','',
'## Verification and retained evidence','',
'All **94,660 evaluated actions** exactly match the frozen base ONNX plus the new ONNX correction, with zero action discrepancy. All **36,952 available first-window prefix controls** through braking onset exactly match V50 action/observation bytes and qpos/qvel. **378,640 physics-rate load samples** are present. Event ages and activation windows verify on every recorded row; failures and missing windows remain failures. All replay labels, model/run hashes, normalizers, source freezes and receipt manifests verify.','',
'Maximum recorded Torch/ONNX export error across the training set and 1,000 random inputs is **2.384186e-6 rad**, below 1e-4. All **140 workspace tests** and **two focused V53 tests** pass. Tests cover process recognition, receipt handling, the changed loss and event lifetime; they do not establish physical behavior. No thresholds or historical scores changed. Fresh/protected banks remain closed; measurement-based calibration, general terrain acceptance and carpet transfer remain unmet.','',
'Artifacts:','',
'- Frozen protocol: `experiments/walking/BRAKING-RETENTION-v53.md`.',
'- Collection: `receipts/walking/20260908-v53-retention-collection/`.',
'- Dataset: `experiments/walking/braking-replay-v53/`.',
'- Run: `logs/braking-retention-20260908-v53/`.',
'- Evaluations: `receipts/walking/20260908-v53-braking-{flat,repeated,endurance,surfaces}/`.',
'- Audit, fitting diagnostic, figure and recorded-pose video: `outputs/walking-braking-v53/`.',
'- Activity closure and source-bound references: `receipts/walking/20260908-v53-activity-closure/`.',
'',f"V53 braking ONNX: `{run['policy_sha256']}`.",f"V53 checkpoint: `{run['checkpoint_sha256']}`.",f"Training freeze: `{run['freeze_sha256']}`.",'The V50 base walker ONNX remains `1f8e87d7370a1aeb7b57f272c96abb6df49e3039b8d1332bfce24c1a81de5b4f`; the additional V53 braking digest is required to identify the composite controller. The active packet uses a passing V53 flat reference only. The video shows the actual rejected downhill start-1 receipt; it re-renders recorded poses without integrating physics or repairing motion.','',
'## Every failed window and session','',
'Window times are relative to each 18-second scoring interval. Complete-session failures are listed independently.','']
for bank,b in r['banks'].items():
 lines+=['### '+bank,'','| Case | First fall (s) | Failures |','|---|---:|---|']
 failed=[(cid,c) for cid,c in b['cases'].items() if not c['passed']]
 if not failed:lines+=['| All cases pass | — | None |']
 for cid,c in failed:lines.append(f"| `{cid}` | {c['first_fall_s'] if c['first_fall_s'] is not None else '—'} | {'; '.join(c['failures'])} |")
 if b['sessions']:
  lines+=['','| Session | Duration (s) | Failures |','|---|---:|---|']
  for s in b['sessions']:
   if not s['passed']:lines.append(f"| `{s['session_id']}` | {s['simulated_duration_s']:.2f} | {'; '.join(s['failures'])} |")
 lines+=['']
(ROOT/'experiments/walking/BRAKING-RESULTS-v53.md').write_text('\n'.join(lines)+'\n');print('Report, current status and queue updated')
