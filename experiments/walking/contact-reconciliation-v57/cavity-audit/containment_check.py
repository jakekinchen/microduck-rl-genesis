"""Independent fixed-vertex containment corroboration; no physics."""
import json
import hashlib
import gzip
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import trimesh
import inspect_surfaces as audit

p=audit.HERE
plan=json.loads((p/'containment-protocol.json').read_text())
assert hashlib.sha256((p/'results.json').read_bytes()).hexdigest()==plan['source_results_sha256']
protocol=json.loads((p/'protocol.json').read_text())
xml=ET.parse(audit.V57/'jaw-contact-enabled/robot.xml')
model=mujoco.MjModel.from_xml_path(str(audit.V57/'jaw-contact-enabled/robot.xml'));data=mujoco.MjData(model)
results=[]
for pose in protocol['poses']:
    if pose['id']=='home':
        home=json.loads((audit.ROOT/'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad'];q=[0,0,.125,1,0,0,0,*home]
    else:
        with gzip.open(audit.ROOT/pose['source'],'rt') as stream:
            for i,line in enumerate(stream):
                if i==pose['row_index']:q=json.loads(line)['qpos'];break
        assert hashlib.sha256(np.asarray(q,dtype='<f8').tobytes()).hexdigest()==pose['qpos_sha256']
    data.qpos[:]=q;mujoco.mj_kinematics(model,data)
    world={}
    for body in xml.getroot().findall('.//body'):
        for g in body.findall('geom'):
            key=(body.get('name'),g.get('mesh'))
            if key not in {(a,b) for pair in protocol['pairs'] for a,b in [(pair[0],pair[1]),(pair[2],pair[3])]} or g.get('class')!='collision':continue
            mesh=audit.original_mesh(audit.UP/'assets'/f'{key[1]}.stl')
            assert len(trimesh.graph.connected_components(mesh.face_adjacency,nodes=np.arange(len(mesh.faces)),min_len=1))==1
            bid=model.body(key[0]).id;quat=np.array([float(v) for v in g.get('quat','1 0 0 0').split()]);quat/=np.linalg.norm(quat);rotation=np.zeros(9);mujoco.mju_quat2Mat(rotation,quat)
            rb=data.xmat[bid].reshape(3,3);rg=rb@rotation.reshape(3,3);translation=data.xpos[bid]+rb@np.array([float(v) for v in g.get('pos','0 0 0').split()]);mesh.vertices=mesh.vertices@rg.T+translation;world[key]=mesh
    for pair in protocol['pairs']:
        left,right=world[(pair[0],pair[1])],world[(pair[2],pair[3])]
        for label,source,target in [('a_in_b',left,right),('b_in_a',right,left)]:
            point=source.vertices[[0]]
            _,distance,triangle=trimesh.proximity.closest_point(target,point)
            results.append({'pose':pose['id'],'pair':pair,'direction':label,'source_vertex':0,'point_world_m':point[0].tolist(),'inside_other_three_rays':[bool(trimesh.ray.ray_util.contains_points(target.ray,point,check_direction=d)[0]) for d in plan['directions']],'distance_to_other_surface_m':float(distance[0]),'nearest_other_triangle':int(triangle[0])})
(p/'containment-results.json').write_text(json.dumps({'queries':results,'physics_steps':0,'method_frozen_before_query':True},indent=2)+'\n')
(p/'containment-manifest.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'containment_check.py',p/'containment-protocol.json',p/'containment-results.json',p/'inspect_surfaces.py',p/'results.json']},indent=2)+'\n')
print(json.dumps({'queries':len(results),'three_direction_inside_count':sum(any(r['inside_other_three_rays']) for r in results),'minimum_selected_point_clearance_m':min(r['distance_to_other_surface_m'] for r in results)}))
