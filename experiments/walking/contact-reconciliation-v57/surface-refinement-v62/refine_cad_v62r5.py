"""One source-bound local CAD refinement; coordinator owns the deadline."""
from pathlib import Path
import hashlib
import json
import signal
import sys
import time

signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
import numpy as np
import trimesh
from cad_refinement_v62r5 import refine

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'proxy-diagnostics-v59'))
from material_validation import _source_mesh


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = Path(sys.argv[1]).resolve()
    protocol = json.loads(protocol_path.read_text())
    name = sys.argv[2]
    spec = protocol['meshes'][name]
    for path, expected in protocol['input_sha256'].items():
        if digest(ROOT / path) != expected:
            raise RuntimeError(f'input changed: {path}')
    np.random.seed(protocol['seed'])
    source_path = ROOT / spec['source_stl']
    source = _source_mesh(source_path.read_bytes())
    if not source.is_watertight or not source.is_winding_consistent:
        raise RuntimeError('source is not an oriented closed solid')
    old_meta = json.loads((ROOT / spec['complete_json']).read_text())
    archive = ROOT / spec['parts_npz']
    if old_meta['parts_sha256'] != digest(archive):
        raise RuntimeError('parent metadata mismatch')
    with np.load(archive, allow_pickle=False) as arrays:
        parts = [trimesh.Trimesh(arrays[f'v{i:03}'], arrays[f'f{i:03}'], process=False)
                 for i in range(old_meta['parts'])]
    out = ROOT / spec['output_directory']
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()

    def progress(records):
        receipt = {'mesh': name, 'elapsed_seconds': time.monotonic()-start,
                   'completed_parents': len(records), 'parents': records}
        (out / 'progress.json').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        if len(records) % 16 == 0 or records[-1]['decision'] != 'unchanged':
            print(json.dumps({'mesh': name, 'parents': len(records),
                              'last_decision': records[-1]['decision'],
                              'output_parts': sum(x['output_count'] for x in records),
                              'seconds': time.monotonic()-start}), flush=True)

    config = protocol['config'] | {'seed_parent_indices': spec.get('seed_parent_indices', [])}
    refined, records = refine(source, parts, config, progress)
    arrays = {}
    for i, part in enumerate(refined):
        arrays[f'v{i:03}'] = np.asarray(part.vertices)
        arrays[f'f{i:03}'] = np.asarray(part.faces)
    with (out / 'parts.npz').open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    complete = {'mesh': name, 'parts': len(refined),
                'part_vertices': [len(p.vertices) for p in refined],
                'part_faces': [len(p.faces) for p in refined],
                'native_seconds': time.monotonic()-start,
                'parts_sha256': digest(out / 'parts.npz'),
                'source_sha256': digest(source_path),
                'parent_parts_sha256': digest(archive),
                'protocol_sha256': digest(protocol_path),
                'config': config, 'material_acceptance': 'requires independent evaluation',
                'physics_executed': False, 'model_admitted': False}
    (out / 'complete.json').write_text(json.dumps(complete, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in complete.items() if k not in {'part_vertices', 'part_faces'}}), flush=True)


if __name__ == '__main__':
    main()
