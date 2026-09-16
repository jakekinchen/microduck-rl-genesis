"""One-time freeze; uses the existing bounded coordinator and verified bulk drive."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import plistlib
import shutil
import subprocess

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')


def main():
    assert not (BASE/'feedback-bank.json').exists()
    mount=Path('/Volumes/cerebro-old')
    disk=plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(mount)]))
    assert disk['VolumeUUID']=='ABDDF5AF-D90F-4F8C-9A5B-4056ECEF58B4'
    free=shutil.disk_usage(mount).free;assert free>10*2**30
    bulk=mount/'CodexOffload/MicroDuck/20260916-feedback-v65';bulk.mkdir(exist_ok=False)
    (BASE/'runs').symlink_to(bulk,target_is_directory=True)
    old=ROOT/'experiments/walking/contact-isolation-v64'
    b=json.loads((old/'bank-r2.json').read_text())
    inputs=dict(b['input_sha256'])
    for rel,expected in inputs.items():assert digest(ROOT/rel)==expected,rel
    additions=[old/'bank-r2.json',old/'closure.json',old/'all-review-r2.json',
        old/'review_v64.py',old/'probe_contact_v64.py',old/'metrics_v64.py',old/'contact_v64.py']
    additions += list(BASE.glob('*.py'))+[BASE/'PROTOCOL.md']
    for model in b['models']:
        for suffix in ('base','dt2500us','dt1250us'):
            for repeat in (1,2):
                path=old/'runs'/f'{model}-replay-{suffix}-r{repeat}'
                additions += [path/f for f in ('initial-state.npz','dynamics.npz','configuration.json','result.json')]
    for path in additions:inputs[str(path.relative_to(ROOT))]=digest(path)
    cases=[]
    for dt in (.005,.0025,.00125):
        for model in b['models']:
            for mode in ('native','fixed_5ms'):
                for repeat in (1,2):
                    cases.append({'id':f'{model}-{mode}-dt{round(dt*1e6)}us-r{repeat}',
                        'model':model,'mode':'replay','feedback':mode,'intervention':'none',
                        'dt_s':dt,'repeat':repeat,'duration_s':18.,'yaw_rad':-.8,
                        'phase':'controls' if dt==.005 else 'native' if mode=='native' else 'fixed'})
    b.update(id='v65-force-input-age',frozen_utc=datetime.now(timezone.utc).isoformat(),
        output_root=str((BASE/'runs').relative_to(ROOT)),v64_root=str(old.relative_to(ROOT)),
        cases=cases,input_sha256=inputs,joint_ids=list(range(1,15)),dof_indices=list(range(6,20)))
    for key in ('amendment','amendment_utc','geometry_audit_times_s'):b.pop(key,None)
    b['decision_rule']='PROTOCOL.md; exact controls and native fine-step conformance before fixed-age intervention; all diagnostics remain exposed.'
    save(BASE/'feedback-bank.json',b)
    coordinator='experiments/walking/contact-reconciliation-v57/proxy-diagnostics-v59/run_geometry_v59.py'
    for phase in ('controls','native','fixed'):
        plan={'input_sha256':{str((BASE/'feedback-bank.json').relative_to(ROOT)):digest(BASE/'feedback-bank.json'),
                              coordinator:digest(ROOT/coordinator)},
            'attempt_marker':phase+'-attempt.json','process_report':phase+'-processes.json',
            'steps':[{'id':c['id'],'script':str((BASE/'probe_feedback_v65.py').relative_to(ROOT)),
                'args':[str((BASE/'feedback-bank.json').relative_to(ROOT)),c['id']],
                'wall_seconds':240,'log':c['id']+'.log'} for c in cases if c['phase']==phase]}
        save(BASE/(phase+'-plan.json'),plan)
    save(BASE/'storage.json',{'mount':str(mount),'volume_uuid':disk['VolumeUUID'],
         'available_bytes_at_freeze':free,'bulk':str(bulk),'sources_preserved':True})
    print(json.dumps({'frozen_cases':len(cases),'input_files':len(inputs),'bank_sha256':digest(BASE/'feedback-bank.json')}))


if __name__=='__main__':main()
