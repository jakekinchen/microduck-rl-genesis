"""Exact original-policy/controller equivalence and non-accumulating HOME reset."""
import argparse
import copy
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from microduck.native_sequence_env_v44 import make_templates, reset_controllers, preview, AssignedAction, request_at
from microduck.native_standing_env_v42 import clone_world, restore
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    templates=make_templates(a.output)
    reports=[]
    for bucket,(original,home) in enumerate(templates):
        candidate=clone_world(original)
        adapter=AssignedAction()
        candidate.walking_policy=candidate.standing_policy=adapter
        passes=[]
        reference=[]
        for repeat in range(2):
            for w in (original,candidate):
                restore(w,home);reset_controllers(w)
            steps=0
            for step in range(2700):
                requested=request_at(step,bucket,0)
                predicted=preview(candidate,requested)
                row=original.step_command(requested)
                adapter.expected,adapter.action,adapter.calls=predicted,original.last_action.copy(),0
                candidate.step_command(requested)
                if adapter.calls!=1:raise ValueError('policy call count')
                for field in ('last_action','last_observation'):
                    if getattr(original,field).tobytes()!=getattr(candidate,field).tobytes():raise ValueError(field)
                for field in ('qpos','qvel','ctrl','qfrc_constraint','qfrc_actuator','efc_force'):
                    np.testing.assert_array_equal(getattr(original.core.data,field),getattr(candidate.core.data,field))
                if repeat==0:reference.append(original.core.data.qpos.copy())
                else:np.testing.assert_array_equal(reference[step],original.core.data.qpos)
                steps+=1
                if row['fell']:break
            passes.append(steps)
        reports.append(dict(bucket=bucket,controls_per_repeat=passes,exact_observation_action_bytes=True,
            exact_physical_continuation=True,exact_nonaccumulating_full_reset=True,baseline_fell=original.fell))
        candidate.close();original.close()
    (a.output/'probe.json').write_text(json.dumps(dict(complete=True,passed=True,reports=reports),indent=2)+'\n')
    (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.relative_to(a.output)}\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))
    print(json.dumps(reports),flush=True)

if __name__=='__main__':main()
