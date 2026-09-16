from pathlib import Path
import json
p=Path('GOAL.md');s=p.read_text();a=s.index('**September 8 V50');b=s.index('**September 8 V49',a)
s=s[:a]+'''**September 8 V50 walking correction complete; not promoted.** The single
864,000-transition run lowers downhill mean absolute yaw error by 16–17% to
.202639/.202257 rad/s, still above .20. Both downhill sessions fall at the
first stop (13.98/13.84 s). All 63 flat cases, both 180-second compositions and
exactly the original five passing surface sessions are retained. One additional
surface window passes, but its whole-session heading still fails. Keep V30.

341,008 paired conformance controls, 56,655 exact original replay labels, every
learning observation/action/reward row, 1,988 switch histories and 9,638 finite
learning scalars verify. V15 standing, V21 teacher and parent normalizers remain
fixed. 140 workspace and three focused tests pass. The run and all four exposed
evaluations are complete; fresh/protected banks stay unrun. Report:
`experiments/walking/RETENTION-RESULTS-v50.md`.

Next revalidate/retarget the three clean V49 braking witnesses on V50 incoming
states before learning a state-conditioned transition. Keep V15 steady standing,
close the remaining .20 yaw margin and require successive stops plus full
retention. V50 is a development starting point only; physical calibration and
carpet transfer remain unmet.

'''+s[b:];p.write_text(s)
p=Path('TRAINING_ACTUALIZATION.md');s=p.read_text();a=s.index('- [ ] Freeze a walking-only correction for downhill yaw');b=s.index('- [ ] Expand the shared walking capability',a)
s=s[:a]+'''- [x] V50 bounded walking-only yaw correction complete. One 864,000-transition
  run reduces downhill absolute yaw by 16–17% to .202639/.202257 rad/s, still
  above the .20 gate. Both first stops fall at 13.98/13.84 s. All 63 flat cases,
  both 180-second compositions and the original five passing surfaces remain.
  All 341,008 paired controls, 56,655 replay labels and recorded learning rows
  verify. Reject promotion; keep V30. The experiment is complete, not walking
  acceptance. See `experiments/walking/RETENTION-RESULTS-v50.md`.
- [ ] Freeze a bounded state-conditioned braking correction from the three
  clean V49 stop witnesses. First revalidate or retarget them on V50 incoming
  states; original-walker search actions are not proven to transfer unchanged.
  Use V50 only as a development starting point, preserve V15 steady standing,
  close the remaining .20 yaw margin and test successive stops, restarts and
  gait phases with full 63-flat, 180-second and passing-surface retention.
  Time-indexed search actions are privileged demonstrations, not a deployed
  general policy. Keep fresh/protected banks closed while prerequisites fail.
'''+s[b:];p.write_text(s)
p=Path('docs/workspace/ACTIVE_EXPERIMENT.md');s=p.read_text();b=s.index('# V49 recovery diagnostic complete')
s='''# V50 correction complete; braking transition is next

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

'''+s[b:];p.write_text(s)
p=Path('docs/workspace/active-experiment.json');d=json.loads(p.read_text());report=json.loads(Path('receipts/walking/20260908-v50-retention-flat/evaluation.json').read_text())
d.update(id='v50-yaw-correction-complete-braking-next',phase='state_conditioned_braking_feasibility_next',
 question='V50 is complete and not promoted. All 63 flat cases, both 180-second compositions and five original surfaces remain, but downhill yaw .202639/.202257 exceeds .20 and first stops fall at 13.98/13.84 s. This packet binds a passing flat reference only. Keep V30; next revalidate the V49 braking witnesses on V50 incoming states before a bounded transition correction.',
 primary='receipts/walking/20260908-v50-retention-flat',primary_policy_sha256=report['policy_sha256'])
d['source_paths']=[{'scripts/evaluate_native_standing_retention_flat_v48.py':'scripts/evaluate_native_retention_flat_v50.py','microduck/native_sequence_env_v48.py':'microduck/native_sequence_env_v50.py','microduck/retained_stander_v48.py':'microduck/retained_walker_v50.py','scripts/train_native_standing_retention_v48.py':'scripts/train_native_retention_v50.py','experiments/walking/native_candidate_v48.py':'experiments/walking/native_candidate_v50.py'}.get(x,x) for x in d['source_paths']]
d['before_training']=['Read experiments/walking/RETENTION-RESULTS-v50.md and the complete downhill/endurance/surface receipts. The single V50 full run and all four exposed evaluations are finished; no extension.','The flat reference passes. Downhill walking still narrowly misses the .20 absolute-yaw gate before braking, and both stops fall. Keep signed averages, prefix scores and full-session acceptance separate.','Revalidate or retarget the three clean V49 stopping witnesses on V50 incoming states before learning a state-conditioned transition. Keep V15 steady standing; original-walker witnesses do not establish unchanged-action recovery for a different walker.','V50 is a development starting point only. Keep V30 retained, close the yaw margin and require successive stops/restarters plus all 63 flat, both 180-second and five passing-surface gates.','Fresh/protected banks, calibrated physics and carpet transfer remain unmet. Freeze the next bounded experiment, check disk space and run guard immediately before compute. No paid compute, activation or hardware authority is implied.']
d['before_training']=[x.replace('stops/restarters','stops/restarts') for x in d['before_training']]
d['boundary']='Measured exposed walking improvement with retained old passes; failed downhill yaw and stopping still block promotion. Not calibrated physical accuracy or carpet transfer.'
p.write_text(json.dumps(d,indent=2)+'\n')
