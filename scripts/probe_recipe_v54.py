"""All V54 cells/layouts: exact insertion and repeated full-state replay."""
import json
from pathlib import Path
import sys
import hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recipe_v54 import new_output,write_manifest,FREEZE,digest
from scripts.train_recipe_v54 import require_freeze
from microduck.native_sequence_env_v54 import (
    make_templates, reset_controllers, preview, AssignedAction, request_at, BUCKETS, LAYOUTS)
from microduck.native_standing_env_v42 import clone_world,restore


def main():
    require_freeze()
    out=new_output('receipts/walking/20260909-v54-conformance')
    templates=make_templates(out)
    reports=[]
    for bucket,(original,home) in enumerate(templates):
        expected=BUCKETS[bucket]
        assert original.motor_ticks==expected[3] and original.sensor_ticks==expected[4]
        floor=original.core.model.geom('floor').id
        angle=np.deg2rad(expected[1])/2
        np.testing.assert_allclose(original.core.model.geom_quat[floor],
            [np.cos(angle),0,np.sin(angle),0],rtol=0,atol=1e-12)
        assert original.core.model.geom_contype[floor]&1 and original.core.model.geom_conaffinity[floor]&1
        candidate=clone_world(original);adapter=AssignedAction()
        candidate.walking_policy=candidate.standing_policy=adapter
        for level,(width,stop,windows) in enumerate(LAYOUTS):
            repeats=[]
            for repeat in range(2):
                for world in (original,candidate): restore(world,home);reset_controllers(world)
                hashes={key:hashlib.sha256() for key in ['observation','action','physical']}
                for step in range(width*windows):
                    requested=request_at(step,bucket,0,level)
                    predicted=preview(candidate,requested)
                    row=original.step_command(requested)
                    adapter.expected,adapter.action,adapter.calls=predicted,original.last_action.copy(),0
                    candidate.step_command(requested)
                    assert adapter.calls==1
                    for field in ('last_observation','last_action'):
                        assert getattr(original,field).tobytes()==getattr(candidate,field).tobytes(),field
                    for field in ('qpos','qvel','ctrl','qfrc_constraint','qfrc_actuator','efc_force'):
                        left,right=getattr(original.core.data,field),getattr(candidate.core.data,field)
                        assert left.tobytes()==right.tobytes(),field
                        hashes['physical'].update(left.tobytes())
                    hashes['observation'].update(original.last_observation.tobytes())
                    hashes['action'].update(original.last_action.tobytes())
                    if row['fell']: break
                repeats.append(dict(controls=step+1,fell=bool(original.fell),
                    **{key+'_sha256':h.hexdigest() for key,h in hashes.items()}))
            assert repeats[0]==repeats[1], 'non-accumulating reset replay mismatch'
            reports.append(dict(bucket=bucket,level=level,planned_controls=width*windows,
                repeats=repeats,exact_observation_action_bytes=True,exact_physical_continuation=True,
                materialized_terrain=original.materialized_terrain,
                materialized_domain=original.materialized_domain,
                motor_ticks=original.motor_ticks,sensor_ticks=original.sensor_ticks))
            print(json.dumps(dict(bucket=bucket,level=level,controls=repeats[0]['controls'],fell=repeats[0]['fell'])),flush=True)
        candidate.close();original.close()
    require_freeze()
    assert len(reports)==72
    (out/'probe.json').write_text(json.dumps(dict(complete=True,passed=True,
        freeze_sha256=digest(FREEZE),reports=reports,
        boundary='Dynamics/input/reset conformance; original falls retained, not behavior acceptance.'),indent=2)+'\n')
    write_manifest(out)


if __name__=='__main__': main()
