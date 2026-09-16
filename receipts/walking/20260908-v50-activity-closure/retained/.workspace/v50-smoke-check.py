import gzip,json,hashlib
from pathlib import Path
import numpy as np
import torch
from scripts.train_native_retention_v50 import binding,FREEZE,PARENTS
from microduck.native_sequence_env_v50 import BUCKETS
folder=Path('logs/retention-native-20260908-v50-smoke');r=json.loads((folder/'run.json').read_text())
assert r['status']=='completed' and r['new_transitions']==2880 and r['checkpoint']=='model_4.pt'
assert binding()==json.loads(FREEZE.read_text())
a=torch.load(folder/r['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
assert all(torch.isfinite(x).all() for x in a.values())
for role in ['standing','walking']:
 p=Path('logs')/PARENTS[role];pr=json.loads((p/'run.json').read_text());state=torch.load(p/pr['checkpoint'],map_location='cpu',weights_only=True)['actor_state_dict']
 for k,v in state.items():
  if role=='standing' or k.startswith('obs_normalizer.'):
   assert a[role+'.'+k].numpy().tobytes()==v.numpy().tobytes()
  if role=='walking':assert a['teacher.'+k].numpy().tobytes()==v.numpy().tobytes()
obs=np.frombuffer(gzip.open(folder/'all-observations-float32.bin.gz','rb').read(),dtype='<f4').reshape(120,24,61)
act=np.frombuffer(gzip.open(folder/'all-actions-float32.bin.gz','rb').read(),dtype='<f4').reshape(120,24,14)
reward=np.frombuffer(gzip.open(folder/'all-reward-components-float32.bin.gz','rb').read(),dtype='<f4').reshape(120,24,6)
assert all(np.isfinite(x).all() for x in [obs,act,reward])
np.testing.assert_array_equal(reward[:,:,5],(obs[:,:,48:51]==0).all(2))
mask=np.array([b[1]>0 for b in BUCKETS])[None,:] & (reward[:,:,5]==0)
np.testing.assert_allclose(reward[:,:,2],np.where(mask,3*abs(reward[:,:,0]-reward[:,:,1])/.2,0),rtol=2e-6,atol=2e-6)
np.testing.assert_allclose(reward[:,:,4],reward[:,:,3]-.02*reward[:,:,2],rtol=2e-6,atol=2e-6)
proof=dict(passed=True,transitions=r['new_transitions'],elapsed_s=r['elapsed_s'],exact_fixed_stander_teacher_and_normalizers=True,reward_and_role_mask_all_rows_verified=True,each_cell_standing_and_walking=bool(((reward[:,:,5]==0).sum(0)>0).all() and ((reward[:,:,5]==1).sum(0)>0).all()))
assert proof['each_cell_standing_and_walking']
Path('.workspace/v50-smoke-check.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
