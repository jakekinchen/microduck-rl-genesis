"""Independent sampled geometry and fixed-pose checks; no dynamics."""
from pathlib import Path
import signal
signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
import importlib.util
import json,gzip,hashlib,copy,os,math,xml.etree.ElementTree as ET
import numpy as np
import mujoco
import trimesh
from scipy.spatial import ConvexHull

P=Path(__file__).resolve().parent;ROOT=P.parents[3];V57=P.parent
UP=ROOT/'experiments/walking/upstream-audit-v56/sources/src/mjlab_microduck/robot/microduck'
protocol=json.loads((P/'protocol.json').read_text());tolerance=protocol['validation']['sampled_geometry_tolerance_m']
report={'scope':'sampled geometric proxy diagnostic, not global error bound or dynamic acceptance','physics_steps':0,'physical_acceptance':False,'meshes':{},'complete_model_admitted':False}
def persist():
    (P/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
def sample(values,n):
    return values[np.unique(np.linspace(0,len(values)-1,min(n,len(values)),dtype=int))]
def original(path):
    raw=path.read_bytes();dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
    v,i=np.unique(np.frombuffer(raw,dtype=dtype,offset=84)['vertices'].reshape(-1,3).astype(float),axis=0,return_inverse=True)
    return trimesh.Trimesh(v,i.reshape(-1,3),process=False)
def union_inside(points,hulls):
    inside=np.zeros(len(points),bool)
    for hull in hulls:
        for start in range(0,len(points),512):
            x=points[start:start+512];inside[start:start+len(x)] |= np.all(x@hull.equations[:,:3].T+hull.equations[:,3]<=1e-9,axis=1)
    return inside
parts_by_name={};hulls_by_name={}
for name in protocol['meshes']:
    path=P/'outputs'/name/'parts.npz';complete=path.with_name('complete.json')
    if not path.exists() or not complete.exists():report['meshes'][name]={'status':'missing_complete_geometry','passed':False};persist();continue
    metadata=json.loads(complete.read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==metadata['parts_sha256']
    with np.load(path,allow_pickle=False) as arrays:parts=[trimesh.Trimesh(arrays[f'v{i:03}'],arrays[f'f{i:03}'],process=False) for i in range(metadata['parts'])]
    finite=all(np.isfinite(part.vertices).all() for part in parts)
    count_ok=1<=len(parts)<=protocol['budget']['maximum_parts_per_mesh']
    if not finite or not count_ok:
        report['meshes'][name]={'status':'invalid_or_over_hull_limit','parts':len(parts),'finite':finite,'passed':False};persist();continue
    hulls=[ConvexHull(part.vertices) for part in parts];source=original(UP/'assets'/f'{name}.stl')
    source_points=np.vstack([sample(source.vertices,4096),sample(source.triangles_center,4096)])
    missing=~union_inside(source_points,hulls);missing_distance=np.zeros(len(source_points))
    if missing.any():
        distances=np.full(int(missing.sum()),np.inf)
        for part in parts:distances=np.minimum(distances,trimesh.proximity.closest_point(part,source_points[missing])[1])
        missing_distance[missing]=distances
    proxy_points=np.vstack([np.vstack([part.vertices for part in parts]),sample(np.vstack([part.triangles_center for part in parts]),4096)])
    # Sample signed material occupancy using the original watertight triangles.
    inside=source.contains(proxy_points)
    excess_distance=np.zeros(len(proxy_points))
    for start in range(0,len(proxy_points),512):
        ids=np.flatnonzero(~inside[start:start+512])+start
        if len(ids):excess_distance[ids]=trimesh.proximity.closest_point(source,proxy_points[ids])[1]
    watertight=all(part.is_watertight for part in parts)
    convex=all(part.is_convex for part in parts)
    record={'status':'verified_sampled_geometry','parts':len(parts),'vertices':sum(len(part.vertices) for part in parts),'faces':sum(len(part.faces) for part in parts),'all_parts_watertight':bool(watertight),'all_parts_convex':bool(convex),'source_samples':len(source_points),'proxy_samples':len(proxy_points),'source_samples_outside_union':int(missing.sum()),'max_sampled_missing_material_m':float(missing_distance.max()),'max_sampled_excess_material_m':float(excess_distance.max()),'sampled_tolerance_m':tolerance,'passed':bool(watertight and convex and missing_distance.max()<=tolerance and excess_distance.max()<=tolerance)}
    report['meshes'][name]=record;parts_by_name[name]=parts;hulls_by_name[name]=hulls;persist();print(name,json.dumps(record),flush=True)

# Assemble even partial geometry as an explicitly partial diagnostic model.
# Only the four implicated body/mesh instances change, not all bearing instances.
xml=ET.parse(V57/'jaw-contact-enabled/robot.xml');root=xml.getroot();root.find('compiler').set('meshdir',str(UP/'assets'))
asset=root.find('asset');targets={('neck_pitch','seeed_bearing__configuration__22x16x4'),('neck_pitch','neck_pitch'),('jaw_soft','bottom_head_shell'),('jaw_soft','jaw')}
for name,parts in parts_by_name.items():
    for i,part in enumerate(parts):
        ET.SubElement(asset,'mesh',name=f'proxy_{name}_{i}',vertex=' '.join(format(v,'.17g') for v in part.vertices.ravel()),face=' '.join(str(int(v)) for v in part.faces.ravel()))
replacements=[]
for body in root.findall('.//body'):
    for geom in list(body.findall('geom')):
        key=(body.get('name'),geom.get('mesh'))
        if key not in targets or geom.get('class')!='collision' or key[1] not in parts_by_name:continue
        index=list(body).index(geom);body.remove(geom)
        for i in range(len(parts_by_name[key[1]])):
            new=copy.deepcopy(geom);new.set('name',geom.get('name')+f'__proxy_{i}');new.set('mesh',f'proxy_{key[1]}_{i}');body.insert(index+i,new)
        replacements.append(list(key))
assert root.findall('./contact/exclude')==[]
ET.indent(root);xml_path=P/'proxy-robot.xml';xml_path.write_text(ET.tostring(root,encoding='unicode')+'\n')
reference=mujoco.MjModel.from_xml_path(str(V57/'jaw-contact-enabled/robot.xml'));model=mujoco.MjModel.from_xml_path(str(xml_path));data=mujoco.MjData(model)
fields=['body_mass','body_inertia','body_ipos','body_iquat','body_pos','body_quat','jnt_qposadr','jnt_range','jnt_axis','jnt_pos','dof_damping','dof_armature','dof_frictionloss','actuator_trnid','actuator_gear','actuator_gaintype','actuator_biastype','actuator_gainprm','actuator_biasprm','actuator_ctrlrange','actuator_forcerange']
array_equal={field:bool(np.array_equal(getattr(reference,field),getattr(model,field))) for field in fields}
report['model']={'replaced_instances':replacements,'all_four_instances_replaced':len(replacements)==4,'active_robot_geoms':int(np.sum((model.geom_contype!=0)|(model.geom_conaffinity!=0))),'explicit_excludes':int(model.nexclude),'physical_arrays_equal':array_equal,'joint_order_equal':[model.joint(i).name for i in range(model.njnt)]==[reference.joint(i).name for i in range(reference.njnt)]}
report['model']['actuator_order_equal']=[model.actuator(i).name for i in range(model.nu)]==[reference.actuator(i).name for i in range(reference.nu)]
module_spec=importlib.util.spec_from_file_location('v56_pair_audit',ROOT/'experiments/walking/upstream-audit-v56/audit.py');pair_audit=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(pair_audit)
geom_rows=pair_audit.geoms(model);active=[g for g in geom_rows if g['active'] and g['body_id']]
pair_rows=[{'geom_ids':[a['id'],b['id']],'eligible':pair_audit.eligible_pair(model,a['id'],b['id'])} for a in active for b in active if a['id']<b['id']]
(P/'pair-matrix.json').write_text(json.dumps({'geoms':geom_rows,'all_internal_pairs':pair_rows},indent=2)+'\n')
report['model']['pair_matrix_sha256']=hashlib.sha256((P/'pair-matrix.json').read_bytes()).hexdigest()
report['model']['all_geoms_uniquely_named']=len({g['name'] for g in geom_rows})==len(geom_rows) and all(g['name'] for g in geom_rows)
support=[g for g in active if g['mesh']=='power_support'];legs=[g for g in active if g['mesh']=='leg']
report['model']['power_support_leg_pairs']=[{'support':a['id'],'leg':b['id'],'eligible':pair_audit.eligible_pair(model,a['id'],b['id'])} for a in support for b in legs]
report['model']['coverage_preserved']=len(replacements)==4 and len(support)==1 and len(legs)==2 and all(x['eligible'] for x in report['model']['power_support_leg_pairs']) and report['model']['all_geoms_uniquely_named'] and model.nexclude==0
persist()

# Transform recorded world-space cavity points back to the original geom frame.
cavity=json.loads((V57/'cavity-audit/results.json').read_text())
pose_protocol=json.loads((V57/'protocol.json').read_text());poses=[]
for source in pose_protocol['sources']:
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
    wanted=set(source['zero_based_indices'])
    with gzip.open(ROOT/source['path'],'rt') as stream:
        for i,line in enumerate(stream):
            if i in wanted:
                row=json.loads(line);poses.append({'source':source['path'],'row_index':i,'qpos':row['qpos']})
home=json.loads((ROOT/'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad']
for case in pose_protocol['home_cases']:
    yaw=case['yaw_rad'];poses.append({'source':'explicit_HOME','case':case,'qpos':[0,0,case['root_z_m'],math.cos(yaw/2),0,0,math.sin(yaw/2),*home]})
full_names={g.get('name'):(body.get('name'),g) for body in ET.parse(V57/'jaw-contact-enabled/robot.xml').getroot().findall('.//body') for g in body.findall('geom')}
cavity_checks=[]
for witness in cavity['results']:
    if witness['pose']=='home':
        pose=next(x for x in poses if x['source']=='explicit_HOME' and x['case']['yaw_rad']==0)
    else:
        pose=next(x for x in poses if x.get('row_index')==1399 and 'laser-course' in x['source'])
    data.qpos[:]=pose['qpos'];mujoco.mj_kinematics(model,data);point=np.array(witness['convex_contact_world_m']);inside=[]
    for body_name,mesh_name in [(witness['pair'][0],witness['pair'][1]),(witness['pair'][2],witness['pair'][3])]:
        if mesh_name not in hulls_by_name:inside.append(None);continue
        elem=next(g for body,g in full_names.values() if body==body_name and g.get('mesh')==mesh_name and g.get('class')=='collision');bid=model.body(body_name).id
        q=np.array([float(x) for x in elem.get('quat','1 0 0 0').split()]);q/=np.linalg.norm(q);r=np.zeros(9);mujoco.mju_quat2Mat(r,q);body_rot=data.xmat[bid].reshape(3,3);rotation=body_rot@r.reshape(3,3);pos=data.xpos[bid]+body_rot@np.array([float(x) for x in elem.get('pos','0 0 0').split()]);local=(point-pos)@rotation
        inside.append(bool(union_inside(local.reshape(1,3),hulls_by_name[mesh_name])[0]))
    required_empty=[i for i,label in enumerate(['a','b']) if not any(witness[f'convex_contact_inside_original_cad_{label}_three_rays']) and witness[f'convex_contact_distance_to_cad_{label}_m']>tolerance]
    cavity_checks.append({'pose':witness['pose'],'pair':witness['pair'],'inside_proxy_unions':inside,'must_remain_empty_sides':required_empty,'source_cavity_preserved':None not in inside and all(not inside[i] for i in required_empty),'no_false_pair_contact_at_witness':None not in inside and not all(inside)})
report['cavity_checks']=cavity_checks;persist()
pose_results=[]
for pose in poses:
    data.qpos[:]=pose['qpos'];mujoco.mj_kinematics(model,data);mujoco.mj_collision(model,data)
    contacts=[]
    for c in data.contact:
        a,b=int(c.geom1),int(c.geom2)
        if model.geom_bodyid[a] and model.geom_bodyid[b] and -float(c.dist)>0:
            contacts.append({'geom_names':[model.geom(a).name,model.geom(b).name],'penetration_m':-float(c.dist)})
    pose_results.append({k:v for k,v in pose.items() if k!='qpos'}|{'max_penetration_m':max([0.]+[x['penetration_m'] for x in contacts]),'contacts':contacts})
(P/'pose-results.json').write_text(json.dumps(pose_results,indent=2)+'\n')
report['pose_bank']={'sampled_poses':len(poses),'maximum_penetration_m':max(x['max_penetration_m'] for x in pose_results),'poses_over_1mm':sum(x['max_penetration_m']>.001 for x in pose_results)}
report['sampled_geometry_gates_passed']=len(parts_by_name)==4 and all(x['passed'] for x in report['meshes'].values()) and all(array_equal.values()) and report['model']['coverage_preserved'] and report['model']['joint_order_equal'] and report['model']['actuator_order_equal'] and all(x['no_false_pair_contact_at_witness'] and x['source_cavity_preserved'] for x in cavity_checks) and report['pose_bank']['poses_over_1mm']==0
report['complete_model_admitted']=False
persist();print(json.dumps(report['pose_bank']),flush=True)
