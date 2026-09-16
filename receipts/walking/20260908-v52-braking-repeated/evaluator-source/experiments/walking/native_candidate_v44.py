"""Accept only the fixed V44 final and its two derived component artifacts."""
import json
from pathlib import Path
from scripts.evaluate_laser import digest
ROOT=Path(__file__).resolve().parents[2]
RUN='sequence-native-20260907-v44'
WALK_RUN=RUN+'-walking'
STAND_RUN=RUN+'-standing'


def candidate_sha():
    folder=ROOT/'logs'/RUN
    record=json.loads((folder/'run.json').read_text())
    frozen=json.loads((ROOT/'experiments/walking/native-sequence-freeze-v44.json').read_text())
    if (record['status']!='completed' or record['variant']!='native-sequence-v44'
        or record['checkpoint']!='model_499.pt' or record['new_transitions']!=768000
        or record['args']['num_envs']!=64 or record['args']['iterations']!=500
        or record['source_sha256']!=frozen['source_sha256']
        or record['warm_start']!=frozen['warm_start']):
        raise ValueError('exact bounded V44 FINAL required')
    for name,sha in record['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('candidate source drift: '+name)
    if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:raise ValueError('joint final drift')
    result=[]
    for role,run in [('walking',WALK_RUN),('standing',STAND_RUN)]:
        component=json.loads((ROOT/'logs'/run/'run.json').read_text())
        if component['joint_checkpoint_sha256']!=record['checkpoint_sha256'] or component['variant']!='native-sequence-'+role+'-v44':
            raise ValueError('component lineage drift')
        sha=component['checkpoint_sha256']
        if digest(ROOT/'logs'/run/component['checkpoint'])!=sha:raise ValueError('component artifact drift')
        result.append(sha)
    return tuple(result)
