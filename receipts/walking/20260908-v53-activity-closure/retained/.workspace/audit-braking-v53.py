"""Offline evidence audit; no simulation, training or artifact selection."""
import gzip, json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np
import onnxruntime as ort
import torch
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest
from microduck.braking_v53 import BrakeNet,BrakeController
OUT=ROOT/'outputs/walking-braking-v53';OUT.mkdir(exist_ok=True)
run=ROOT/'logs/braking-retention-20260908-v53';r=json.loads((run/'run.json').read_text())
assert r['status']=='completed' and r['steps']==8000 and r['new_rl_transitions']==0 and not r['policy_activated']
counts={str(run.relative_to(ROOT)):manifest(run)}
freezes={}
for p in [ROOT/'experiments/walking/retention-collection-freeze-v53.json',*sorted((ROOT/'experiments/walking').glob('braking-*freeze-v53.json'))]:
 f=json.loads(p.read_text());sources=f['source_sha256']
 for name,h in sources.items():assert digest(ROOT/name)==h,name
 freezes[p.name]={'sha256':digest(p),'verified_sources':len(sources)}
loss=[json.loads(x) for x in (run/'learning.jsonl').read_text().splitlines()]
assert len(loss)==8000 and [x['step'] for x in loss]==list(range(8000)) and all(np.isfinite(x['loss']) for x in loss)
assert digest(run/'model.pt')==r['checkpoint_sha256'] and digest(run/'policy.onnx')==r['policy_sha256']
opt=ort.SessionOptions();opt.intra_op_num_threads=1;opt.inter_op_num_threads=1
def session(p):return ort.InferenceSession(str(p),sess_options=opt,providers=['CPUExecutionProvider'])
def infer(s,x):return s.run(None,{s.get_inputs()[0].name:x[None]})[0][0]
brake=session(run/'policy.onnx');base=ROOT/'receipts/walking/20260908-v50-retention-flat'
actors=[session(base/'policy.onnx'),session(base/'standing/policy.onnx')]
dataset=ROOT/'experiments/walking/braking-replay-v53';counts[str(dataset.relative_to(ROOT))]=manifest(dataset)
with np.load(dataset/'replay.npz') as d:x=d['observations'];y=d['residuals'];pos=d['positive']
assert x.shape==(13055,61) and y.shape==(13055,14) and pos.sum()==500 and not np.any(y[~pos])
provenance=json.loads((dataset/'provenance.json').read_text());offset=0
collection=ROOT/'receipts/walking/20260908-v53-retention-collection';counts[str(collection.relative_to(ROOT))]=manifest(collection)
assert digest(collection/'SHA256SUMS')==provenance['collection_manifest_sha256']
cr=json.loads((collection/'result.json').read_text());assert cr['complete'] and cr['eligible_branches']==9 and len(cr['branches'])==18
for b in cr['branches']:
 folder=ROOT/b['branch'];aa=np.load(folder/'actions-float32.npy');oo=np.load(folder/'observations-float32.npy')
 assert len(aa)==len(oo)==b['observed_controls']-b['start_control'] and b['repeat_exact']
 with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
  for i,line in enumerate(f):
   row=json.loads(line);assert np.asarray(row['action_rad'],np.float32).tobytes()==aa[i].tobytes() and np.asarray(row['actor_observation'],np.float32).tobytes()==oo[i].tobytes() and len(row['self_load_physics'])==4
