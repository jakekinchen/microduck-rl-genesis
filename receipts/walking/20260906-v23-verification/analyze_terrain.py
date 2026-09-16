import json,hashlib,collections,shutil
from pathlib import Path
import numpy as np
def verify_input_manifest(folder):
    entries={}
    for line in (folder/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        file=(folder/name).resolve()
        if not file.is_relative_to(folder.resolve()) or name in entries: raise ValueError('invalid manifest path')
        actual=hashlib.sha256(file.read_bytes()).hexdigest()
        if actual!=digest: raise ValueError('manifest hash drift: '+name)
        entries[name]=digest
    files={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
    if set(entries)!=files: raise ValueError('manifest coverage mismatch')
    if not {'probe.json','trajectory.jsonl','policy.onnx','evaluator-freeze.json','suite.json'}<=set(entries): raise ValueError('required custom probe evidence missing')
root=Path('.')
rp=root/'receipts/walking/20260906-v23-terrain'
verify_input_manifest(rp)
r=json.loads((rp/'probe.json').read_text())
selected=['downhill-3deg-start-1--window-1','downhill-3deg-start-2--window-1','seams-3mm-start-1--window-1']
traces={name:[] for name in selected}
counts=collections.Counter(); modes=collections.Counter(); contact_friction=collections.Counter()
observed_raised=collections.Counter(); max_tilt=0
for line in (rp/'trajectory.jsonl').open():
 row=json.loads(line);name=row['case_id'];counts[name]+=1;modes[row['actor_mode']]+=1
 max_tilt=max(max_tilt,row['tilt_deg'])
 for friction in row['observed_contact_sliding_friction']:contact_friction[str(friction)]+=1
 observed_raised[row['session_id']]+=sum(c['ground'].startswith('terrain_') and c['normal_n']>1 for c in row['terrain_contacts'])
 if name in traces:traces[name].append(row)
for c in r['case_reports']:
 acts=np.load(rp/(c['case_id']+'-actions-float32.npy'))
 assert acts.dtype==np.float32 and acts.shape==(counts[c['case_id']],14)
 assert len(acts)*.02==c['observed_duration_s']
for s in r['session_reports']:
 assert observed_raised[s['session_id']]==s['raised_surface_loaded_contact_samples']
keys=['time_s','actor_mode','command','policy_command','robot_xyz_m','ground_height_at_base_m','base_clearance_m','tilt_deg','foot_normal_n','loaded_contact_slip_m_s','fell']
diagnostics={}
for name,rows in traces.items():
 switches=[{k:row[k] for k in ('time_s','actor_mode')} for i,row in enumerate(rows) if i==0 or row['actor_mode']!=rows[i-1]['actor_mode']]
 snapshots=[{k:min(rows,key=lambda r:abs(r['time_s']-t))[k] for k in keys} for t in [12.98,13.02,13.16,13.30,13.54,13.82]]
 moving=[v for v in rows if 2<=v['time_s']<=13]
 diagnostics[name]={'actor_switches':switches,'transition_snapshots':snapshots,'moving_forward_mae_m_s':float(np.mean([abs(v['body_velocity_m_s'][0]-.12) for v in moving])),'moving_yaw_mae_rad_s':float(np.mean([abs(v['yaw_rate_rad_s']) for v in moving])),'boundary':'Observed association. No controller intervention or counterfactual replay; not causal attribution.'}
result={'schema':'microduck.v23-terrain-review/v1','input_manifest_sha256':hashlib.sha256((rp/'SHA256SUMS').read_bytes()).hexdigest(),'complete':r['complete'],'all_session_buckets':r['buckets'],'passed_sessions':r['passed_sessions'],'total_sessions':r['total_sessions'],'passed_unseen_terrain_sessions':sum(s['passed'] for s in r['session_reports'] if s['bucket']!='flat-control'),'total_unseen_terrain_sessions':12,'passed_windows':r['passed_windows'],'total_windows':r['total_windows'],'fall_windows':[c['case_id'] for c in r['case_reports'] if c.get('gait',{}).get('fell')],'unrun_windows':[c['case_id'] for c in r['case_reports'] if c['observed_duration_s']==0],'control_rows':sum(counts.values()),'actor_samples':dict(modes),'contact_friction_histogram':dict(contact_friction),'all_action_files_match_row_counts':True,'all_raised_surface_counts_match':True,'diagnostics':diagnostics,'boundary':'Small preregistered deterministic development matrix. All outcomes exposed; no population reliability, unseen-family generalization admission or physical calibration claim.'}
out=root/'receipts/walking/20260906-v23-verification'
(out/'terrain-review.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ('control_rows','passed_unseen_terrain_sessions','total_unseen_terrain_sessions','fall_windows','unrun_windows')})
for name in ('downhill-stop.png','seam-tracking.png'):shutil.copy2(root/'.workspace/v23-visual-inspection'/name,out/name)
