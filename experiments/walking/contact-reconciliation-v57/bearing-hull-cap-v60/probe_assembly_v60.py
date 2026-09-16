"""Compile a source-bound proxy assembly and inspect preserved model properties."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import signal
import xml.etree.ElementTree as ET
import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[4]


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    parser = argparse.ArgumentParser()
    parser.add_argument('bank', type=Path)
    args = parser.parse_args()
    bank = json.loads(args.bank.read_text())
    for name, digest in bank['input_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    out = ROOT / bank['output_directory']
    out.mkdir(exist_ok=False)
    save = lambda value: (out / 'result.json').write_text(json.dumps(value, indent=2) + '\n')
    report = {'physics_steps': 0, 'model_admitted': False, 'physical_acceptance': False,
              'compile_success': False, 'inspection_complete': False}
    save(report)
    reference_path = ROOT / bank['reference_xml']
    xml = ET.parse(reference_path)
    root = xml.getroot()
    root.find('compiler').set('meshdir', str(ROOT / bank['source_mesh_directory']))
    count = 0
    for entry in bank['replacements']:
        archive = ROOT / entry['parts_npz']
        complete = json.loads((ROOT / entry['complete_json']).read_text())
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == complete['parts_sha256']
        body = root.find(f'.//body[@name="{entry["body"]}"]')
        geom = next(g for g in body.findall('geom') if g.get('mesh') == entry['mesh'] and g.get('class') == 'collision')
        index = list(body).index(geom)
        body.remove(geom)
        with np.load(archive, allow_pickle=False) as arrays:
            for i in range(complete['parts']):
                mesh_name = f'proxy_{entry["mesh"]}_{i}'
                ET.SubElement(root.find('asset'), 'mesh', name=mesh_name, inertia='shell',
                              vertex=' '.join(format(v, '.17g') for v in arrays[f'v{i:03}'].ravel()),
                              face=' '.join(str(int(x)) for x in arrays[f'f{i:03}'].ravel()))
                new = copy.deepcopy(geom)
                new.set('mesh', mesh_name)
                new.set('name', geom.get('name') + f'__proxy_{i}')
                body.insert(index+i, new)
        count += complete['parts']
    path = out / 'robot.xml'
    path.write_text(ET.tostring(root, encoding='unicode') + '\n')
    report['xml_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        model = mujoco.MjModel.from_xml_path(str(path))
    except Exception as error:
        report['compile_error'] = str(error)
        save(report)
        print(json.dumps(report), flush=True)
        return
    report['compile_success'] = True
    save(report)
    original = mujoco.MjModel.from_xml_path(str(reference_path))
    spec = importlib.util.spec_from_file_location('v59_compiler', ROOT / bank['inspection_module'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report.update(module.inspect_compiled(model, original, root, out))
    report['inspection_complete'] = True
    report['compiler_compatibility_passed'] = (all(x['exact'] for x in report['physical_arrays'].values())
        and all(report['orders_equal'].values()) and report['compiled_proxy_geoms'] == count
        and report['active_robot_colliders'] == 70-len(bank['replacements'])+count
        and report['explicit_excludes'] == 0 and report['contact_properties_equal']
        and report['all_geoms_unique_named'] and report['power_support_leg_coverage']
        and report['maximum_world_vertex_error_m'] <= 1e-7)
    report['all_four_target_meshes_replaced'] = len(bank['replacements']) == 4
    report['pose_bank_scope'] = 'full proxy candidate' if len(bank['replacements']) == 4 else 'partial bearing-only diagnostic; original unrepaired cavities remain'
    report['material_validation_is_separate'] = True
    save(report)
    print(json.dumps({k:v for k,v in report.items() if k != 'physical_arrays'}), flush=True)


if __name__ == '__main__':
    main()
