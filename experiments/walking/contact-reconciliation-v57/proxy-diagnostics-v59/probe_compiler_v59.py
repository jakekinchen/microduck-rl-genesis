"""Frozen compile/kinematics diagnostic; never steps dynamics or admits a model."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import signal
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
V57 = P.parent
V58 = V57 / 'proxy-experiment-v58'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def qmat(q):
    q = np.asarray(q, dtype=float)
    q /= np.linalg.norm(q)
    result = np.zeros(9)
    mujoco.mju_quat2Mat(result, q)
    return result.reshape(3, 3)


def frozen_poses():
    protocol = json.loads((V57 / 'protocol.json').read_text())
    poses = []
    for source in protocol['sources']:
        path = ROOT / source['path']
        assert sha(path) == source['sha256'], path
        wanted = set(source['zero_based_indices'])
        with gzip.open(path, 'rt') as stream:
            for i, line in enumerate(stream):
                if i in wanted:
                    poses.append({'source': source['path'], 'row_index': i,
                                  'qpos': json.loads(line)['qpos']})
    home = json.loads((ROOT / 'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad']
    for case in protocol['home_cases']:
        yaw = case['yaw_rad']
        poses.append({'source': 'explicit_HOME', 'case': case,
                      'qpos': [0, 0, case['root_z_m'], math.cos(yaw/2), 0, 0,
                               math.sin(yaw/2), *home]})
    assert len(poses) == 201
    return poses


def compare_arrays(reference, model):
    fields = ['body_mass', 'body_inertia', 'body_ipos', 'body_iquat', 'body_pos',
              'body_quat', 'body_parentid', 'body_rootid', 'body_weldid', 'qpos0',
              'jnt_qposadr', 'jnt_dofadr', 'jnt_type', 'jnt_limited', 'jnt_range',
              'jnt_axis', 'jnt_pos', 'jnt_stiffness', 'jnt_margin', 'jnt_solref',
              'jnt_solimp', 'dof_damping', 'dof_armature', 'dof_frictionloss',
              'dof_solref', 'dof_solimp']
    fields += [name for name in dir(reference) if name.startswith('actuator_')
               and isinstance(getattr(reference, name), np.ndarray)]
    results = {}
    for name in fields:
        a, b = getattr(reference, name), getattr(model, name)
        results[name] = {'exact': bool(np.array_equal(a, b)),
                         'reference_shape': list(a.shape), 'candidate_shape': list(b.shape)}
    return results


def original_source_frame(model, data, body_name, geom):
    bid = model.body(body_name).id
    rotation = data.xmat[bid].reshape(3, 3) @ qmat([float(x) for x in geom.get('quat', '1 0 0 0').split()])
    position = data.xpos[bid] + data.xmat[bid].reshape(3, 3) @ np.array([float(x) for x in geom.get('pos', '0 0 0').split()])
    return rotation, position


def inspect_compiled(model, original, xml_root, out):
    arrays = compare_arrays(original, model)
    names = {kind: [getattr(model, kind)(i).name for i in range(getattr(model, count))]
             == [getattr(original, kind)(i).name for i in range(getattr(original, count))]
             for kind, count in [('body', 'nbody'), ('joint', 'njnt'), ('actuator', 'nu')]}
    spec = importlib.util.spec_from_file_location('v56_pair_audit', ROOT / 'experiments/walking/upstream-audit-v56/audit.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    geoms = audit.geoms(model)
    active = [g for g in geoms if g['active'] and g['body_id']]
    rows = [{'geom_ids': [a['id'], b['id']], 'eligible': audit.eligible_pair(model, a['id'], b['id'])}
            for i, a in enumerate(active) for b in active[i+1:]]
    save(out / 'pair-matrix.json', {'geoms': geoms, 'pairs': rows})
    support = [g for g in active if g['mesh'] == 'power_support']
    legs = [g for g in active if g['mesh'] == 'leg']
    support_pairs = [audit.eligible_pair(model, a['id'], b['id']) for a in support for b in legs]
    # Preserve effective mask/contact properties for every original geom or replacement.
    original_geoms = {original.geom(i).name: i for i in range(original.ngeom)}
    contact_fields = ['geom_contype', 'geom_conaffinity', 'geom_condim', 'geom_friction',
                      'geom_solref', 'geom_solimp', 'geom_margin', 'geom_gap',
                      'geom_priority', 'geom_solmix', 'geom_bodyid']
    property_checks = []
    for i in range(model.ngeom):
        name = model.geom(i).name
        parent = name.split('__proxy_')[0]
        j = original_geoms[parent]
        property_checks.append(all(np.array_equal(getattr(model, f)[i], getattr(original, f)[j]) for f in contact_fields))
    poses = frozen_poses()
    data = mujoco.MjData(model)
    original_xml = ET.parse(V57 / 'jaw-contact-enabled/robot.xml').getroot()
    original_elements = {g.get('name'): (b.get('name'), g) for b in original_xml.findall('.//body') for g in b.findall('geom')}
    assets = {mesh.get('name'): mesh for mesh in xml_root.findall('./asset/mesh')}
    home = next(x for x in poses if x['source'] == 'explicit_HOME' and x['case']['yaw_rad'] == 0)
    data.qpos[:] = home['qpos']
    mujoco.mj_kinematics(model, data)
    transform_checks = []
    for i in range(model.ngeom):
        geom_name = model.geom(i).name
        if '__proxy_' not in geom_name:
            continue
        mid = int(model.geom_dataid[i])
        asset = assets[model.mesh(mid).name]
        vertices = np.fromstring(asset.get('vertex'), sep=' ').reshape(-1, 3)
        body, source_geom = original_elements[geom_name.split('__proxy_')[0]]
        rotation, position = original_source_frame(model, data, body, source_geom)
        expected = vertices @ rotation.T + position
        start, count = int(model.mesh_vertadr[mid]), int(model.mesh_vertnum[mid])
        actual = model.mesh_vert[start:start+count].astype(float) @ data.geom_xmat[i].reshape(3, 3).T + data.geom_xpos[i]
        error = max(cKDTree(actual).query(expected)[0].max(), cKDTree(expected).query(actual)[0].max())
        transform_checks.append({'geom': geom_name, 'vertices': count, 'max_world_vertex_error_m': float(error)})
    save(out / 'compiled-geometry.json', transform_checks)
    # Export source-local witnesses for the independent, compilation-free validator.
    cavity = json.loads((V57 / 'cavity-audit/results.json').read_text())
    source_by_pair = {(b, g.get('mesh')): g for b, g in original_elements.values() if g.get('class') == 'collision'}
    witnesses = []
    for index, witness in enumerate(cavity['results']):
        pose = home if witness['pose'] == 'home' else next(x for x in poses if x.get('row_index') == 1399 and 'laser-course' in x['source'])
        data.qpos[:] = pose['qpos']
        mujoco.mj_kinematics(model, data)
        sides = []
        for label, (body, mesh) in zip(('a', 'b'), (witness['pair'][:2], witness['pair'][2:])):
            rotation, position = original_source_frame(model, data, body, source_by_pair[(body, mesh)])
            local = (np.array(witness['convex_contact_world_m']) - position) @ rotation
            sides.append({'mesh': mesh, 'local_point_m': local.tolist(),
                          'source_inside_three_rays': witness[f'convex_contact_inside_original_cad_{label}_three_rays'],
                          'source_distance_m': witness[f'convex_contact_distance_to_cad_{label}_m']})
        witnesses.append({'id': f'{index}-{witness["pose"]}', 'sides': sides})
    save(out / 'local-cavity-witnesses.json', witnesses)
    pose_results = []
    for pose in poses:
        data.qpos[:] = pose['qpos']
        mujoco.mj_kinematics(model, data)
        mujoco.mj_collision(model, data)
        contacts = [{'geom_names': [model.geom(int(c.geom1)).name, model.geom(int(c.geom2)).name],
                     'penetration_m': -float(c.dist)} for c in data.contact
                    if model.geom_bodyid[c.geom1] and model.geom_bodyid[c.geom2] and c.dist < 0]
        pose_results.append({k: v for k, v in pose.items() if k != 'qpos'} |
                            {'maximum_penetration_m': max([0.] + [c['penetration_m'] for c in contacts]), 'contacts': contacts})
    save(out / 'pose-results.json', pose_results)
    return {'physical_arrays': arrays, 'orders_equal': names, 'active_robot_colliders': len(active),
            'explicit_excludes': model.nexclude, 'contact_properties_equal': all(property_checks),
            'all_geoms_unique_named': all(g['name'] for g in geoms) and len(set(g['name'] for g in geoms)) == len(geoms),
            'power_support_leg_coverage': len(support) == 1 and len(legs) == 2 and all(support_pairs),
            'compiled_proxy_geoms': len(transform_checks),
            'maximum_world_vertex_error_m': max(x['max_world_vertex_error_m'] for x in transform_checks),
            'sampled_poses': len(poses), 'poses_over_1mm': sum(x['maximum_penetration_m'] > .001 for x in pose_results),
            'maximum_penetration_m': max(x['maximum_penetration_m'] for x in pose_results)}


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=['baseline', 'shell-fragment'])
    args = parser.parse_args()
    protocol = json.loads((P / 'protocol.json').read_text())
    for path, digest in protocol['input_sha256'].items():
        assert sha(ROOT / path) == digest, path
    for path, digest in json.loads((P / 'implementation.lock.json').read_text()).items():
        assert sha(P / path) == digest, path
    out = P / args.case
    out.mkdir(exist_ok=False)
    report = {'case': args.case, 'physics_steps': 0, 'model_admitted': False, 'physical_acceptance': False,
              'compile_success': False, 'inspection_complete': False}
    save(out / 'result.json', report)
    xml = ET.parse(V58 / 'proxy-robot.xml')
    root = xml.getroot()
    if args.case == 'shell-fragment':
        mesh = root.find(f'./asset/mesh[@name="{protocol["shell_mesh_name"]}"]')
        assert mesh is not None and mesh.get('inertia') is None
        mesh.set('inertia', 'shell')
    xml_path = out / 'robot.xml'
    xml_path.write_text(ET.tostring(root, encoding='unicode') + '\n')
    report['model_sha256'] = sha(xml_path)
    try:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
    except Exception as error:
        report['compile_error'] = str(error)
        save(out / 'result.json', report)
        print(json.dumps(report), flush=True)
        return
    report['compile_success'] = True
    save(out / 'result.json', report)
    original = mujoco.MjModel.from_xml_path(str(V57 / 'jaw-contact-enabled/robot.xml'))
    report.update(inspect_compiled(model, original, root, out))
    report['inspection_complete'] = True
    report['compiler_compatibility_passed'] = (all(x['exact'] for x in report['physical_arrays'].values())
        and all(report['orders_equal'].values()) and report['active_robot_colliders'] == 322
        and report['compiled_proxy_geoms'] == 256 and report['explicit_excludes'] == 0
        and report['contact_properties_equal'] and report['all_geoms_unique_named']
        and report['power_support_leg_coverage'] and report['maximum_world_vertex_error_m'] <= 1e-7)
    # Material gates from V58 remain failed even if all compiler checks pass.
    report['material_gates_passed'] = False
    save(out / 'result.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'physical_arrays'}), flush=True)


if __name__ == '__main__':
    main()
