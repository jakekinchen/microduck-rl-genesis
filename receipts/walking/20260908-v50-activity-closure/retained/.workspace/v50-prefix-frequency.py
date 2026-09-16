import gzip,json
from pathlib import Path
import numpy as np
path=Path('receipts/walking/20260906-v30-heading-endurance/trajectory.jsonl')
if not path.exists():path=path.with_suffix('.jsonl.gz')
opener=gzip.open if path.suffix=='.gz' else open
cases={f'downhill-3deg-start-{i}--window-1':[] for i in [1,2]}
with opener(path,'rt') as f:
 for line in f:
  row=json.loads(line)
  if row['case_id'] in cases and 2.-1e-9<=row['time_s']<=13.+1e-9:cases[row['case_id']].append(row)
out={}
for name,rows in cases.items():
 y=np.array([r['yaw_rate_rad_s'] for r in rows]);n=len(y);power=abs(np.fft.rfft((y-y.mean())*np.hanning(n)))**2;freq=np.fft.rfftfreq(n,.02);power[0]=0
 out[name]={'rows':n,'dominant_yaw_frequency_hz':float(freq[power.argmax()]),'mean_absolute_yaw_rad_s':float(abs(y).mean()),'signed_mean_yaw_rad_s':float(y.mean()),'boundary':'Descriptive spectrum of the same exposed 2-13 s prefix, not a causal diagnosis or changed gate.'}
Path('.workspace/v50-baseline-frequency.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
