import collections,json,math,hashlib,shutil
from pathlib import Path
import numpy as np
rp=Path('receipts/walking/20260906-v23-endurance');out=Path('receipts/walking/20260906-v23-verification')
r=json.loads((rp/'probe.json').read_text());whole=json.loads((out/'whole-session-heading.json').read_text())
rows=collections.defaultdict(list);counts=collections.Counter()
for line in (rp/'trajectory.jsonl').open():
 row=json.loads(line);rows[row['session_id']].append(row);counts[row['case_id']]+=1
phase=[]
for session,values in rows.items():
 ts=np.array([v['session_time_s'] for v in values]);q=np.array([v['qpos'][3:7] for v in values]);w,x,y,z=q.T
 theta=np.unwrap(np.arctan2(2*(x*y+w*z),1-2*(y*y+z*z)))
 assert len(values)==9000
 for case in [c for c in r['case_reports'] if c['session_id']==session]:
  actions=np.load(rp/(case['case_id']+'-actions-float32.npy'));assert actions.dtype==np.float32 and actions.shape==(counts[case['case_id']],14)
  relevant=[v for v in values if v['case_id']==case['case_id']]
  np.testing.assert_array_equal(actions,np.array([v['action_rad'] for v in relevant],np.float32))
 if session.startswith('continuous'):
  for i in range(10):
   offset=i*18
   def angle(t):return float(theta[np.argmin(abs(ts-t))])
   command=values[i*900+100]['command'][2]
   p={'session':session,'window':i+1,'requested_yaw_rad_s':command,
      'startup_1_to_2_actual_deg':math.degrees(angle(offset+2)-angle(offset+1)),
      'steady_2_to_13_actual_deg':math.degrees(angle(offset+13)-angle(offset+2)),
      'stop_13_to_18_actual_deg':math.degrees(angle(offset+18)-angle(offset+13)),
      'whole_window_actual_deg':math.degrees(angle(offset+18)-angle(max(.02,offset))),
      'whole_window_requested_deg':math.degrees(command*12)}
   p['whole_window_signed_error_deg']=p['whole_window_actual_deg']-p['whole_window_requested_deg'];phase.append(p)
result={'schema':'microduck.v23-endurance-review/v1','input_manifest_sha256':hashlib.sha256((rp/'SHA256SUMS').read_bytes()).hexdigest(),
 'original_passed_sessions':r['passed_sessions'],'original_total_sessions':r['total_sessions'],'original_passed_windows':r['passed_windows'],'original_total_windows':r['total_windows'],
 'complete_audit_passed_sessions':sum(s['passed'] and whole['session_reports'][s['session_id']]['passed'] for s in r['session_reports']),
 'simulated_seconds':sum(s['simulated_duration_s'] for s in r['session_reports']),'control_rows':sum(counts.values()),'physics_samples':sum(s['full_session_internal_load']['observed_samples'] for s in r['session_reports']),
 'all_action_bytes_match_float32_trajectory_actions':True,'all_session_rows_continuous':True,
 'max_window_yaw_MAE_rad_s':max(c['metrics']['mean_abs_yaw_error_rad_s'] for c in r['case_reports']),
 'minimum_actual_joint_margin_rad':min(c['metrics']['minimum_actual_joint_margin_rad'] for c in r['case_reports']),
 'max_self_penetration_m':max(c['self_contact']['maximum_self_penetration_m'] for c in r['case_reports']),
 'all_full_session_load_gates_pass':all(s['full_session_internal_load']['passed'] for s in r['session_reports']),
 'phase_diagnostics':phase,'boundary':'Original window results remain 24/24 and original session gates 6/6. The additive whole-session heading audit rejects both compositions. Thus complete-audit endurance is 4/6, not 6/6. Phase segmentation is diagnostic, not causal evidence or new training.'}
(out/'endurance-review.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ('complete_audit_passed_sessions','simulated_seconds','control_rows','physics_samples')})
for p in phase:print(p['session'],p['window'],round(p['whole_window_signed_error_deg'],2),'stop_delta',round(p['stop_13_to_18_actual_deg'],2))
shutil.copy2('/tmp/review_v23_endurance.py',out/'analyze_endurance.py')
