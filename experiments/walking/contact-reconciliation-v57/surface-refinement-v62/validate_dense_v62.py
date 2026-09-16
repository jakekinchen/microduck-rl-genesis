"""Additive all-face checks with unused barycentrics and analytic witnesses.

This evaluator imports no generator or simulator and does not replace V59.
Distance queries use millimetres internally; all evidence is returned in metres.
The independent witness calculation searches every original triangle using
plane projections and clamped edge segments, without Trimesh proximity code.
"""
from pathlib import Path
import hashlib
import itertools
import json
import signal
import sys
import time
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'proxy-diagnostics-v59'))
from material_validation import _source_mesh


def analytic_nearest(triangles, point):
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    normal = np.cross(b-a, c-a)
    length = np.linalg.norm(normal, axis=1)
    if np.any(length <= 0):
        raise ValueError('degenerate source triangle')
    normal /= length[:, None]
    projection = point - (np.einsum('ij,ij->i', point-a, normal)[:, None] * normal)
    inside = np.ones(len(triangles), dtype=bool)
    for start, end in ((a, b), (b, c), (c, a)):
        inside &= np.einsum('ij,ij->i', np.cross(end-start, projection-start), normal) >= 0
    candidates = [projection]
    distances = [np.where(inside, np.sum((point-projection)**2, axis=1), np.inf)]
    for start, end in ((a, b), (b, c), (c, a)):
        edge = end-start
        t = np.clip(np.einsum('ij,ij->i', point-start, edge) / np.sum(edge**2, axis=1), 0, 1)
        close = start+t[:, None]*edge
        candidates.append(close)
        distances.append(np.sum((point-close)**2, axis=1))
    matrix = np.stack(distances)
    region, triangle = np.unravel_index(np.argmin(matrix), matrix.shape)
    return candidates[region][triangle], float(np.sqrt(matrix[region, triangle])), int(triangle)


def samples(mesh):
    triangles = mesh.triangles
    points = [mesh.vertices, triangles.mean(axis=1)]
    for weights in itertools.permutations((.2, .3, .5)):
        points.append(np.einsum('j,ijk->ik', weights, triangles))
    for i in range(3):
        for fraction in (.25, .75):
            points.append((1-fraction)*triangles[:, i]+fraction*triangles[:, (i+1)%3])
    return np.vstack(points)


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    bank_path = Path(sys.argv[1])
    bank = json.loads(bank_path.read_text())
    for path, digest in bank['input_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'input changed: {path}')
    out = ROOT/bank['output']
    if out.exists():
        raise RuntimeError('dense result already exists')
    report = {'scope': 'additive sampled geometry, not a global bound or physical calibration',
              'bank_sha256': hashlib.sha256(bank_path.read_bytes()).hexdigest(),
              'tolerance_m': .00025, 'analytic_agreement_tolerance_m': 1e-9,
              'meshes': {}, 'all_passed': False, 'physics_steps': 0, 'model_admitted': False}
    start = time.monotonic()
    for name, spec in bank['meshes'].items():
        record = {'passed': False}
        report['meshes'][name] = record
        try:
            source = _source_mesh((ROOT/spec['source_stl']).read_bytes())
            source_mm = source.copy()
            source_mm.apply_scale(1000.0)
            meta = json.loads((ROOT/spec['complete_json']).read_text())
            archive = ROOT/spec['parts_npz']
            if hashlib.sha256(archive.read_bytes()).hexdigest() != meta['parts_sha256']:
                raise RuntimeError('archive metadata mismatch')
            worst, count, violations = [], 0, 0
            with np.load(archive, allow_pickle=False) as arrays:
                for i in range(meta['parts']):
                    mesh = trimesh.Trimesh(arrays[f'v{i:03}'], arrays[f'f{i:03}'], process=False)
                    points = samples(mesh)
                    distances = np.zeros(len(points))
                    for begin in range(0, len(points), 512):
                        batch = points[begin:begin+512]*1000.0
                        outside = ~source_mm.contains(batch)
                        if outside.any():
                            distances[begin+np.flatnonzero(outside)] = trimesh.proximity.closest_point(source_mm, batch[outside])[1]/1000.0
                    if not np.isfinite(distances).all():
                        raise RuntimeError('nonfinite distances')
                    count += len(points)
                    violations += int(np.sum(distances > .00025))
                    worst.extend({'part': i, 'point_m': points[k].tolist(), 'distance_m': float(distances[k])}
                                 for k in np.argsort(distances)[-20:])
                    worst = sorted(worst, key=lambda x: x['distance_m'], reverse=True)[:20]
            for witness in worst:
                close, distance, triangle = analytic_nearest(source_mm.triangles, np.array(witness['point_m'])*1000.0)
                witness.update(analytic_distance_m=distance/1000.0, analytic_point_m=(close/1000.0).tolist(),
                               analytic_triangle=triangle,
                               analytic_agrees=abs(distance/1000.0-witness['distance_m']) <= 1e-9)
            record.update(parts=meta['parts'], samples=count, violations=violations,
                          maximum_excess_m=worst[0]['distance_m'], witnesses=worst,
                          analytic_witnesses_agree=all(w['analytic_agrees'] for w in worst))
            record['passed'] = violations == 0 and record['analytic_witnesses_agree']
        except Exception as error:
            record['error'] = repr(error)
        (out.parent/(out.stem+'-progress.json')).write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        print(json.dumps({'mesh': name, **{k:v for k,v in record.items() if k != 'witnesses'}}), flush=True)
    report['all_passed'] = bool(report['meshes']) and all(r['passed'] for r in report['meshes'].values())
    report['elapsed_seconds'] = time.monotonic()-start
    out.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
