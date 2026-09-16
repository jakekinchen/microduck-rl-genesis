"""Accept only the fixed V48 standing final with original V21 walking."""
import json
from pathlib import Path
from scripts.evaluate_laser import digest
ROOT=Path(__file__).resolve().parents[2]
RUN='standing-retention-native-20260908-v48'
WALK_RUN='walking-20260906-v21'
STAND_RUN=RUN+'-standing'


def candidate_sha():
    folder=ROOT/'logs'/RUN
    record=json.loads((folder/'run.json').read_text())
    frozen=json.loads((ROOT/'experiments/walking/native-standing-retention-freeze-v48.json').read_text())
    if (record['status']!='completed' or record['variant']!='native-standing-retention-v48'
        or record['checkpoint']!='model_499.pt' or record['new_transitions']!=576000
        or record['args']['num_envs']!=48 or record['args']['iterations']!=500
        or record['source_sha256']!=frozen['source_sha256']
        or record['warm_start']!=frozen['warm_start']):
        raise ValueError('exact bounded V48 FINAL required')
    for name,sha in record['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('candidate source drift: '+name)
    if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:raise ValueError('joint final drift')
    result=[]
    for role,run in [('walking',WALK_RUN),('standing',STAND_RUN)]:
        component=json.loads((ROOT/'logs'/run/'run.json').read_text())
        if role=='standing' and (component['joint_checkpoint_sha256']!=record['checkpoint_sha256'] or component['variant']!='native-standing-retention-standing-v48'):
            raise ValueError('component lineage drift')
        sha=component['checkpoint_sha256']
        if role=='walking' and sha!=record['warm_start']['walking']:raise ValueError('original walker required')
        if digest(ROOT/'logs'/run/component['checkpoint'])!=sha:raise ValueError('component artifact drift')
        result.append(sha)
    return tuple(result)
