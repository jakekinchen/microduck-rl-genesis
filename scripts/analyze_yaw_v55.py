"""Compare immutable V55 finals and V54 references; no physics or score changes."""
import argparse,gzip,json,shutil
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from experiments.walking.yaw_v55 import digest,write_manifest,run_name

def read(folder):
    return json.loads((folder/'probe.json').read_text())

def report_case(c):
    return {k:c[k] for k in ('case_id','passed','failures','metrics','observed_duration_s','required_duration_s') if k in c} | {
        'final_standing_posture':c.get('endurance',{}).get('final_standing_posture'),
        'heading':c.get('endurance',{}).get('full_horizon_heading'),
        'tracking_buckets':c.get('endurance',{}).get('tracking_buckets')}

def load_rows(folder):
    rows=[]
    with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:
        for line in f: rows.append(json.loads(line))
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    lanes=[('V54 parent','20260909-v54-shared-endurance','20260912-v55-parent-fresh','#536170'),
        ('V55 control','20260912-v55-control-endurance','20260912-v55-control-fresh','#0072B2'),
        ('V55 yaw ×2','20260912-v55-yaw6-endurance','20260912-v55-yaw6-fresh','#D55E00')]
    result={'sources':{},'lanes':{},'boundary':'Post-hoc descriptive comparison on exposed simulator recordings. Different closed-loop actions do not isolate a physics cause; no physical calibration or transfer evidence.'}
    fig,axes=plt.subplots(3,2,figsize=(12,9),sharex='col',layout='constrained')
    fields=[('yaw_rate_rad_s','Yaw rate (rad/s)'),('tilt_deg','Body tilt (degrees)'),('speed_m_s','Horizontal speed (m/s)')]
    for label,old,new,color in lanes:
        result['lanes'][label]={}
        for col,(bank,name,session) in enumerate([('original',old,'downhill-3deg-start-1'),('new',new,'downhill-3deg-v55-yaw-1')]):
            folder=ROOT/'receipts/walking'/name;r=read(folder)
            assert r['complete'] and r['exception'] is None and not r['held_out']
            rows=load_rows(folder)
            result['sources'][name]={f:digest(folder/f) for f in ('probe.json','SHA256SUMS','trajectory.jsonl.gz')}
            falls=[{'session':x['session_id'],'case':x['case_id'],'time_s':x['session_time_s'],'actor_mode':x['actor_mode']} for x in rows if x['fell']]
            result['lanes'][label][bank]={'cases':[report_case(c) for c in r['case_reports']],
                'sessions':[{k:s[k] for k in ('session_id','passed','failures','whole_session_heading')} for s in r['session_reports']],
                'falls':falls,'yaw_diagnostic':{}}
            for c in r['case_reports']:
                if not c['case_id'].startswith('downhill'): continue
                # Match the primary evaluator's inclusive endpoints (2 <= t <= 13).
                chosen=[x for x in rows if x['case_id']==c['case_id'] and 2 <= x['time_s'] <= 13]
                if chosen:
                    errors=np.asarray([x['yaw_rate_rad_s']-x['command'][2] for x in chosen])
                    if 'mean_abs_yaw_error_rad_s' in c['metrics']:
                        assert float(abs(errors).mean()) == c['metrics']['mean_abs_yaw_error_rad_s']
                    result['lanes'][label][bank]['yaw_diagnostic'][c['case_id']]={
                        'signed_mean_rad_s':float(errors.mean()),'mean_absolute_rad_s':float(abs(errors).mean()),
                        'rms_rad_s':float(np.sqrt((errors**2).mean())),'samples':len(errors)}
            chosen=[x for x in rows if x['session_id']==session]
            for row,(field,ylabel) in enumerate(fields):
                axes[row,col].plot([x['session_time_s'] for x in chosen],[x[field] for x in chosen],color=color,lw=.9,label=label)
                if chosen[-1]['fell']: axes[row,col].scatter(chosen[-1]['session_time_s'],chosen[-1][field],marker='x',color=color,s=40)
                axes[row,col].set_ylabel(ylabel);axes[row,col].grid(alpha=.2)
    for col in range(2):
        axes[0,col].set_title(['Original downhill start 1','New downhill initial heading .04 rad'][col])
        for ax in axes[:,col]:
            for t in (13,31): ax.axvline(t,color='#999999',ls='--',lw=1)
            ax.set_xlim(0,36)
        axes[-1,col].set_xlabel('Recorded time (s); dashed lines = stop requests')
    axes[0,0].legend(fontsize=8);fig.suptitle('V55 actual recorded locomotion and stops — curves end at terminal recording')
    for arm in ('control','yaw6'):
        folder=ROOT/'logs'/run_name(arm);r=json.loads((folder/'run.json').read_text());c=r['final_coverage']
        bymode=Counter();last={}
        with gzip.open(folder/'handoff-histories.jsonl.gz','rt') as f:
            for line in f:
                x=json.loads(line);last[(x['env'],x['episode'])]=x
        with gzip.open(folder/'episodes.jsonl.gz','rt') as f:
            for line in f:
                x=json.loads(line)
                if x['fell']:
                    switch=last.get((x['env'],x['episode']))
                    mode=switch['direction'] if switch else 'initial_standing'
                    bymode[(c['buckets'][x['bucket']],mode)]+=1
        result['lanes']['V55 '+('control' if arm=='control' else 'yaw ×2')]['training']={
            'long_completion_cells':sum(n[2]>0 for n in c['curriculum_completions']),
            'missing_long_cells':[b for b,n in zip(c['buckets'],c['curriculum_completions']) if not n[2]],
            'falls_by_cell_last_switch':[{ 'cell':b,'last_switch':m,'falls':n} for (b,m),n in sorted(bymode.items())],
            'elapsed_s':r['elapsed_s'],'transitions':r['new_transitions']}
    a.output.mkdir(parents=True);fig.savefig(a.output/'yaw-and-stops.png',dpi=160);plt.close(fig)
    shutil.copy2(__file__,a.output/Path(__file__).name)
    (a.output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');write_manifest(a.output)
if __name__=='__main__':main()
