"""Preregistered guided-drop timestep and cross-asset comparisons."""
from pathlib import Path
import json
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
def load(p):return json.loads(p.read_text())


def compare(a,b,bank):
    root=ROOT/bank['output_root'];ra=load(root/a['id']/'result.json');rb=load(root/b['id']/'result.json')
    dt=max(a['dt_s'],b['dt_s']);sa=round(dt/a['dt_s']);sb=round(dt/b['dt_s'])
    with np.load(root/a['id']/'dynamics.npz') as x,np.load(root/b['id']/'dynamics.npz') as y:
        qa=x['position_m'][sa-1::sa];qb=y['position_m'][sb-1::sb]
        assert len(qa)==len(qb)==round(1./dt)
        delta=float(np.max(np.abs(qa-qb)))
    mass=bank['models'][a['model']]['static']['mass_kg']
    r={'a':a['id'],'b':b['id'],'position_max_m':delta,
        'penetration_peak_delta_m':abs(ra['peak_penetration_m']-rb['peak_penetration_m']),
        'impulse_fraction_mgT':abs(ra['normal_impulse_ns']-rb['normal_impulse_ns'])/(mass*9.81),
        'first_impact_delta_s':abs(ra['first_loaded_impact_s']-rb['first_loaded_impact_s'])}
    r['failures']=[key for key,limit in bank['numerical_screen'].items() if r[key]>limit+1e-14]
    r['numerical_screen_passed']=not r['failures'];return r


def main():
    b=load(BASE/'bench-bank.json');review=load(BASE/'bench-review.json')
    assert review['verification_passed'] and review['cases_verified']==32
    def case(m,dt):return next(c for c in b['cases'] if c['model']==m and c['dt_s']==dt and c['repeat']==1)
    screens=[];cross=[];summary=[]
    for m in b['models']:
        for a,z in ((.005,.0025),(.0025,.00125),(.00125,.000625)):
            r=compare(case(m,a),case(m,z),b);r['finest_pair']=z==.000625;screens.append(r)
    for foot in ('left','right'):
        for dt in (.005,.0025,.00125,.000625):cross.append(compare(case('v11-'+foot,dt),case('v62-'+foot,dt),b))
    for c in b['cases']:
        if c['repeat']==1:
            r=load(ROOT/b['output_root']/c['id']/'result.json')
            summary.append({k:v for k,v in r.items() if k!='elapsed_seconds'})
    output={'cases':summary,'numerical_screens':screens,'cross_asset_screens':cross,
        'finest_numerical_pass_count':sum(r['numerical_screen_passed'] for r in screens if r['finest_pair']),
        'all_case_diagnostic_pass_count':sum(c['diagnostic_passed'] for c in review['checks'].values()),
        'walking_accepted':False,'physical_acceptance':False,
        'boundary':'Matched guided CAD ankle drops only; no full-body load, actuator or calibration claim.'}
    (BASE/'bench-comparison.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
