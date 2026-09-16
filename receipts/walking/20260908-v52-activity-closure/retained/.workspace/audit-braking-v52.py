"""Offline evidence audit; no simulation, training or artifact selection."""
import gzip, json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import onnxruntime as ort
import torch
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest
from microduck.braking_v52 import BrakeNet,BrakeController
OUT=ROOT/'outputs/walking-braking-v52';OUT.mkdir(exist_ok=True)
run=ROOT/'logs/braking-distill-20260908-v52';r=json.loads((run/'run.json').read_text())
assert r['status']=='completed' and r['steps']==2000 and r['new_rl_transitions']==0 and not r['policy_activated']
counts={str(run.relative_to(ROOT)):manifest(run)}
freezes={}
for p in [ROOT/'experiments/walking/recovery-freeze-v51.json',*sorted((ROOT/'experiments/walking').glob('braking-*freeze-v52.json'))]:
 f=json.loads(p.read_text());sources=f['source_sha256']
 for name,h in sources.items():assert digest(ROOT/name)==h,name
 freezes[p.name]={'sha256':digest(p),'verified_sources':len(sources)}
loss=[json.loads(x) for x in (run/'learning.jsonl').read_text().splitlines()]
assert len(loss)==2000 and [x['step'] for x in loss]==list(range(2000)) and all(np.isfinite(x['loss']) for x in loss)
assert digest(run/'model.pt')==r['checkpoint_sha256'] and digest(run/'policy.onnx')==r['policy_sha256']
opt=ort.SessionOptions();opt.intra_op_num_threads=1;opt.inter_op_num_threads=1
def session(p):return ort.InferenceSession(str(p),sess_options=opt,providers=['CPUExecutionProvider'])
def infer(s,x):return s.run(None,{s.get_inputs()[0].name:x[None]})[0][0]
brake=session(run/'policy.onnx');base=ROOT/'receipts/walking/20260908-v50-retention-flat'
actors=[session(base/'policy.onnx'),session(base/'standing/policy.onnx')]
dataset=ROOT/'experiments/walking/braking-replay-v52';counts[str(dataset.relative_to(ROOT))]=manifest(dataset)
with np.load(dataset/'replay.npz') as d:x=d['observations'];y=d['residuals'];pos=d['positive']
assert x.shape==(12000,61) and y.shape==(12000,14) and pos.sum()==375 and not np.any(y[~pos])
provenance=json.loads((dataset/'provenance.json').read_text());offset=0
for src in provenance['sources']:
 folder=ROOT/src['source'];n=src['rows'];counts[src['source']]=manifest(folder) if (folder/'SHA256SUMS').exists() else 0
 if src['kind']=='eligible_recovery':
  assert digest(folder/'observations-float32.npy')==src['observations_sha256'] and digest(folder/'actions-float32.npy')==src['actions_sha256']
  obs=np.load(folder/'observations-float32.npy')[:125];a=np.load(folder/'actions-float32.npy')[:125]
  target=np.array([act-infer(actors[int((row[48:51]==0).all())],row) for act,row in zip(a,obs)],np.float32)
 else:
  assert digest(folder/'SHA256SUMS')==src['manifest_sha256']
  p=folder/('evaluation.json' if (folder/'evaluation.json').exists() else 'probe.json');rr=json.loads(p.read_text());allowed={c['case_id'] for c in rr['case_reports'] if c['passed']}
  if 'session_reports' in rr:
   passed={s['session_id'] for s in rr['session_reports'] if s['passed']};allowed={c for c in allowed if c.split('--window-')[0] in passed}
  obs=[]
  with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
   for line in f:
    row=json.loads(line)
    if row['case_id'] in allowed and 13.<row['time_s']<=15.5:obs.append(row['actor_observation'])
  obs=np.asarray(obs,np.float32);target=np.zeros((n,14),np.float32)
 assert len(obs)==n and obs.tobytes()==x[offset:offset+n].tobytes() and target.tobytes()==y[offset:offset+n].tobytes(),src['source']
 offset+=n
