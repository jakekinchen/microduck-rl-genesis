"""Bounded diagnosis of the failed shell parent; produces no candidate archive."""
from pathlib import Path
import hashlib
import json
import signal
import sys
import numpy as np
import trimesh
from cad_refinement_v62r2 import to_manifold, from_manifold, make_hull, face_samples, excess_distances
from validate_dense_v62 import analytic_nearest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'proxy-diagnostics-v59'))
from material_validation import _source_mesh


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    bank = json.loads(Path(sys.argv[1]).read_text())
    for path, digest in bank['input_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
    source = _source_mesh((ROOT/bank['source_stl']).read_bytes())
    source_mm = source.copy()
    source_mm.apply_scale(1000.)
    with np.load(ROOT/bank['parts_npz'], allow_pickle=False) as a:
        i = bank['parent']
        part = trimesh.Trimesh(a[f'v{i:03}'], a[f'f{i:03}'], process=False)
    clip = to_manifold(source)^to_manifold(part)
    pending = [(c, 0) for c in clip.decompose()]
    records, leaves = [], 0
    out = ROOT/bank['output']
    if out.exists():
        raise RuntimeError('diagnostic already exists')
    while pending and len(records) < bank['maximum_nodes']:
        solid, depth = pending.pop(0)
        mesh = from_manifold(solid)
        hull = make_hull(np.asarray(mesh.vertices))
        points = face_samples(hull)
        distances = excess_distances(source, points, source_mm)
        point = points[distances.argmax()]
        _, actual, triangle = analytic_nearest(source_mm.triangles, point*1000.)
        maximum = float(distances.max())
        row = {'depth': depth, 'extents_m': mesh.extents.tolist(), 'maximum_m': maximum,
               'analytic_maximum_witness_m': actual/1000., 'analytic_triangle': triangle,
               'point_m': point.tolist(), 'source_volume_m3': solid.volume()}
        if maximum <= .00012:
            row['decision'] = 'retain'
            leaves += 1
        else:
            axis = int(np.argmax(mesh.extents))
            offset = float(mesh.bounds[:, axis].mean())
            children = solid.split_by_plane(np.eye(3)[axis], offset)
            row.update(decision='split', axis=axis, offset_m=offset)
            pending.extend((c, depth+1) for c in children if not c.is_empty())
        records.append(row)
    result = {'parent': bank['parent'], 'processed_nodes': len(records),
              'retained_leaves': leaves, 'pending_nodes': len(pending), 'records': records,
              'completed': not pending, 'candidate_generated': False, 'physics_steps': 0}
    out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'records'}), flush=True)


if __name__ == '__main__':
    main()
