import json,shutil
from pathlib import Path
ROOT=Path.cwd();out=ROOT/'outputs/walking-braking-v52';r=json.loads((out/'verification.json').read_text());banks=r['banks']
shutil.copy2('.workspace/audit-braking-v52.py',out/'audit-source.py')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
labels=['Flat\n63 cases','Endurance\n2 sessions','Surfaces\n14 sessions'];old=[1,1,5/14];new=[38/63,0,3/14]
import numpy as np
z=np.arange(3);axes[0].bar(z-.18,old,.36,label='V50 development baseline',color='#567D91');axes[0].bar(z+.18,new,.36,label='V52 braking correction',color='#CB6B46');axes[0].set(xticks=z,xticklabels=labels,ylim=(0,1.15),ylabel='Fraction passing every gate',title='Retention regressed');axes[0].legend(fontsize=8)
for i,(a,b,den) in enumerate(zip(old,new,[63,2,14])):
 axes[0].text(i-.18,a+.02,f'{round(a*den)}/{den}',ha='center',fontsize=9);axes[0].text(i+.18,b+.02,f'{round(b*den)}/{den}',ha='center',fontsize=9)
t=r['first_flat_failure_braking_trace'];axes[1].plot([x['time_s'] for x in t],[x['max_abs_residual_rad'] for x in t],color='#CB6B46',label='Largest action correction');axes[1].set(xlabel='Recorded time (seconds)',ylabel='Maximum |residual| (radians)',title='Nominal forward 0.08 m/s: first stop');axes[1].axvline(14.42,color='#555',ls='--',lw=1);axes[1].text(14.4,.05,'Fall at 14.42 s',rotation=90,ha='right',va='bottom',fontsize=9)
fig.suptitle('V52: downhill stops survive, overall candidate rejected',fontsize=14);fig.savefig(out/'comparison.png',dpi=170);plt.close(fig)
lines=['# V51 recovery revalidation and V52 braking correction: complete, rejected','',
'V52 survives both successive downhill stops in each 36-second session. It still fails downhill absolute yaw and regresses previously successful flat, endurance and surface cases. The bounded activity is complete; the behavior is not accepted. Keep the original V21/V15 actors with V30 controller retained. V50 and V52 remain development candidates only.','',
'## Measured acceptance','',
'| Exposed evaluation | V50 | V52 | Decision |','|---|---:|---:|---|',
'| Flat timing bank | 21/21 | 13/21 | Eight regressions |','| Repeated flat windows | 42/42 | 25/42 | Seventeen regressions, including unrun windows |','| Downhill whole sessions | 0/2 | 0/2 | Stops now survive; yaw still fails |','| Continuous 180-second compositions | 2/2 | 0/2 | Falls at 15.10 and 158.58 seconds |','| Whole surface sessions | 5/14 | 3/14 | Two original passes lost |','| Surface windows | 13/28 | 8/28 | Five fewer complete passes |','',
'Both downhill sessions finish 36 seconds with no resets. All four downhill windows fail only the absolute-yaw gate and its tracking-bucket counterpart: first/second windows are .202639/.205836 rad/s for start 1 and .202257/.207138 for start 2, against .20. Stopping, final head posture, gait, contact geometry, internal loading and the other required checks pass in those four windows; whole-session heading also passes. This is measured exposed stopping improvement, not full walking acceptance.','',
'Surface passes retained: `rigid-control-start-2`, `soft-low-traction-start-2`, `unseen-low-medium-start-1`. Lost passes: `rigid-control-start-1` (fall at 15.76 s) and `soft-low-traction-start-1` (second-window fall, session time 32.38 s). Historical `unseen-*` names refer to already exposed development cases, not a fresh validation bank. Four surface failures occur before any braking intervention and exactly match V50 prefixes.','',
'## V51 prerequisites and V52 training','',
'V51 revalidated three V49 first-stop witnesses on V50 incoming physical states. Two witnesses were reusable with original V15 steady standing; one state required the preregistered 384-candidate retargeting search. All three first-stop demonstrations became eligible. Eligibility excludes only the already-failed pre-stop yaw checks; it is not whole-session acceptance. The retargeted branch still fell at the second stop (31.84 s).','',
'V51 verified 1,391 original source controls, 150 reset controls, 9,698 exactly repeated comparison controls and all 83,053 search controls. All twelve comparison branches and selected search branches preserve full physical state and physics-rate internal-load evidence. No original evaluator or historical score was edited.','',
'V52 performed one supervised demonstration-distillation run, not PPO: 2,000 Adam updates, 512,000 sample draws, seed 26090852, FINAL only, zero new RL transitions. Training used 375 demonstrated recovery rows plus 11,625 zero-residual retention rows from previously passing stops. The 61D normalized residual actor adds 14D raw servo deltas for 125 controls (2.5 seconds) after requested movement becomes zero; movement cancels the correction. V50 walking and V15 steady-standing weights remain fixed. The late 13.14-second demonstration differs from the evaluated 13-second trigger; the frozen protocol declares this distribution difference. No action clipping, physics change or policy activation occurred.','',
'Final training RMSE: .006832 rad on demonstrations and .008877 rad on retention rows. Maximum ONNX/Torch export error across all training inputs and 1,000 random inputs: 1.430512e-6 rad. Low demonstration error did not preserve closed-loop behavior.','',
'## First regression and next best step','',
'The focused flat case is `nominal-20-20ms--forward-08`. Its first 650 controls (through 13.00 s) match V50 action and observation float32 bytes and qpos/qvel float64 bytes. At 13.02 s, the braking observation exactly matches a zero-residual training example, yet the model adds a maximum .019819-rad correction. This is already a retention-fitting error, before any unseen-state extrapolation. The correction reaches .431395 rad at 13.80 s and 1.102263 rad at the 14.42-second fall. The nearest normalized replay distance grows from zero to 67.146. These are measured facts; they support compounding closed-loop error, not a proven unique causal mechanism.','',
'Next freeze a retention-constrained braking experiment: first inspect and reduce the worst zero-label errors on the exact successful-stop states, then collect verified corrective targets on states visited by the learned braker as it begins to diverge. A zero residual is a justified label on retained successful trajectories, not automatically on newly visited off-trajectory states; revalidate recovery there. Keep successful downhill demonstrations, original V15 steady standing, the unchanged .20 yaw gate, and all 63 flat, both endurance and five original surface retention gates. Preregister the changed loss/data rule and one bounded final-only run. Do not extend V52, select an intermediate checkpoint, add terrain-specific switches, or open fresh/protected banks. Close the remaining walking yaw margin separately after stopping retention holds.','',
'This next-data strategy is motivated by the primary DAgger paper, which addresses imitation-learning distribution changes caused by the learner’s own actions: [Ross, Gordon and Bagnell, 2011](https://proceedings.mlr.press/v15/ross11a.html). Its theory motivates the experiment; it does not certify this robot or guarantee recovery from every visited state.','',
'## Verification and provenance','',
'Offline verification reconstructs all 12,000 replay rows and positive residual labels byte-for-byte, checks all 2,000 finite losses and normalized model tensors, verifies frozen source and retained manifests, and rechecks every evaluated action against the retained V50/V15 ONNX plus the V52 correction. All 73,242 evaluated controls match exactly (zero action discrepancy); 292,968 physics-rate load samples are present. All 36,952 available first-window prefix controls match V50 actions, observations, qpos and qvel exactly. Controller activation age and the 125-control bound verify on every row. Missing windows remain failures.','',
'Workspace tooling: 140 tests pass. Four focused V51/V52 tests pass. These validate tooling and event routing, not physical behavior. All original motor, posture, gait, geometric interference, internal-load, endurance and heading gates remain unchanged. No fresh/protected bank, measurement-based physical calibration, carpet transfer or general terrain acceptance is claimed.','',
'Artifacts:',
'- Frozen plans: `experiments/walking/BRAKING-FEASIBILITY-v51.md`, `experiments/walking/BRAKING-DISTILLATION-v52.md`.',
'- V51 receipts: `receipts/walking/20260908-v51-recovery-{capture,comparisons,search}`.',
'- V52 run: `logs/braking-distill-20260908-v52`.',
'- V52 evaluations: `receipts/walking/20260908-v52-braking-{flat,repeated,endurance,surfaces}`.',
'- Full case failures, manifests, audit source and figure: `outputs/walking-braking-v52/`.',
'- Recorded-pose downhill video: `outputs/walking-braking-v52/downhill-start-1.mp4`. The full-session FAIL label includes the remaining yaw failure; this visualization adds no new simulation or repaired motion.',
'- Final closure: `receipts/walking/20260908-v52-activity-closure/`.',
'',f"Braking ONNX SHA-256: `{r['training']['policy_sha256']}`.",f"Braking checkpoint SHA-256: `{r['training']['checkpoint_sha256']}`.",'V50 base walking ONNX SHA-256: `1f8e87d7370a1aeb7b57f272c96abb6df49e3039b8d1332bfce24c1a81de5b4f`. The braking digest is additional to this base-policy identity; a V50 base digest alone does not identify the composite V52 controller.','',
'## Every failed evaluated case','',
'Case time below is relative to its 18-second scoring window. Full compositions retain uninterrupted session time. Unrun windows after a fall are counted as failures.','']
for bank,b in banks.items():
 lines+=['### '+bank,'','| Case | First fall (s) | Failures |','|---|---:|---|']
 for cid,c in b['cases'].items():
  if not c['passed']:lines.append(f"| `{cid}` | {c['first_fall_s'] if c['first_fall_s'] is not None else '—'} | {'; '.join(c['failures'])} |")
 lines+=['']
