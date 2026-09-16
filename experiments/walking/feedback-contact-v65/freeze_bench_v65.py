"""Compile and audit matched assets without integrating, then freeze drop cases."""
from datetime import datetime,timezone
import json
import signal
from bench_v65 import BASE,ROOT,build_static,load,save,sha


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
    assert not (BASE/'bench-bank.json').exists()
    b=load(BASE/'feedback-bank.json')
    for name,digest in b['input_sha256'].items():assert sha(ROOT/name)==digest,name
    out=BASE/'bench-models';out.mkdir(exist_ok=False)
    static=build_static(b,out)
    save(BASE/'bench-static.json',static)
    assert static['static_passed']
    inputs=dict(b['input_sha256'])
    additions=list(BASE.glob('*bench*.py'))+[BASE/'bench-static.json',BASE/'feedback-bank.json']+list(out.glob('*.xml'))
    for path in additions:inputs[str(path.relative_to(ROOT))]=sha(path)
    for check in static['models'].values():
        # Assets are already bound transitively, but record an explicit binding too.
        path=ROOT/check['asset'];inputs[str(path.relative_to(ROOT))]=sha(path)
    cases=[]
    for model in static['models']:
        for dt in (.005,.0025,.00125,.000625):
            for repeat in (1,2):
                cases.append({'id':f'bench-{model}-dt{round(dt*1e6)}us-r{repeat}',
                    'model':model,'dt_s':dt,'repeat':repeat,'duration_s':1.})
    bank={'id':'v65-matched-guided-sole-drop','frozen_utc':datetime.now(timezone.utc).isoformat(),
        'output_root':b['output_root'],'cases':cases,'input_sha256':inputs,
        'models':{name:{'xml':str((out/(name+'.xml')).relative_to(ROOT)),'static':check} for name,check in static['models'].items()},
        'numerical_screen':{'position_max_m':.0001,'penetration_peak_delta_m':.0001,
            'impulse_fraction_mgT':.02,'first_impact_delta_s':.00125},
        'decision':'PROTOCOL.md; isolated numerical diagnostic, no calibrated physical or behavior claim'}
    save(BASE/'bench-bank.json',bank)
    coord='experiments/walking/contact-reconciliation-v57/proxy-diagnostics-v59/run_geometry_v59.py'
    plan={'input_sha256':{str((BASE/'bench-bank.json').relative_to(ROOT)):sha(BASE/'bench-bank.json'),coord:sha(ROOT/coord)},
        'attempt_marker':'bench-attempt.json','process_report':'bench-processes.json','steps':[
            {'id':c['id'],'script':str((BASE/'probe_bench_v65.py').relative_to(ROOT)),
             'args':[str((BASE/'bench-bank.json').relative_to(ROOT)),c['id']],
             'wall_seconds':60,'log':c['id']+'.log'} for c in cases]}
    save(BASE/'bench-plan.json',plan)
    print(json.dumps({'static_passed':True,'cases_frozen':len(cases),'input_files':len(inputs)}),flush=True)


if __name__=='__main__':main()
