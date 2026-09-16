"""One frozen local CoACD pilot on the difficult shell region; no model admission."""
from pathlib import Path
import hashlib
import json
import signal
import sys
import time
import numpy as np
import trimesh
import coacd
from scipy.spatial import ConvexHull
from cad_refinement_v62r2 import to_manifold, from_manifold, make_hull, face_samples, excess_distances, refine

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'proxy-diagnostics-v59'))
from material_validation import _source_mesh, union_inside


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    bank = json.loads(Path(sys.argv[1]).read_text())
    for path, digest in bank['input_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    source = _source_mesh((ROOT/bank['source_stl']).read_bytes())
    with np.load(ROOT/bank['parent_parts_npz'], allow_pickle=False) as a:
        i = bank['parent']
        parent = trimesh.Trimesh(a[f'v{i:03}'], a[f'f{i:03}'], process=False)
    clip = from_manifold(to_manifold(source)^to_manifold(parent))
    if not clip.is_watertight or not clip.is_winding_consistent:
        raise RuntimeError('clipped source is not a closed oriented mesh')
    out = ROOT/bank['output_directory']
    out.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(out/'clipped-source.npz', vertices=clip.vertices, faces=clip.faces)
    start = time.monotonic()
    with np.load(ROOT/bank['initial_parts_npz'], allow_pickle=False) as initial:
        original_parts = [trimesh.Trimesh(initial[f'v{i:03}'], initial[f'f{i:03}'], process=False) for i in range(len(initial.files)//2)]
    parts, records = refine(source, original_parts, bank['refinement_config'])
    (out/'refinement.json').write_text(json.dumps(records, indent=2)+'\n')
    elapsed = time.monotonic()-start
    arrays = {f'{key}{i:03}': np.asarray(getattr(part, attr)) for i, part in enumerate(parts)
              for key, attr in [('v', 'vertices'), ('f', 'faces')]}
    np.savez_compressed(out/'parts.npz', **arrays)
    scaled = trimesh.Trimesh(source.vertices*1000., source.faces, process=False)
    errors = [float(excess_distances(source, face_samples(part), scaled).max()) for part in parts]
    clip_points = np.vstack([clip.vertices, clip.triangles_center])
    missing = ~union_inside(clip_points, [ConvexHull(p.vertices) for p in parts])
    distances = np.full(int(missing.sum()), np.inf)
    for part in parts:
        mm = trimesh.Trimesh(part.vertices*1000., part.faces, process=False)
        if len(distances):
            distances = np.minimum(distances, trimesh.proximity.closest_point(mm, clip_points[missing]*1000.)[1]/1000.)
    maximum_missing = float(distances.max()) if len(distances) else 0.
    result = {'parent': bank['parent'], 'parts': len(parts), 'generation_seconds': elapsed,
              'dense_excess_m': max(errors), 'clipped_source_samples': len(clip_points),
              'maximum_sampled_missing_m': maximum_missing,
              'clipped_source_watertight': bool(clip.is_watertight),
              'all_parts_convex_watertight': all(p.is_convex and p.is_watertight for p in parts),
              'parts_sha256': hashlib.sha256((out/'parts.npz').read_bytes()).hexdigest(),
              'pilot_passed': max(errors) <= .00018 and maximum_missing <= .00025,
              'scope': 'one exposed region; independent whole-mesh and assembly checks still required',
              'model_admitted': False, 'physics_steps': 0}
    (out/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