(ROOT/'experiments/walking/BRAKING-RESULTS-v52.md').write_text('\n'.join(lines)+'\n')
summary='''**September 8 V51/V52 braking activity complete; V52 rejected.**
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

'''
p=ROOT/'GOAL.md';s=p.read_text();start=s.index('**September 8 V51 recovery');end=s.index('**September 8 V50 walking',start);s=s[:start]+summary+s[end:];old='''Next revalidate/retarget the three clean V49 braking witnesses on V50 incoming
states before learning a state-conditioned transition. Keep V15 steady standing,
close the remaining .20 yaw margin and require successive stops plus full
retention. V50 is a development starting point only; physical calibration and
carpet transfer remain unmet.''';s=s.replace(old,'The V50 follow-up revalidation and braking correction are completed in V51/V52\nabove. V50 remains a development starting point; its historical score is intact.');p.write_text(s)
p=ROOT/'TRAINING_ACTUALIZATION.md';s=p.read_text();start=s.index('- [ ] Freeze a bounded state-conditioned braking correction');end=s.index('- [ ] Expand the shared walking capability',start);s=s[:start]+'''- [x] V51/V52 bounded braking activity complete. Three first-stop demonstrations
  admitted after 384 retargeting candidates; one 2,000-update supervised run
  survives both successive stops in both downhill sessions. All still fail yaw.
  Flat retention is 38/63, endurance 0/2 and surface sessions 3/14. Reject V52;
  keep V30. Every action, source, label and load trace verifies. See
  `experiments/walking/BRAKING-RESULTS-v52.md`.
- [ ] Freeze a retention-constrained braking correction. First reduce the worst
  zero-residual fitting errors on existing successful-stop states, then collect
  verified corrective targets on learner-visited diverging states. Do not label
  arbitrary new states zero without recovery evidence. Preserve downhill stop
  gains, V15 steady standing, all 63 flat cases, both 180-second compositions,
  all five original surface passes and every original gate. Use one newly
  preregistered bounded final-only run; do not extend V52. Keep the remaining
  .20 yaw correction separate and fresh/protected banks closed.
'''+s[end:];p.write_text(s)
p=ROOT/'docs/workspace/ACTIVE_EXPERIMENT.md';p.write_text('''# V52 braking complete and rejected; retention correction is next

'''+summary+'''The active packet now binds the actual failed V52 nominal forward-0.08 flat
case, compared with the identical V50 passing reference. First divergence is
the braking action at 13.02 seconds; first fall is 14.42 seconds. The V52
composite includes its separately retained braking ONNX as well as the V50
base walker and original V15 stander. Read the receipt's `braking/` manifest
entries and `braking_policy_sha256`; the base walking digest alone is not the
full controller identity. `duck prepare` verifies the retained source and
trace bindings and starts no training. No new run has been frozen or launched.

The following records describe completed earlier activity.

'''+p.read_text())
p=ROOT/'docs/workspace/active-experiment.json';a=json.loads(p.read_text());a.update(id='v52-braking-rejected-retention-next',phase='braking_retention_diagnosis',primary='receipts/walking/20260908-v52-braking-flat',comparison='receipts/walking/20260908-v50-retention-flat',comparison_policy_sha256=a['primary_policy_sha256'],question='V52 is complete and rejected. It survives both successive downhill stops but loses 25/63 flat passes, both endurance runs and two of five surface passes. This packet binds the failed nominal forward-0.08 stop against V50: identical through 13.00 s, residual starts at 13.02 s, fall at 14.42 s. The additional braking ONNX is 2dea5e82c66690ea06d2cf3b56a76968f360de567d3cb6c1ed0491ace389421b. Keep V30; next correct braking retention.',boundary='Measured exposed downhill stopping improvement with flat/endurance/surface regressions. Rejected; not full walking, calibrated physics or carpet transfer.')
a['source_paths']=['scripts/evaluate_braking_flat_v52.py','microduck/braking_v52.py','scripts/train_braking_v52.py','scripts/build_braking_replay_v52.py','experiments/walking/BRAKING-DISTILLATION-v52.md','experiments/walking/braking-replay-v52/replay.npz','experiments/walking/braking-replay-v52/provenance.json']+a['source_paths']
a['before_training']=['Read experiments/walking/BRAKING-RESULTS-v52.md and all four failed evaluation banks. The V51 search, single V52 learner and all evaluations are complete; no extension or checkpoint reselection.', 'Inspect the V52 nominal forward-0.08 first stop: its 13.02-second observation exactly matches a zero-residual training sample, but the model adds .019819 rad; it later falls at 14.42 seconds. Prefix identity and exact runtime ONNX actions verify.', 'The primary manifest binds braking/policy.onnx SHA-256 2dea5e82c66690ea06d2cf3b56a76968f360de567d3cb6c1ed0491ace389421b in addition to the V50 base walker and V15 stander. This is the V52 composite, not V50 alone.', 'Next freeze one retention-constrained braking experiment: tighter successful-stop fitting and validated corrective labels on learner-visited states, with unchanged gates. Preserve V15 standing and downhill stop gains; require all 63 flat, both 180-second and five original surface passes. Keep V30 retained.', 'Downhill yaw .202257-.207138 still exceeds .20. Fresh/protected banks, measured calibration and carpet transfer remain unmet. Check free storage and run guard immediately before newly authorized compute. No paid compute, activation or hardware authority is implied.'];p.write_text(json.dumps(a,indent=2)+'\n')
print('Wrote report, figure and current queue/packet')