for src in provenance['sources']:
 folder=ROOT/src['source'];n=src['rows']
 if 'manifest_sha256' in src:counts[src['source']]=manifest(folder);assert digest(folder/'SHA256SUMS')==src['manifest_sha256']
 if src['kind']=='original_zero_labels':
  with np.load(folder/'replay.npz') as data:keep=~data['positive'];obs=data['observations'][keep];target=data['residuals'][keep]
 elif src['kind']=='actual_successful_downhill_brakes_yaw_still_failed':
  rr=json.loads((folder/'probe.json').read_text());allowed={'mean_abs_yaw_error_rad_s','endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s'}
  accepted={c['case_id'] for c in rr['case_reports'] if c['case_id'].startswith('downhill') and c['observed_duration_s']==18 and not(set(c['failures'])-allowed)};assert len(accepted)==4
  obs=[];target=[]
  with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
   for line in f:
    row=json.loads(line)
    if row['case_id'] in accepted and row['braking_active']:
     ob=np.asarray(row['actor_observation'],np.float32);obs.append(ob);target.append(np.asarray(row['action_rad'],np.float32)-infer(actors[int(row['actor_mode']=='standing')],ob))
  obs=np.asarray(obs,np.float32);target=np.asarray(target,np.float32)
 else:
  for name,key in [('observations-float32.npy','observations_sha256'),('actions-float32.npy','actions_sha256'),('branch-result.json','branch_result_sha256')]:assert digest(folder/name)==src[key]
  report=json.loads((folder/'branch-result.json').read_text());assert report['passed'] and report['demonstration_eligible'] and report['mode']=='base' and report['observed_controls']==900 and report['start_control']+n==775
  obs=np.load(folder/'observations-float32.npy')[:n];a=np.load(folder/'actions-float32.npy')[:n];target=np.zeros((n,14),np.float32)
  for ob,act in zip(obs,a):assert infer(actors[int((ob[48:51]==0).all())],ob).tobytes()==act.tobytes()
 assert len(obs)==n and obs.tobytes()==x[offset:offset+n].tobytes() and target.tobytes()==y[offset:offset+n].tobytes(),src['source']
 offset+=n
assert offset==len(x)
pools=[json.loads(line) for line in (run/'hard-pools.jsonl').read_text().splitlines()];assert len(pools)==160 and [p['step'] for p in pools]==list(range(0,8000,50))
for p in pools:assert len(set(p['row_indices']))==128 and all(0<=i<len(x) and not pos[i] for i in p['row_indices']) and np.isfinite(p['maximum_error_rad'])
for entry in loss:assert all(np.isfinite(entry['components'])) and abs(entry['loss']-(entry['components'][0]+8*entry['components'][1]+8*entry['components'][2]))<1e-3
state=torch.load(run/'model.pt',map_location='cpu',weights_only=True);model=BrakeNet(torch.zeros(61),torch.ones(61));model.load_state_dict(state);model.eval();torch.set_num_threads(1)
parent=torch.load(ROOT/'logs/braking-distill-20260908-v52/model.pt',map_location='cpu',weights_only=True)
assert torch.equal(state['mean'],parent['mean']) and torch.equal(state['scale'],parent['scale'])
assert digest(ROOT/'logs/braking-distill-20260908-v52/model.pt')==r['parent_checkpoint_sha256']
with torch.no_grad():pred=model(torch.from_numpy(x)).numpy()
export_error=max(float(np.abs(infer(brake,row)-target).max()) for row,target in zip(x,pred));assert export_error<1e-4
result={'collection':{k:v for k,v in cr.items() if k!='branches'},'verified_hard_pools':len(pools),'passed':True,'behavior_accepted':False,'frozen_sources':freezes,'training':{**{k:v for k,v in r.items() if k!='source_sha256'},'verified_loss_rows':len(loss),'verified_replay_rows':len(x),'recomputed_export_max_error':export_error},'banks':{},'manifests':counts}
nominal=[]
for bank in ['flat','repeated','endurance','surfaces']:
 folder=ROOT/f'receipts/walking/20260908-v53-braking-{bank}';prior=ROOT/f'receipts/walking/20260908-v50-retention-{bank}';counts[str(folder.relative_to(ROOT))]=manifest(folder)
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
result['nominal_stop_braking_trace']=nominal
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASSED offline evidence audit; behavior rejected',flush=True)
