"""Unshifted, common-grid, per-phase numerical decisions for the frozen V66 bank."""
from pathlib import Path
import json
import sys
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
sys.path.insert(1,str(BASE.parent/'feedback-contact-v65'))
from compare_bench_v65 import compare


def load(p):return json.loads(p.read_text())


def main():
    b=load(BASE/'bank.json');review=load(BASE/'all-review.json')
    assert review['verification_passed'] and review['cases_verified']==96
    def case(model,phase,dt):
        return next(c for c in b['cases'] if c['model']==model and c['phase_bucket']==phase and c['dt_s']==dt and c['repeat']==1)
    screens=[];cross=[];summaries=[]
    for model in b['models']:
        for phase in range(4):
            for coarse,fine in ((.000625,.0003125),(.0003125,.00015625)):
                r=compare(case(model,phase,coarse),case(model,phase,fine),b)
                r.update(model=model,phase_bucket=phase,finest_pair=fine==.00015625)
                required=[c for c in b['cases'] if c['model']==model and c['phase_bucket']==phase and c['dt_s'] in (coarse,fine)]
                r['all_cases_passed']=all(review['checks'][c['id']]['combined_passed'] for c in required)
                r['bucket_passed']=r['numerical_screen_passed'] and r['all_cases_passed']
                screens.append(r)
    for foot in ('left','right'):
        for phase in range(4):
            for dt in (.000625,.0003125,.00015625):
                cross.append(compare(case('v11-'+foot,phase,dt),case('v62-'+foot,phase,dt),b))
    for c in b['cases']:
        if c['repeat']==1:
            r=load(ROOT/b['output_root']/c['id']/'result.json')
            summaries.append({k:v for k,v in r.items() if k!='elapsed_seconds'})
    finest=[r for r in screens if r['finest_pair']]
    all_cases=all(r['combined_passed'] for r in review['checks'].values())
    gate=all_cases and len(finest)==16 and all(r['bucket_passed'] for r in finest)
    result={'cases':summaries,'numerical_screens':screens,'cross_asset_screens':cross,
        'finest_buckets_passed':sum(r['bucket_passed'] for r in finest),'finest_buckets_required':16,
        'all_case_diagnostic_pass_count':sum(r['diagnostic_passed'] for r in review['checks'].values()),
        'all_case_analytic_pass_count':sum(r['analytic_passed'] for r in review['checks'].values()),
        'guided_bench_numerical_gate_passed':gate,'guided_bench_candidate_reference_dt_s':.00015625 if gate else None,
        'full_robot_reference_accepted':False,'walking_accepted':False,'physical_acceptance':False,
        'boundary':'All frozen phase buckets required; no time-axis alignment. A guided ankle-drop numerical screen does not admit full-robot physics or policy behavior.'}
    (BASE/'comparison.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','numerical_screens','cross_asset_screens')},indent=2))


if __name__=='__main__':main()
