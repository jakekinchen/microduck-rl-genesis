"""Post-run numerical comparisons; no simulator or policy execution."""
from pathlib import Path
import json
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def load(p):return json.loads(p.read_text())


def main():
    bank=load(BASE/'bank-r2.json');reports={};arrays={};summaries={}
    for c in bank['cases']:
        p=ROOT/bank['output_root']/c['id'];r=load(p/'result.json');assert 'error' not in r
        reports[c['id']]=r
        with np.load(p/'dynamics.npz') as a:arrays[c['id']]={n:a[n] for n in a.files}
        summaries[c['id']]={k:r[k] for k in ('passed','failures','completed','observed_physics_steps','first_fall_s',
             'maximum_ground_penetration_m','maximum_internal_penetration_m','maximum_internal_load_n',
             'maximum_nonsole_ground_load_n','minimum_joint_margin_rad','stop_reason','performance')}
    def case(model,mode,dt,intervention='none',repeat=1):
        return next(c for c in bank['cases'] if (c['model'],c['mode'],c['dt_s'],c['intervention'],c['repeat'])==(model,mode,dt,intervention,repeat))
    def compare(a,b):
        aa,bb=arrays[a['id']],arrays[b['id']]
        stride=round(a['dt_s']/b['dt_s']);assert stride>=1
        qa=aa['qpos'];qb=bb['qpos'][stride-1::stride];n=min(len(qa),len(qb))
        delta=qa[:n]-qb[:n]
        ra,rb=reports[a['id']],reports[b['id']]
        root=np.linalg.norm(delta[:,:3],axis=1);joints=np.max(np.abs(delta[:,7:]),axis=1)
        return {'common_steps':n,'common_duration_s':n*a['dt_s'],'root_max_m':float(root.max()),
                'joint_max_rad':float(joints.max()),
                'root_rms_m':float(np.sqrt(np.mean(root**2))),
                'first_root_over_1mm_s':float((np.flatnonzero(root>.001)[0]+1)*a['dt_s']) if (root>.001).any() else None,
                'ground_peak_delta_m':abs(ra['maximum_ground_penetration_m']-rb['maximum_ground_penetration_m']),
                'internal_peak_delta_m':abs(ra['maximum_internal_penetration_m']-rb['maximum_internal_penetration_m']),
                'terminal_time_delta_s':abs(ra['observed_physics_steps']*a['dt_s']-rb['observed_physics_steps']*b['dt_s']),
                'same_terminal_category':ra['stop_reason']==rb['stop_reason'],
                'both_full_duration':ra['completed'] and rb['completed']}
    convergence={}
    for model in ('v11','v62'):
        for mode in ('replay','passive'):
            coarse,middle,fine=[case(model,mode,dt) for dt in (.005,.0025,.00125)]
            one,two=compare(coarse,middle),compare(middle,fine)
            failures=[k for k,limit in bank['convergence_screen'].items() if k!='same_terminal_category_required' and two[k]>limit+1e-12]
            if not two['same_terminal_category']:failures.append('terminal_category')
            convergence[model+'-'+mode]={'coarse_to_middle':one,'middle_to_fine':two,
                'finest_agreement_screen_passed':not failures,'failed_components':failures}
    counterfactuals={};native=case('v62','replay',.005)
    review=load(BASE/'all-review-r2.json')
    first_contact=review['checks'][native['id']]['first_shell_contact_s']
    for kind in ('match_v11_export','mask_shell_floor'):
        c=case('v62','replay',.005,kind);cmp=compare(native,c)
        cmp['materially_visible_effect']=bool(cmp['root_max_m']>.001 or cmp['joint_max_rad']>np.deg2rad(1.) or not cmp['same_terminal_category'] or cmp['terminal_time_delta_s']>.02)
        if kind=='mask_shell_floor':
            n=round(first_contact/.005)-1
            differences={name:float(np.max(np.abs(arrays[native['id']][name][:n]-arrays[c['id']][name][:n]))) for name in ('qpos','qvel','ctrl','target')}
            cmp['before_first_original_shell_contact_max_errors']=differences
            cmp['unaffected_prefix_verified']=all(v<=1e-10 for v in differences.values())
        counterfactuals[kind]=cmp
    physical={}
    with np.load(ROOT/bank['output_root']/case('v11','replay',.005)['id']/'physical-parameters.npz') as ref:
        for c in bank['cases']:
            if c['intervention']=='match_v11_export':
                with np.load(ROOT/bank['output_root']/c['id']/'physical-parameters.npz') as candidate:
                    assert candidate.files==ref.files
                    for name in ref.files:np.testing.assert_array_equal(ref[name],candidate[name])
                    physical[c['id']]={'arrays_exact':len(ref.files)}
    result={'status':'completed_diagnostics','cases':summaries,'diagnostic_passes':sum(r['passed'] for r in reports.values()),
            'counterfactuals':counterfactuals,'convergence':convergence,'matched_export_physical_arrays':physical,
            'model_admitted':False,'walking_accepted':False,'physical_acceptance':False,
            'boundary':'Exposed deterministic model diagnostics, with quarantined premature isolation attempts excluded. No closed-loop policy score, measured calibration or terrain acceptance.'}
    (BASE/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
