"""Frozen common-grid numerical screens; original behavior thresholds retained."""
from pathlib import Path
import gzip
import json
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def load(p): return json.loads(p.read_text())


def compare(a,b,runroot):
    pa=runroot/a['id'];pb=runroot/b['id']
    ra=load(pa/'result.json');rb=load(pb/'result.json')
    common=max(a['dt_s'],b['dt_s'])
    sa=round(common/a['dt_s']);sb=round(common/b['dt_s'])
    with np.load(pa/'dynamics.npz') as x,np.load(pb/'dynamics.npz') as y:
        qa=x['qpos'][sa-1::sa];qb=y['qpos'][sb-1::sb];n=min(len(qa),len(qb))
        assert n>0
        root=float(np.linalg.norm(qa[:n,:3]-qb[:n,:3],axis=1).max())
        joints=float(np.abs(qa[:n,7:]-qb[:n,7:]).max())
    peaks=[]
    for path,c in ((pa,a),(pb,b)):
        m=[0.,0.]
        with gzip.open(path/'physics.jsonl.gz','rt') as stream:
            for line in stream:
                r=json.loads(line)
                if r['time_s']>n*common+1e-8:break
                m=[max(m[0],r['ground_penetration_m']),max(m[1],r['internal_penetration_m'])]
        peaks.append(m)
    ta=ra['physics_sample_count']*a['dt_s'];tb=rb['physics_sample_count']*b['dt_s']
    return {'a':a['id'],'b':b['id'],'common_duration_s':n*common,'root_max_m':root,
        'joint_max_rad':joints,'common_prefix_ground_peaks_m':[p[0] for p in peaks],
        'common_prefix_internal_peaks_m':[p[1] for p in peaks],
        'ground_peak_delta_m':abs(peaks[0][0]-peaks[1][0]),
        'internal_peak_delta_m':abs(peaks[0][1]-peaks[1][1]),
        'terminal_time_delta_s':abs(ta-tb),'terminal_times_s':[ta,tb],
        'same_terminal_category':ra['stop_reason']==rb['stop_reason'],
        'full_prefix_ground_peaks_m':[ra['maximum_ground_penetration_m'],rb['maximum_ground_penetration_m']]}


def main():
    b=load(BASE/'feedback-bank.json');review=load(BASE/'all-feedback-review.json')
    assert review['verification_passed'] and review['cases_verified']==24
    root=ROOT/b['output_root']; first=[c for c in b['cases'] if c['repeat']==1]
    def case(model,mode,dt):return next(c for c in first if c['model']==model and c['feedback']==mode and c['dt_s']==dt)
    numerical=[];interventions=[]
    for model in b['models']:
        for mode in ('native','fixed_5ms'):
            r=compare(case(model,mode,.0025),case(model,mode,.00125),root)
            r['model']=model;r['feedback']=mode
            r['failures']=[key for key,limit in b['convergence_screen'].items() if key!='same_terminal_category_required' and r[key]>limit]
            if not r['same_terminal_category']:r['failures'].append('terminal_category')
            r['numerical_screen_passed']=not r['failures']; numerical.append(r)
        for dt in (.005,.0025,.00125):
            r=compare(case(model,'native',dt),case(model,'fixed_5ms',dt),root)
            r.update(model=model,dt_s=dt);interventions.append(r)
    summary=[]
    for c in first:
        r=load(root/c['id']/'result.json')
        summary.append({'case':c['id'],'time_s':r['physics_sample_count']*c['dt_s'],
            'completed':r['completed'],'stop':r['stop_reason'],'diagnostic_passed':r['passed'],
            'failures':r['failures'],'ground_peak_m':r['maximum_ground_penetration_m'],
            'internal_peak_m':r['maximum_internal_penetration_m'],'internal_load_peak_n':r['maximum_internal_load_n']})
    output={'cases':summary,'numerical_screens':numerical,'intervention_effects':interventions,
        'numerical_screen_pass_count':sum(r['numerical_screen_passed'] for r in numerical),
        'all_case_diagnostic_pass_count':sum(c['diagnostic_passed'] for c in review['checks'].values()),
        'walking_accepted':False,'physical_acceptance':False,
        'boundary':'Only force-input age is intervened on within each integration rate. Common-prefix screens do not establish calibrated physics or closed-loop policy success.'}
    (BASE/'feedback-comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