assert offset==len(x)
state=torch.load(run/'model.pt',map_location='cpu',weights_only=True);model=BrakeNet(torch.zeros(61),torch.ones(61));model.load_state_dict(state);model.eval();torch.set_num_threads(1)
np.testing.assert_array_equal(state['mean'].numpy(),torch.from_numpy(x).mean(0).numpy());np.testing.assert_array_equal(state['scale'].numpy(),torch.from_numpy(x).std(0).clamp_min(.05).numpy())
with torch.no_grad():pred=model(torch.from_numpy(x)).numpy()
export_error=max(float(np.abs(infer(brake,row)-target).max()) for row,target in zip(x,pred));assert export_error<1e-4
result={'passed':True,'behavior_accepted':False,'frozen_sources':freezes,'training':{**{k:v for k,v in r.items() if k!='source_sha256'},'verified_loss_rows':len(loss),'verified_replay_rows':len(x),'recomputed_export_max_error':export_error},'banks':{},'manifests':counts}
nominal=[]
for bank in ['flat','repeated','endurance','surfaces']:
 folder=ROOT/f'receipts/walking/20260908-v52-braking-{bank}';prior=ROOT/f'receipts/walking/20260908-v50-retention-{bank}';counts[str(folder.relative_to(ROOT))]=manifest(folder)
 name='evaluation.json' if bank in ['flat','repeated'] else 'probe.json';rr=json.loads((folder/name).read_text());old=json.loads((prior/name).read_text())
 assert not rr['reserved_opened'] and not rr['physical_transfer_validated'] and rr['braking_policy_sha256']==r['policy_sha256']
 for name in ['policy_sha256','standing_policy_sha256']:assert rr[name]==old[name]
 assert digest(folder/'braking/policy.onnx')==r['policy_sha256'] and digest(folder/'braking/model.pt')==r['checkpoint_sha256']
 ef=json.loads((folder/'evaluator-freeze.json').read_text());assert digest(folder/'evaluator-freeze.json')==rr['evaluator_freeze_sha256']
 for name,h in ef['source_sha256'].items():assert digest(folder/'evaluator-source'/name)==h
 first={c['case_id'] for c in rr['case_reports'] if c.get('window_start_s',c.get('session_window_start_s',0))==0}
 prefix={}
 def values(row):return tuple(np.asarray(row[k],np.float32 if k in ['actor_observation','action_rad'] else np.float64).tobytes() for k in ['actor_observation','action_rad','qpos','qvel'])
 with gzip.open(prior/'trajectory.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line)
   if row['case_id'] in first and row['time_s']<=13.:prefix[(row['case_id'],round(row['time_s']*50))]=values(row)
 controllers={};data=defaultdict(lambda:{'controls':0,'active_controls':0,'max_residual_rad':0.,'first_fall_s':None,'first_joint_margin_failure_s':None,'first_nonfoot_support_s':None});action_arrays={};verified_prefix=0;maxerr=0
 with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
  for line in f:
   row=json.loads(line);cid=row['case_id'];d=data[cid];sid=cid.split('--window-')[0].split('--repeat-')[0];ctrl=controllers.setdefault(sid,BrakeController(brake));ctrl.prepare(row['command'])
   assert ctrl.age==row['braking_age'] and ctrl.active==row['braking_active'],(bank,cid,row['time_s'])
   obs=np.asarray(row['actor_observation'],np.float32);act=np.asarray(row['action_rad'],np.float32)
   if cid not in action_arrays:action_arrays[cid]=np.load(folder/f'{cid}-actions-float32.npy')
   assert act.tobytes()==action_arrays[cid][d['controls']].tobytes() and len(row['self_load_physics'])==4
   delta=infer(brake,obs) if ctrl.active else np.zeros(14,np.float32);expected=(infer(actors[int(row['actor_mode']=='standing')],obs)+delta).astype(np.float32)
   err=float(np.abs(expected-act).max());assert err<1e-4;maxerr=max(maxerr,err)
   key=(cid,round(row['time_s']*50))
   if key in prefix:assert values(row)==prefix[key],(bank,key);verified_prefix+=1
   d['controls']+=1;d['active_controls']+=int(ctrl.active);d['max_residual_rad']=max(d['max_residual_rad'],float(abs(delta).max()))
   for prop,failed in [('first_fall_s',row['fell']),('first_joint_margin_failure_s',row['minimum_actual_joint_margin_rad']<.02),('first_nonfoot_support_s',bool(row['nonfoot_ground_contacts']))]:
    if failed and d[prop] is None:d[prop]=row['time_s']
   if bank=='flat' and cid=='nominal-20-20ms--forward-08' and ctrl.active:
    nominal.append({'time_s':row['time_s'],'tilt_deg':row['tilt_deg'],'delta':delta.tolist(),'observation':obs.tolist(),'fell':row['fell']})
 for cid,a in action_arrays.items():assert len(a)==data[cid]['controls']
 assert verified_prefix==len(prefix)
 for c in rr['case_reports']:data[c['case_id']].update(passed=c['passed'],failures=c['failures'])
 result['banks'][bank]={'controls':sum(d['controls'] for d in data.values()),'verified_exact_prefix_controls':verified_prefix,'maximum_runtime_action_error':maxerr,'cases':dict(data),'passed_cases':sum(c['passed'] for c in rr['case_reports']),'total_cases':len(rr['case_reports']),'sessions':rr.get('session_reports',[])}
 print(bank,result['banks'][bank]['controls'],sum(c['passed'] for c in rr['case_reports']),len(rr['case_reports']),flush=True)
# Same-observation residual error on a formerly successful stop; nearest replay distance is diagnostic, not admission.
from scipy.spatial.distance import cdist
scale=state['scale'].numpy();normalized=x/scale
for item in nominal:
 ob=np.asarray(item.pop('observation'),np.float32);distance=cdist((ob/scale)[None],normalized,'euclidean')[0];j=int(distance.argmin());item.update(nearest_replay_distance=float(distance[j]),nearest_replay_positive=bool(pos[j]),max_abs_residual_rad=max(abs(v) for v in item['delta']))
result['first_flat_failure_braking_trace']=nominal
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASSED offline evidence audit; behavior rejected',flush=True)
