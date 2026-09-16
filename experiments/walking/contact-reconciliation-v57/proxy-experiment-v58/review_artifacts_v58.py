"""Posthoc classification of immutable V58 outputs, including compile failure."""
from pathlib import Path
import ast,gzip,hashlib,json,xml.etree.ElementTree as ET
import numpy as np
import mujoco
from scipy.spatial import ConvexHull
import trimesh

p=Path(__file__).resolve().parent;root=p.parents[3];v57=p.parent
frozen=json.loads((p/'implementation.lock.json').read_text())
for name,digest in frozen.items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
tree=ast.parse((p/'validate_proxy_v58.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='union_inside')
namespace={'np':np};exec(compile(ast.Module(body=[function],type_ignores=[]),'frozen_union_inside','exec'),namespace);union_inside=namespace['union_inside']
hulls={};parts=[]
for path in sorted((p/'outputs').glob('*/parts.npz')):
    complete=json.loads(path.with_name('complete.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==complete['parts_sha256']
    hulls[path.parent.name]=[]
    with np.load(path,allow_pickle=False) as data:
        for i in range(complete['parts']):
            vertices,faces=data[f'v{i:03}'],data[f'f{i:03}'];mesh=trimesh.Trimesh(vertices,faces,process=False);hull=ConvexHull(vertices);hulls[path.parent.name].append(hull)
            parts.append({'mesh':path.parent.name,'part':i,'vertices':len(vertices),'faces':len(faces),'convex_hull_volume_m3':float(hull.volume),'triangle_signed_volume_m3':float(mesh.volume),'minimum_centered_singular_value_m':float(np.linalg.svd(vertices-vertices.mean(0),compute_uv=False)[-1]),'is_convex_trimesh':bool(mesh.is_convex),'watertight':bool(mesh.is_watertight),'bounds_extent_m':np.ptp(vertices,axis=0).tolist()})
(p/'posthoc-part-audit.json').write_text(json.dumps({'boundary':'unmodified generated parts; posthoc numerical diagnosis','parts':parts},indent=2)+'\n')
source_xml=v57/'jaw-contact-enabled/robot.xml';model=mujoco.MjModel.from_xml_path(str(source_xml));data=mujoco.MjData(model);xml=ET.parse(source_xml)
elements={(b.get('name'),g.get('mesh')):g for b in xml.getroot().findall('.//body') for g in b.findall('geom') if g.get('class')=='collision'}
cavity=json.loads((v57/'cavity-audit/results.json').read_text());home=json.loads((root/'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad'];poses={'home':[0,0,.125,1,0,0,0,*home]}
with gzip.open(root/'receipts/laser-course/20260913-v2-development/nominal/trajectory.jsonl.gz','rt') as stream:
    for i,line in enumerate(stream):
        if i==1399:poses['worst_sample']=json.loads(line)['qpos'];break
checks=[]
for witness in cavity['results']:
    data.qpos[:]=poses[witness['pose']];mujoco.mj_kinematics(model,data);point=np.array(witness['convex_contact_world_m']);sides=[]
    for label,(body_name,mesh_name) in zip(['a','b'],[(witness['pair'][0],witness['pair'][1]),(witness['pair'][2],witness['pair'][3])]):
        g=elements[(body_name,mesh_name)];bid=model.body(body_name).id;q=np.array([float(x) for x in g.get('quat','1 0 0 0').split()]);q/=np.linalg.norm(q);r=np.zeros(9);mujoco.mju_quat2Mat(r,q);rb=data.xmat[bid].reshape(3,3);rotation=rb@r.reshape(3,3);position=data.xpos[bid]+rb@np.array([float(x) for x in g.get('pos','0 0 0').split()]);local=(point-position)@rotation
        inside=bool(union_inside(local.reshape(1,3),hulls[mesh_name])[0]);must_empty=not any(witness[f'convex_contact_inside_original_cad_{label}_three_rays']) and witness[f'convex_contact_distance_to_cad_{label}_m']>.00025
        sides.append({'body':body_name,'mesh':mesh_name,'inside_convex_part_union':inside,'must_remain_empty':must_empty,'cavity_preserved':not must_empty or not inside})
    checks.append({'pose':witness['pose'],'pair':witness['pair'],'sides':sides,'source_cavities_preserved':all(s['cavity_preserved'] for s in sides),'both_proxy_sides_filled':all(s['inside_convex_part_union'] for s in sides)})
report={'scope':'posthoc fixed-point material occupancy; original kinematic frames and SciPy convex hulls of generated vertices, no compiled proxy or dynamics','physics_steps':0,'all_8_source_cavities_preserved':all(c['source_cavities_preserved'] for c in checks),'checks':checks,'complete_proxy_model_compiles':False,'full_pose_bank_evaluated':False,'physical_arrays_validated':False,'pair_matrix_validated':False,'proxy_admitted':False}
(p/'posthoc-cavity-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':len(parts),'cavity_cases_preserved':sum(x['source_cavities_preserved'] for x in checks),'cavity_cases':len(checks),'proxy_admitted':False}))
