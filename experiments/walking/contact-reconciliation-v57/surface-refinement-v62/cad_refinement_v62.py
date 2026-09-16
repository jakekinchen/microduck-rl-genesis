"""Source-CAD intersection and deterministic local convex partitioning."""
from pathlib import Path
import sys
import numpy as np
import trimesh
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / '.workspace/geometry-deps-v62/site'))
import manifold3d as manifold


def to_manifold(mesh):
    result = manifold.Manifold(manifold.Mesh64(
        np.array(mesh.vertices, dtype=np.float64, order='C', copy=True),
        np.array(mesh.faces, dtype=np.uint64, order='C', copy=True)))
    if result.status() != manifold.Error.NoError:
        raise ValueError(f'manifold import failed: {result.status()}')
    return result


def from_manifold(solid):
    if solid.status() != manifold.Error.NoError:
        raise ValueError(f'manifold operation failed: {solid.status()}')
    raw = solid.to_mesh64()
    return trimesh.Trimesh(np.asarray(raw.vert_properties)[:, :3],
                           np.asarray(raw.tri_verts), process=False)


def make_hull(vertices):
    hull = ConvexHull(vertices)
    faces = hull.simplices.copy()
    triangles = vertices[faces]
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    flip = np.einsum('ij,ij->i', cross, hull.equations[:, :3]) < 0
    faces[flip] = faces[flip][:, [0, 2, 1]]
    used, inverse = np.unique(faces, return_inverse=True)
    mesh = trimesh.Trimesh(vertices[used], inverse.reshape(-1, 3), process=False)
    if not mesh.is_watertight or not mesh.is_convex or mesh.volume <= 0:
        raise ValueError('constructed hull failed positive-volume/convex/watertight checks')
    return mesh


def face_samples(mesh, dense=True):
    t = mesh.triangles
    points = [mesh.vertices, t.mean(axis=1)]
    if dense:
        points += [(t[:, 0]+t[:, 1])/2, (t[:, 1]+t[:, 2])/2,
                   (t[:, 2]+t[:, 0])/2]
        points += [(4*t[:, i]+t[:, (i+1)%3]+t[:, (i+2)%3])/6 for i in range(3)]
    return np.vstack(points)


def excess_distances(source, points):
    result = np.zeros(len(points))
    for start in range(0, len(points), 512):
        batch = points[start:start+512]
        outside = ~source.contains(batch)
        if outside.any():
            result[start+np.flatnonzero(outside)] = trimesh.proximity.closest_point(source, batch[outside])[1]
    if not np.isfinite(result).all():
        raise ValueError('nonfinite source distance')
    return result


def partition_source(source, clipped, config):
    """Retain every nonempty source component; split only failing convex hulls."""
    pending = [(component, 0) for component in clipped.decompose()]
    leaves, events = [], []
    while pending:
        solid, depth = pending.pop(0)
        mesh = from_manifold(solid)
        if solid.is_empty() or len(mesh.vertices) < 4 or solid.volume() <= 0:
            raise ValueError('unexpected empty or nonpositive partition')
        hull = make_hull(np.asarray(mesh.vertices))
        error = float(excess_distances(source, face_samples(hull)).max())
        record = {'depth': depth, 'source_volume_m3': float(solid.volume()),
                  'convex_volume_m3': float(hull.volume), 'dense_excess_m': error}
        if error <= config['refinement_target_m']:
            leaves.append(hull)
            events.append(record | {'decision': 'retain'})
        else:
            if depth >= config['maximum_depth']:
                raise RuntimeError('fixed partition depth exhausted')
            if len(leaves)+len(pending)+2 > config['maximum_leaves_per_parent']:
                raise RuntimeError('fixed local piece budget exhausted')
            axis = int(np.argmax(mesh.extents))
            offset = float(mesh.bounds[:, axis].mean())
            normal = np.eye(3)[axis]
            children = solid.split_by_plane(normal, offset)
            nonempty = [child for child in children if not child.is_empty()]
            if len(nonempty) != 2:
                raise RuntimeError('partition did not split into two nonempty regions')
            total = sum(child.volume() for child in nonempty)
            if abs(total-solid.volume()) > max(1e-18, abs(solid.volume())*1e-8):
                raise RuntimeError('partition volume conservation failed')
            events.append(record | {'decision': 'split', 'axis': axis, 'offset_m': offset})
            pending.extend((child, depth+1) for child in nonempty)
    return leaves, events


def refine(source, old_parts, config, progress=None):
    source_solid = to_manifold(source)
    source_roundtrip = from_manifold(source_solid)
    if abs(source_roundtrip.volume-source.volume) > max(1e-18, abs(source.volume)*1e-8):
        raise RuntimeError('source solid import changed volume')
    output, records = [], []
    for index, part in enumerate(old_parts):
        error = float(excess_distances(source, face_samples(part)).max())
        forced = index in config.get('seed_parent_indices', [])
        record = {'parent_part': index, 'original_dense_excess_m': error,
                  'original_volume_m3': float(part.volume), 'output_start': len(output)}
        if not forced and error <= config['selection_threshold_m']:
            output.append(part)
            record.update(decision='unchanged', output_count=1)
        else:
            clipped = source_solid ^ to_manifold(part)
            if clipped.status() != manifold.Error.NoError:
                raise RuntimeError(f'CAD intersection error at part {index}')
            record['intersected_source_volume_m3'] = float(clipped.volume())
            if clipped.is_empty():
                # This is an explicit source-solid Boolean result, never silent pruning.
                record.update(decision='empty_source_intersection', output_count=0)
            else:
                leaves, events = partition_source(source, clipped, config)
                output.extend(leaves)
                record.update(decision='source_partition', output_count=len(leaves), partition_events=events)
        if len(output) > config['maximum_total_parts']:
            raise RuntimeError('fixed total piece budget exhausted')
        records.append(record)
        if progress is not None:
            progress(records)
    return output, records
