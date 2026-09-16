"""Fixed identities and safe new-data placement for the V55 yaw comparison."""
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VOLUME = Path('/Volumes/cerebro-old')
EXTERNAL = VOLUME/'CodexOffload/MicroDuck/20260912-yaw-v55'
VOLUME_UUID = 'ABDDF5AF-D90F-4F8C-9A5B-4056ECEF58B4'
FREEZE = ROOT/'experiments/walking/yaw-freeze-v55.json'
REPLAY = ROOT/'experiments/walking/recipe-replay-v54'
SEED = 26091255
PARENTS = {'walking': 'walking-20260906-v21', 'standing': 'standing-20260906-v15'}
RECIPES = ('control', 'yaw6')
WEIGHTS = {'control': 3., 'yaw6': 6.}
INITIAL_RUN = 'recipe-native-20260909-v54-shared'
INITIAL_SHA = '9a3e57d975c080f72541eabcd2bcccc4f5a573b98ff299969befef684b5b7f26'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def storage_ready():
    if not VOLUME.is_mount():
        raise ValueError('expected external volume is not mounted')
    info = plistlib.loads(subprocess.check_output(['diskutil','info','-plist',str(VOLUME)]))
    if info.get('VolumeUUID') != VOLUME_UUID:
        raise ValueError('external volume UUID mismatch')
    if shutil.disk_usage(VOLUME).free < 20_000_000_000:
        raise ValueError('less than 20 GB external free space')
    if shutil.disk_usage(ROOT).free < 3_000_000_000:
        raise ValueError('less than 3 GB internal free space')


def new_output(relative):
    """New artifacts only: create an external directory and a stable repo link."""
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('relative output required')
    storage_ready()
    link, out = ROOT/relative, EXTERNAL/relative
    if link.exists() or link.is_symlink() or out.exists():
        raise FileExistsError(relative)
    out.mkdir(parents=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(out, target_is_directory=True)
    if link.resolve() != out or out.stat().st_dev != VOLUME.stat().st_dev:
        raise ValueError('external output identity mismatch')
    return link


def run_name(recipe, smoke=False):
    if recipe not in RECIPES:
        raise ValueError('unknown recipe')
    return 'yaw-native-20260912-v55-' + recipe + ('-smoke' if smoke else '')


def verify_sources(frozen):
    for name, sha in frozen['source_sha256'].items():
        if digest(ROOT/name) != sha:
            raise ValueError('source drift: ' + name)


def write_manifest(folder):
    folder = Path(folder)
    (folder/'SHA256SUMS').write_text(''.join(
        f'{digest(p)}  {p.relative_to(folder)}\n'
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))


def candidate(recipe):
    if recipe == 'parent':
        from experiments.walking.recipe_v54 import candidate as old_candidate
        return old_candidate('shared')
    run = run_name(recipe)
    folder = ROOT/'logs'/run
    record = json.loads((folder/'run.json').read_text())
    frozen = json.loads(FREEZE.read_text())
    verify_sources(frozen)
    if (record['status'] != 'completed' or record['recipe'] != recipe
            or record['checkpoint'] != 'model_2249.pt'
            or record['new_transitions'] != 2_592_000
            or record['source_sha256'] != frozen['source_sha256']):
        raise ValueError('exact bounded V55 final required')
    if digest(folder/record['checkpoint']) != record['checkpoint_sha256']:
        raise ValueError('joint checkpoint drift')
    hashes = []
    for role in PARENTS:
        part = ROOT/'logs'/(run+'-'+role)
        meta = json.loads((part/'run.json').read_text())
        if meta['joint_checkpoint_sha256'] != record['checkpoint_sha256']:
            raise ValueError('component lineage drift')
        if digest(part/meta['checkpoint']) != meta['checkpoint_sha256']:
            raise ValueError('component checkpoint drift')
        hashes.append(meta['checkpoint_sha256'])
    return run+'-walking', run+'-standing', tuple(hashes)
