"""Exact four-pair intervention matrix for the V44 component diagnosis."""
import json
from pathlib import Path
from scripts.evaluate_laser import digest
from experiments.walking.native_candidate_v44 import candidate_sha, WALK_RUN, STAND_RUN
ROOT=Path(__file__).resolve().parents[2]
OLD_WALK='walking-20260906-v21'
OLD_STAND='standing-20260906-v15'
OLD_SHAS=('7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322',
          'acab8402e262dbb6af5a3fab9b67fa4ce5e34a4d23cadb127fe6dfa475a70e46')
PAIRS={'original':(OLD_WALK,OLD_STAND),'joint-v44':(WALK_RUN,STAND_RUN),
       'new-walker':(WALK_RUN,OLD_STAND),'new-stander':(OLD_WALK,STAND_RUN)}
FLAT_CASES={'nominal-20-20ms--forward-08','zero-lag--forward-08'}


def resolve_pair(name):
    new_shas=candidate_sha()
    runs=PAIRS[name]
    shas=tuple(new_shas[i] if run in (WALK_RUN,STAND_RUN) else OLD_SHAS[i] for i,run in enumerate(runs))
    for run,expected in zip(runs,shas):
        folder=ROOT/'logs'/run;record=json.loads((folder/'run.json').read_text())
        checkpoint=(folder/record['checkpoint']).resolve()
        if record['status']!='completed' or checkpoint.parent!=folder.resolve() or digest(checkpoint)!=expected or record['checkpoint_sha256']!=expected:
            raise ValueError('component identity mismatch: '+run)
    return runs,shas
