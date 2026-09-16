import gzip,json
from pathlib import Path
import numpy as np
import sys
root=Path.cwd();sys.path.insert(0,str(root))
from experiments.walking.recovery_v49 import digest,manifest
result={}
for name in ['20260906-v30-heading-endurance','20260907-v46-retention-endurance','20260908-v48-standing-retention-endurance']:
 folder=root/'receipts/walking'/name;manifest(folder)
 path=folder/'trajectory.jsonl.gz'
 if not path.exists():path=folder/'trajectory.jsonl'
 data={}
 with (gzip.open(path,'rt') if path.suffix=='.gz' else path.open()) as stream:
  for line in stream:
   r=json.loads(line)
   if r['session_id'].startswith('downhill') and r['case_id'].endswith('window-1') and 2<=r['time_s']<=13:data.setdefault(r['session_id'],[]).append(r)
 stats={}
 for case,rows in data.items():
  assert len(rows)==551 and all(r['command'][2]==0 for r in rows)
  yaw=np.array([r['yaw_rate_rad_s'] for r in rows]);cmd=np.array([r['policy_command'][2] for r in rows])
  stats[case]=dict(controls=len(rows),mean_abs_yaw_error_rad_s=float(abs(yaw).mean()),signed_mean_yaw_rate_rad_s=float(yaw.mean()),mean_abs_policy_yaw_command_rad_s=float(abs(cmd).mean()),threshold_rad_s=.2,pre_intervention=True)
 result[name]=dict(manifest_sha256=digest(folder/'SHA256SUMS'),trace_sha256=digest(path),cases=stats)
(root/'.workspace/v49-prestop-audit-verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
