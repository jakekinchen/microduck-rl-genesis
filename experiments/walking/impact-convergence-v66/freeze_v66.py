"""Single-use source/case freeze, preserving the V65 closed artifact set."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import plistlib
import shutil
import subprocess
import mujoco
from impact_v66 import ADVANCE,DT

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')


def main():
    assert not (BASE/'bank.json').exists()
    old=BASE.parent/'feedback-contact-v65';closure=load(old/'closure.json')
    for name,digest in closure['artifact_sha256'].items():assert sha(old/name)==digest,name
    bank=load(old/'bench-bank.json');inputs=dict(bank['input_sha256'])
    for name,digest in inputs.items():assert sha(ROOT/name)==digest,name
    additions=list(BASE.glob('*.py'))+[BASE/'PROTOCOL.md',old/'bench-bank.json',old/'closure.json',old/'bench-review.json',old/'compare_bench_v65.py',old/'bench_v65.py']
    for model in bank['models']:
        for repeat in (1,2):
            path=old/'runs'/f'bench-{model}-dt625us-r{repeat}'
            additions += [path/name for name in ('dynamics.npz','physics.jsonl.gz','configuration.json','result.json')]
    for p in additions:inputs[str(p.relative_to(ROOT))]=sha(p)
    disk=plistlib.loads(subprocess.check_output(['diskutil','info','-plist','/Volumes/cerebro-old']))
    assert disk['VolumeUUID']=='ABDDF5AF-D90F-4F8C-9A5B-4056ECEF58B4'
    free=shutil.disk_usage('/Volumes/cerebro-old').free;assert free>10*2**30
    bulk=Path('/Volumes/cerebro-old/CodexOffload/MicroDuck/20260916-impact-v66')
    bulk.mkdir(exist_ok=False);(BASE/'runs').symlink_to(bulk,target_is_directory=True)
    cases=[]
    for model in bank['models']:
        for phase,tau in enumerate(ADVANCE):
            for dt in DT:
                for repeat in (1,2):
                    cases.append({'id':f'{model}-p{phase}-dt{round(dt*1e9)}ns-r{repeat}',
                        'model':model,'dt_s':dt,'repeat':repeat,'duration_s':1.,'start_advance_s':tau,
                        'phase_bucket':phase,'phase':'controls' if phase==0 and dt==DT[0] else 'main'})
    bank.update(id='v66-guided-impact-phase-convergence',frozen_utc=datetime.now(timezone.utc).isoformat(),
        output_root=str((BASE/'runs').relative_to(ROOT)),v65_root=str(old.relative_to(ROOT)),
        cases=cases,input_sha256=inputs,mujoco_version=mujoco.__version__,
        decision='PROTOCOL.md: every finest model/phase bucket, every case diagnostic and analytic audit required; no full-robot admission.')
    save(BASE/'bank.json',bank)
    coord='experiments/walking/contact-reconciliation-v57/proxy-diagnostics-v59/run_geometry_v59.py'
    for phase in ('controls','main'):
        plan={'input_sha256':{str((BASE/'bank.json').relative_to(ROOT)):sha(BASE/'bank.json'),coord:sha(ROOT/coord)},
            'attempt_marker':phase+'-attempt.json','process_report':phase+'-processes.json',
            'steps':[{'id':c['id'],'script':str((BASE/'probe_impact_v66.py').relative_to(ROOT)),
                'args':[str((BASE/'bank.json').relative_to(ROOT)),c['id']],
                'wall_seconds':60,'log':c['id']+'.log'} for c in cases if c['phase']==phase]}
        save(BASE/(phase+'-plan.json'),plan)
    save(BASE/'storage.json',{'volume_uuid':disk['VolumeUUID'],'bulk':str(bulk),'free_bytes_at_freeze':free})
    save(BASE/'prior-closure-review.json',{'verified':True,'v65_artifacts':closure['artifact_count'],
        'v65_closure_sha256':sha(old/'closure.json'),'boundary':'Prior V65 artifacts, including its prior V62–V64 closure audit, preserved.'})
    print(json.dumps({'cases_frozen':len(cases),'inputs':len(inputs),'bank_sha256':sha(BASE/'bank.json')}))


if __name__=='__main__':main()
