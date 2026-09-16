import gzip,hashlib,json
from pathlib import Path
import torch,numpy as np
from scripts.train_native_retention_v50 import PARENTS,binding,FREEZE
from experiments.walking.native_candidate_v50 import candidate_sha,RUN
assert binding()==json.loads(FREEZE.read_text())
sha=candidate_sha();f=Path('logs')/RUN;r=json.loads((f/'run.json').read_text());joint=torch.load(f/r['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
report={}
for role,run in PARENTS.items():
 p=Path('logs')/run;parent=json.loads((p/'run.json').read_text());orig=torch.load(p/parent['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
 c=Path('logs')/(RUN+'-'+role);cr=json.loads((c/'run.json').read_text());split=torch.load(c/cr['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
 for key,value in split.items():
  assert torch.isfinite(value).all() and torch.equal(value,joint[role+'.'+key])
  if role=='standing' or key.startswith('obs_normalizer.'):assert value.numpy().tobytes()==orig[key].numpy().tobytes()
  if role=='walking':assert orig[key].numpy().tobytes()==joint['teacher.'+key].numpy().tobytes()
 changes={k:float((v-orig[k]).abs().max()) for k,v in split.items() if k.startswith('mlp.')}
 report[role]={'maximum_weight_change':max(changes.values()),'exact_component_split':True,'parent_normalizer_frozen':True}
assert report['walking']['maximum_weight_change']>0 and report['standing']['maximum_weight_change']==0
for role,dim in [('observation',61),('action',14)]:
 raw=gzip.open(f/('all-'+role+'s-float32.bin.gz'),'rb').read()
 assert len(raw)==864000*dim*4 and np.isfinite(np.frombuffer(raw,dtype='<f4')).all()
 assert hashlib.sha256(raw).hexdigest()==r['final_coverage'][role+'_raw_sha256']
 report[role]={'rows':864000,'all_finite':True,'raw_digest_verified':True}
Path('.workspace/v50-checkpoint-check.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
