"""Bounded parallel point queries; preserve frozen samples and tolerances."""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
import multiprocessing
from pathlib import Path
import signal
import sys
import time
import numpy as np
import trimesh
from validate_dense_v62 import analytic_nearest, samples

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'proxy-diagnostics-v59'))
from material_validation import _source_mesh

SOURCE = None
SOURCE_MM = None


def initialize(raw):
    global SOURCE, SOURCE_MM
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    SOURCE = _source_mesh(raw)
    SOURCE_MM = SOURCE.copy()
    SOURCE_MM.apply_scale(1000.)


def score_points(task):
    index, points, scale = task
    source = SOURCE if scale == 1 else SOURCE_MM
    distances = np.zeros(len(points))
    for start in range(0, len(points), 512):
        batch = points[start:start+512]*scale
        outside = ~source.contains(batch)
        if outside.any():
            distances[start+np.flatnonzero(outside)] = trimesh.proximity.closest_point(source, batch[outside])[1]/scale
    if not np.isfinite(distances).all():
        raise RuntimeError('nonfinite point distance')
    return {'part': index, 'samples': len(points), 'violations': int(np.sum(distances > .00025)),
            'witnesses': [{'part': index, 'point_m': points[k].tolist(), 'distance_m': float(distances[k])}
                          for k in np.argsort(distances)[-20:]]}


def winding(triangles, point):
    vectors = triangles-point
    lengths = np.linalg.norm(vectors, axis=2)
    a, b, c = vectors[:, 0], vectors[:, 1], vectors[:, 2]
    numerator = np.einsum('ij,ij->i', a, np.cross(b, c))
    denominator = (np.prod(lengths, axis=1)+np.einsum('ij,ij->i', a, b)*lengths[:, 2]
                   +np.einsum('ij,ij->i', b, c)*lengths[:, 0]+np.einsum('ij,ij->i', c, a)*lengths[:, 1])
    return float(np.arctan2(numerator, denominator).sum()/(2*np.pi))


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    bank_path = Path(sys.argv[1])
    bank = json.loads(bank_path.read_text())
    for path, digest in bank['input_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise RuntimeError('input changed:'+path)
    output = ROOT/bank['output']
    if output.exists():
        raise RuntimeError('output already exists')
    report = {'kind': bank['kind'], 'meshes': {}, 'model_admitted': False, 'physics_steps': 0,
              'bank_sha256': hashlib.sha256(bank_path.read_bytes()).hexdigest(),
              'scope': 'sampled geometry; no global bound or physical calibration',
              'tolerance_m': .00025, 'analytic_agreement_tolerance_m': 1e-9,
              'workers': bank['workers']}
    start = time.monotonic()
    for name, spec in bank['meshes'].items():
        record = {'passed': False}
        report['meshes'][name] = record
        try:
            raw = (ROOT/spec['source_stl']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != bank['input_sha256'][spec['source_stl']]:
                raise RuntimeError('source changed before worker initialization')
            initialize(raw)
            metadata = json.loads((ROOT/spec['complete_json']).read_text())
            if metadata['mesh'] != name or metadata['source_sha256'] != hashlib.sha256(raw).hexdigest():
                raise RuntimeError('source or mesh metadata mismatch')
            if type(metadata['parts']) is not int or not 1 <= metadata['parts'] <= bank['maximum_parts']:
                raise RuntimeError('invalid or over-budget part count')
            raw_archive = (ROOT/spec['parts_npz']).read_bytes()
            if hashlib.sha256(raw_archive).hexdigest() != metadata['parts_sha256']:
                raise RuntimeError('archive metadata mismatch')
            with np.load(io.BytesIO(raw_archive), allow_pickle=False) as archive:
                parts = [trimesh.Trimesh(archive[f'v{i:03}'], archive[f'f{i:03}'], process=False)
                         for i in range(metadata['parts'])]
            if bank['kind'] == 'legacy_excess_localization':
                total_faces = sum(len(p.faces) for p in parts)
                selected = np.unique(np.linspace(0, total_faces-1, min(4096, total_faces), dtype=int))
                points_by_part, face_offset = [], 0
                for part in parts:
                    ids = selected[(selected >= face_offset) & (selected < face_offset+len(part.faces))]-face_offset
                    points_by_part.append(np.vstack([part.vertices, part.triangles_center[ids]]))
                    face_offset += len(part.faces)
                scale = 1.
            elif bank['kind'] == 'additive_dense':
                points_by_part = [samples(part) for part in parts]
                scale = 1000.
            else:
                raise RuntimeError('unknown point bank kind')
            worst, count, violations = [], 0, 0
            tasks = [(i, points, scale) for i, points in enumerate(points_by_part)]
            with ProcessPoolExecutor(max_workers=bank['workers'], mp_context=multiprocessing.get_context('spawn'),
                                     initializer=initialize, initargs=(raw,)) as pool:
                for i, result in enumerate(pool.map(score_points, tasks, chunksize=4)):
                    if result['part'] != i:
                        raise RuntimeError('missing or reordered part result')
                    count += result['samples']
                    violations += result['violations']
                    worst.extend(result['witnesses'])
                    worst = sorted(worst, key=lambda x: x['distance_m'], reverse=True)[:20]
                    if (i+1) % 100 == 0 or i+1 == len(parts):
                        print(json.dumps({'mesh': name, 'completed_parts': i+1, 'total_parts': len(parts),
                                          'checked_samples': count, 'violations_so_far': violations}), flush=True)
            for witness in worst:
                point = np.array(witness['point_m'])*1000.
                close, distance, triangle = analytic_nearest(SOURCE_MM.triangles, point)
                witness.update(analytic_distance_m=distance/1000., analytic_point_m=(close/1000.).tolist(),
                               analytic_triangle=triangle,
                               analytic_agrees=abs(distance/1000.-witness['distance_m']) <= 1e-9)
                if bank['kind'] == 'legacy_excess_localization':
                    witness['normalized_distance_m'] = float(trimesh.proximity.closest_point(SOURCE_MM, point[None])[1][0]/1000.)
                    witness['winding_number'] = winding(SOURCE_MM.triangles, point)
            record.update(parts=len(parts), samples=count, violations=violations,
                          maximum_excess_m=worst[0]['distance_m'], witnesses=worst,
                          analytic_witnesses_agree=all(w['analytic_agrees'] for w in worst))
            record['passed'] = violations == 0 and record['analytic_witnesses_agree']
            if bank['kind'] == 'legacy_excess_localization':
                record['original_maximum_reproduced'] = abs(record['maximum_excess_m']-bank['original_maximum_m'][name]) <= 1e-9
                record['passed'] = False
        except Exception as error:
            record['error'] = repr(error)
        print(json.dumps({'mesh': name, **{k:v for k,v in record.items() if k != 'witnesses'}}), flush=True)
    report['all_passed'] = bool(report['meshes']) and all(r['passed'] for r in report['meshes'].values())
    report['elapsed_seconds'] = time.monotonic()-start
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
