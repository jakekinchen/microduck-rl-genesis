"""Source-clipped local CoACD followed by refinement of residual excess."""
from pathlib import Path
import hashlib
import json
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
    for index, part in enumerate(old_parts):
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
