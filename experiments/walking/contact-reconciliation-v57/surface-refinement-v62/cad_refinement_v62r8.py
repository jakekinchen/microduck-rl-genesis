"""Source-clipped local CoACD followed by refinement of residual excess."""
from pathlib import Path
import hashlib
import json
import shutil
import copy
import numpy as np
import trimesh
import coacd
from cad_refinement_v62r2 import (
    to_manifold, from_manifold, make_hull, face_samples, excess_distances,
    refine as refine_residuals,
)

ROOT = Path(__file__).resolve().parents[4]


def save_parts(path, parts):
    arrays = {f'{key}{i:03}': np.asarray(getattr(part, attr))
              for i, part in enumerate(parts)
              for key, attr in [('v', 'vertices'), ('f', 'faces')]}
    with path.open('xb') as stream:
        np.savez_compressed(stream, **arrays)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refine(source, old_parts, config, progress=None):
    source_solid = to_manifold(source)
    scaled = trimesh.Trimesh(source.vertices*1000., source.faces, process=False)
    output, records = [], []
    region_root = ROOT/config['region_directory']
    region_root.mkdir(parents=True, exist_ok=False)
    reuse = json.loads((ROOT/config['reuse_index']).read_text())
    previous_protocol = json.loads((ROOT/config['reuse_protocol']).read_text())
    previous_config = previous_protocol['config']
    previous_mesh = previous_protocol['meshes'][config['reuse_mesh']]
    for source_key, digest_key in [('source_stl', 'source_stl_sha256'), ('parts_npz', 'parent_parts_sha256')]:
        if previous_protocol['input_sha256'][previous_mesh[source_key]] != config[digest_key]:
            raise RuntimeError('reuse source or parent archive changed')
    for key in ('selection_threshold_m', 'refinement_target_m', 'maximum_depth',
                'maximum_leaves_per_parent', 'maximum_parts_per_region', 'coacd_params'):
        if previous_config[key] != config[key]:
            raise RuntimeError('reuse changes the local algorithm configuration')
    if [r['parent_part'] for r in reuse] != list(range(len(reuse))):
        raise RuntimeError('reuse index is not a complete prefix')
    for index, part in enumerate(old_parts):
        if index < len(reuse):
            record = copy.deepcopy(reuse[index])
            if record['output_start'] != len(output):
                raise RuntimeError('reused prefix output offset mismatch')
            if record['decision'] == 'unchanged':
                if record['output_count'] != 1:
                    raise RuntimeError('reused unchanged region has invalid count')
                output.append(part)
            elif record['decision'] == 'local_coacd_source_partition':
                previous = ROOT/record['region_directory']
                region = region_root/f'{index:03}'
                for filename, key in [('coacd-parts.npz', 'coarse_sha256'), ('refined-parts.npz', 'refined_sha256')]:
                    if hashlib.sha256((previous/filename).read_bytes()).hexdigest() != record[key]:
                        raise RuntimeError('reused region digest mismatch')
                shutil.copytree(previous, region)
                with np.load(region/'refined-parts.npz', allow_pickle=False) as archive:
                    if len(archive.files) != 2*record['output_count']:
                        raise RuntimeError('reused region count mismatch')
                    output.extend(trimesh.Trimesh(archive[f'v{i:03}'], archive[f'f{i:03}'], process=False)
                                  for i in range(record['output_count']))
                record['reused_from'] = previous.relative_to(ROOT).as_posix()
                record['region_directory'] = region.relative_to(ROOT).as_posix()
                (region/'region.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
            elif record['decision'] != 'empty_source_intersection' or record['output_count'] != 0 or record['intersected_source_volume_m3'] != 0:
                raise RuntimeError('unknown reuse decision')
            if len(output) > config['maximum_total_parts']:
                raise RuntimeError('reused prefix exceeds new declared total budget')
            records.append(record)
            if progress is not None:
                progress(records)
            continue
        error = float(excess_distances(source, face_samples(part), scaled).max())
        record = {'parent_part': index, 'original_dense_excess_m': error,
                  'original_volume_m3': float(part.volume), 'output_start': len(output)}
        if error <= config['selection_threshold_m']:
            output.append(part)
            record.update(decision='unchanged', output_count=1)
        else:
            clip_solid = source_solid^to_manifold(part)
            record['intersected_source_volume_m3'] = float(clip_solid.volume())
            if clip_solid.is_empty():
                record.update(decision='empty_source_intersection', output_count=0)
            else:
                clip = from_manifold(clip_solid)
                if not clip.is_watertight or not clip.is_winding_consistent:
                    raise RuntimeError(f'non-oriented clipped source at parent {index}')
                region = region_root/f'{index:03}'
                region.mkdir(exist_ok=False)
                np.savez_compressed(region/'source-clip.npz', vertices=clip.vertices, faces=clip.faces)
                coarse = [make_hull(v) for v, _ in coacd.run_coacd(
                    coacd.Mesh(np.array(clip.vertices, copy=True), np.array(clip.faces, copy=True)),
                    **config['coacd_params'])]
                coarse_hash = save_parts(region/'coacd-parts.npz', coarse)
                local_config = config | {'maximum_total_parts': config['maximum_parts_per_region']}
                polished, lineage = refine_residuals(source, coarse, local_config)
                polished_hash = save_parts(region/'refined-parts.npz', polished)
                record.update(decision='local_coacd_source_partition', output_count=len(polished),
                              coarse_parts=len(coarse), region_directory=region.relative_to(ROOT).as_posix(),
                              coarse_sha256=coarse_hash, refined_sha256=polished_hash,
                              local_refinement=lineage,
                              source_coverage='approximate local decomposition; independent missing-material gate required')
                (region/'region.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
                output.extend(polished)
        if len(output) > config['maximum_total_parts']:
            raise RuntimeError('fixed total piece budget exhausted; completed region artifacts are diagnostic only')
        records.append(record)
        if progress is not None:
            progress(records)
    return output, records
