"""Read recorded yaw/face/action signals to scope a subsequent objective audit."""
import gzip,json,shutil,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.yaw_v55 import digest,write_manifest
from microduck.constants import HEAD_JOINT_IDS,DEFAULT_JOINT_POS

def main():
 out=ROOT/'outputs/walking-yaw-v55/objective-audit'
 if out.exists():raise FileExistsError(out)
 reports={};sources={}
 for bank in ('endurance','fresh'):
  folder=ROOT/f'receipts/walking/20260912-v55-yaw6-{bank}';path=folder/'trajectory.jsonl.gz'
  sources[bank]={f:digest(folder/f) for f in ('trajectory.jsonl.gz','probe.json','SHA256SUMS')}
  cases={}
  with gzip.open(path,'rt') as f:
   for line in f:
    r=json.loads(line)
    if r['case_id'].startswith('downhill'):cases.setdefault(r['case_id'],[]).append(r)
  result=json.loads((folder/'probe.json').read_text())
  for case,rows in cases.items():
   stop=[r for r in rows if r['time_s']>=16]
   head=np.asarray([r['qpos'][7:] for r in stop])[:,HEAD_JOINT_IDS]-np.asarray(DEFAULT_JOINT_POS)[list(HEAD_JOINT_IDS)]
   tilt=np.asarray([r['tilt_deg'] for r in stop])
   face=np.degrees(np.arcsin(np.clip(np.abs(np.asarray([r['face_world'][2] for r in stop])),0,1)))
   cost=2*np.mean((np.maximum(abs(head)-.2,0)/.15)**2,axis=1)
   bodycost=4*(np.maximum(tilt-10,0)/5)**2
   assert len(stop)==101 and all(r['actor_mode']=='standing' for r in stop)
   reported=next(c for c in result['case_reports'] if c['case_id']==case)
   assert float(face.mean())==reported['endurance']['final_standing_posture']['mean_absolute_face_pitch_deg']
   moving=np.asarray([2<=r['time_s']<=13 for r in rows]);yaw=np.asarray([r['yaw_rate_rad_s'] for r in rows])[moving]
   actions=np.load(folder/(case+'-actions-float32.npy'))[moving]
   freq=np.fft.rfftfreq(len(yaw),.02);ys=abs(np.fft.rfft(yaw-yaw.mean()))**2
   power=abs(np.fft.rfft(actions-actions.mean(0),axis=0))**2
   reports[case]=dict(standing_samples=len(stop),face_pitch_deg_mean=float(face.mean()),
    mean_tilt_deg=float(tilt.mean()),head_joint_mean_abs_rad=abs(head).mean(0).tolist(),
    mean_head_reward_cost=float(cost.mean()),mean_body_tilt_reward_cost=float(bodycost.mean()),
    zero_head_and_tilt_cost_while_face_above_30_samples=int(((cost==0)&(bodycost==0)&(face>30)).sum()),
    yaw_spectrum_peak_hz=float(freq[1+np.argmax(ys[1:])]),
    action_spectrum_peak_hz=float(freq[1+np.argmax(power[1:].sum(1))]),
    action_power_above_8hz_fraction=float(power[freq>8].sum()/power[1:].sum()),
    action_rms_step_change_rad=float(np.sqrt(np.mean(np.diff(actions,axis=0)**2))))
 out.mkdir(parents=True);shutil.copy2(__file__,out/Path(__file__).name)
 (out/'audit.json').write_text(json.dumps(dict(cases=reports,sources=sources,
  boundary='Post-hoc recorded-signal audit. Head/body cost is reconstructed from V55 source and recorded state; not the full reward. Spectra are descriptive and do not establish a physical cause or select a filter. No new physics, policy change or gate relaxation.'),indent=2)+'\n')
 write_manifest(out)
 print(json.dumps(reports,indent=1))
if __name__=='__main__':main()
