"""Resolve only the preregistered native standing FINAL for evaluation."""
import json
from pathlib import Path
from scripts.evaluate_laser import digest
ROOT=Path(__file__).resolve().parents[2]
RUN='standing-native-20260906-v41'


def candidate_sha():
    folder=ROOT/'logs'/RUN;record=json.loads((folder/'run.json').read_text())
    frozen=json.loads((ROOT/'experiments/walking/native-standing-freeze-v41.json').read_text())
    if (record['status']!='completed' or record['variant']!='native-standing-v41'
        or record['checkpoint']!='model_249.pt' or record['new_transitions']!=384000
        or record['args']['num_envs']!=64 or record['args']['iterations']!=250
        or record['source_sha256']!=frozen['source_sha256'] or record['warm_start']['sha256']!=frozen['parent_sha256']):
        raise ValueError('exact bounded native standing FINAL required')
    for name,sha in record['source_sha256'].items():
        if digest(ROOT/name)!=sha:raise ValueError('candidate source drift')
    if digest(folder/record['checkpoint'])!=record['checkpoint_sha256']:raise ValueError('candidate artifact drift')
    return record['checkpoint_sha256']
