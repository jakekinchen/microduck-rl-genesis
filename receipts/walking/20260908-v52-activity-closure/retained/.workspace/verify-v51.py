import gzip,json,hashlib
from pathlib import Path
import numpy as np
from experiments.walking.recovery_v51 import CAPTURE,COMPARE,SEARCH,manifest
for p in [CAPTURE,COMPARE,SEARCH]:manifest(p)
r=json.loads((SEARCH/'result.json').read_text());a=gzip.open(SEARCH/'all-actions-float32.bin.gz','rb').read();o=gzip.open(SEARCH/'all-observations-float32.bin.gz','rb').read();offset=0;n=0
for line in (SEARCH/'trials.jsonl').read_text().splitlines():
 t=json.loads(line);assert t['raw_row_offset']==offset
 for raw,dim,key in [(a,14,'action_sha256'),(o,61,'observation_sha256')]:
  part=raw[offset*dim*4:(offset+t['controls'])*dim*4];assert hashlib.sha256(part).hexdigest()==t[key] and np.isfinite(np.frombuffer(part,dtype='<f4')).all()
 offset+=t['controls'];n+=1
assert offset==r['search_controls'] and n==r['search_trials']==384 and len(a)==offset*14*4 and len(o)==offset*61*4
c=json.loads((COMPARE/'result.json').read_text());repeats=sum(b['suffix_controls'] for b in c['branches']);assert len(c['branches'])==12 and all(b['repeat_exact'] for b in c['branches'])
for base in [COMPARE,SEARCH]:
 for p in base.glob('*/branch-result.json'):
  report=json.loads(p.read_text());folder=p.parent
  actions=np.load(folder/'actions-float32.npy');obs=np.load(folder/'observations-float32.npy');assert len(actions)==len(obs)==report['suffix_controls']
  with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
   rows=[json.loads(x) for x in f]
  assert len(rows)==len(actions)
  for row,x in zip(rows,obs):assert np.asarray(row['actor_observation'],np.float32).tobytes()==x.tobytes() and len(row['self_load_physics'])==4
out=dict(passed=True,search_trials=n,search_controls=offset,comparison_repeated_controls=repeats,source_controls=1391,reset_controls=150,eligible_demonstrations=3,complete_session_passes=sum(b['passed'] for b in c['branches']))
Path('.workspace/v51-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
