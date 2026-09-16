"""Accept only the fixed V44 final and its two derived component artifacts."""
import json
from pathlib import Path
from scripts.evaluate_laser import digest
ROOT=Path(__file__).resolve().parents[2]
RUN='retention-native-20260907-v46'
WALK_RUN=RUN+'-walking'
STAND_RUN='standing-20260906-v15'


def candidate_sha():
    folder=ROOT/'logs'/RUN
    record=json.loads((folder/'run.json').read_text())
    frozen=json.loads((ROOT/'experiments/walking/native-retention-freeze-v46.json').read_text())
    if (record['status']!='completed' or record['variant']!='native-retention-v46'
        or record['checkpoint']!='model_249.pt' or record['new_transitions']!=360000
        or record['args']['num_envs']!=60 or record['args']['iterations']!=250
        or record['source_sha256']!=frozen['source_sha256']
        or record['warm_start']!=frozen['warm_start']):
        raise ValueError('exact bounded V44 FINAL required')
    for name,sha in record['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('candidate source drift: '+name)
    if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:raise ValueError('joint final drift')
    result=[]
    for role,run in [('walking',WALK_RUN),('standing',STAND_RUN)]:
        component=json.loads((ROOT/'logs'/run/'run.json').read_text())
        if role=='walking' and (component['joint_checkpoint_sha256']!=record['checkpoint_sha256'] or component['variant']!='native-retention-walking-v46'):
            raise ValueError('component lineage drift')
        sha=component['checkpoint_sha256']
        if role=='standing' and sha!=record['warm_start']['standing']:raise ValueError('original stander required')
        if digest(ROOT/'logs'/run/component['checkpoint'])!=sha:raise ValueError('component artifact drift')
        result.append(sha)
    return tuple(result)
