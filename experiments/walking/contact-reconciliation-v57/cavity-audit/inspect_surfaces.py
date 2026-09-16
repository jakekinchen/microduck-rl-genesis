#!/usr/bin/env python3
"""Original CAD triangle witnesses; never steps dynamics or repairs meshes."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import trimesh
from scipy.spatial import cKDTree, ConvexHull

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
V57=HERE.parent
UP=ROOT/'experiments/walking/upstream-audit-v56/sources/src/mjlab_microduck/robot/microduck'


def original_mesh(path):
    raw=path.read_bytes();n=int.from_bytes(raw[80:84],'little');assert len(raw)==84+n*50
    dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
    triangles=np.frombuffer(raw,dtype=dtype,offset=84)['vertices'].astype(float)
    vertices,inverse=np.unique(triangles.reshape(-1,3),axis=0,return_inverse=True)
    return trimesh.Trimesh(vertices=vertices,faces=inverse.reshape(-1,3),process=False)


def crossings(mesh_a,mesh_b):
    """Conservative proper segment/triangle crossing witnesses.

    All original edges of both triangles are tested for every AABB-overlapping
    triangle pair. Crossing endpoints must straddle the opposite plane by >10nm
    and the intersection must be inside the triangle by barycentric 1e-7.
    Coplanarity and tangency are reported as unresolved, never called clearance.
    """
    aa,bb=mesh_a.triangles,mesh_b.triangles
    tree=mesh_b.triangles_tree
    count=0;near=0;witnesses=[];pending=[]
    def batch(pairs):
        nonlocal count,near
        ai=np.array([p[0] for p in pairs]);bi=np.array([p[1] for p in pairs])
        ta,tb=aa[ai],bb[bi];count+=len(pairs)
        found=[]
        for source,target,reverse in [(ta,tb,False),(tb,ta,True)]:
            e0,e1=target[:,1]-target[:,0],target[:,2]-target[:,0]
            normal=np.cross(e0,e1);norm=np.linalg.norm(normal,axis=1)
            valid=norm>1e-18;normal=normal/np.maximum(norm[:,None],1e-300)
            xx=np.einsum('ij,ij->i',e0,e0);xy=np.einsum('ij,ij->i',e0,e1);yy=np.einsum('ij,ij->i',e1,e1)
            denominator=xx*yy-xy*xy
            for edge in range(3):
                p0,p1=source[:,edge],source[:,(edge+1)%3]
                d0=np.einsum('ij,ij->i',p0-target[:,0],normal)
                d1=np.einsum('ij,ij->i',p1-target[:,0],normal)
                near+=int(np.sum(valid & (np.abs(d0)<=1e-8) & (np.abs(d1)<=1e-8)))
                mask=valid & (denominator>1e-30) & (((d0>1e-8)&(d1<-1e-8))|((d0<-1e-8)&(d1>1e-8)))
                ids=np.flatnonzero(mask)
                if not len(ids):continue
                t=d0[ids]/(d0[ids]-d1[ids]);point=p0[ids]+t[:,None]*(p1[ids]-p0[ids]);delta=point-target[ids,0]
                ex=np.einsum('ij,ij->i',delta,e0[ids]);ey=np.einsum('ij,ij->i',delta,e1[ids])
                u=(yy[ids]*ex-xy[ids]*ey)/denominator[ids];v=(xx[ids]*ey-xy[ids]*ex)/denominator[ids]
                good=np.flatnonzero((u>1e-7)&(v>1e-7)&(u+v<1-1e-7))
                for j in good[:4]:
                    i=int(ids[j]);found.append({'triangle_a':int(ai[i]),'triangle_b':int(bi[i]),'edge_from':'b' if reverse else 'a','edge_index':edge,'intersection_world_m':point[j].tolist(),'edge_endpoints_world_m':[p0[i].tolist(),p1[i].tolist()],'opposite_plane_endpoint_distances_m':[float(d0[i]),float(d1[i])],'opposite_triangle_barycentric':[float(1-u[j]-v[j]),float(u[j]),float(v[j])],'triangle_a_world_m':ta[i].tolist(),'triangle_b_world_m':tb[i].tolist()})
        return found
    for i,triangle in enumerate(aa):
        bounds=np.r_[triangle.min(0)-1e-10,triangle.max(0)+1e-10]
        for j in sorted(tree.intersection(bounds)):
            pending.append((i,j))
        if len(pending)>=4096:
            witnesses.extend(batch(pending));pending=[]
            if witnesses:break
    completed=not witnesses
    if pending and not witnesses:witnesses.extend(batch(pending))
    return {'proper_crossing_witnesses':witnesses[:8],'aabb_triangle_pairs_tested':count,'edge_pairs_near_coplanar_count':near,'all_aabb_pairs_tested':completed,'classification':'original_triangle_surfaces_cross' if witnesses else 'no_proper_crossing_found_tangency_coplanarity_or_containment_unknown'}


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert hashlib.sha256((V57/'manifest.json').read_bytes()).hexdigest()==protocol['prior_manifest_sha256']
    manifest=json.loads((V57/'manifest.json').read_text())
    for path,digest in {**manifest['inputs'],**manifest['outputs']}.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    xml=ET.parse(V57/'jaw-contact-enabled/robot.xml')
    elements={g.get('name'):(b.get('name'),g) for b in xml.getroot().findall('.//body') for g in b.findall('geom')}
    model=mujoco.MjModel.from_xml_path(str(V57/'jaw-contact-enabled/robot.xml'));data=mujoco.MjData(model)
    local_meshes={name:original_mesh(UP/'assets'/f'{name}.stl') for pair in protocol['pairs'] for name in [pair[1],pair[3]]}
    quality={name:{'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'signed_volume_m3':float(mesh.volume),'euler_number':int(mesh.euler_number),'degenerate_faces':int(np.sum(mesh.area_faces<1e-18))} for name,mesh in local_meshes.items()}
    results=[]
    for pose in protocol['poses']:
        if pose['id']=='home':
            home=json.loads((ROOT/'microduck_contract/interface/observation-v1.json').read_text())['home_joint_position_rad'];q=[0,0,pose['root_z_m'],1,0,0,0,*home]
        else:
            with gzip.open(ROOT/pose['source'],'rt') as stream:
                for i,line in enumerate(stream):
                    if i==pose['row_index']:q=json.loads(line)['qpos'];break
            assert hashlib.sha256(np.asarray(q,dtype='<f8').tobytes()).hexdigest()==pose['qpos_sha256']
        data.qpos[:]=q;mujoco.mj_kinematics(model,data);mujoco.mj_collision(model,data)
        world={};geom_ids={};transform_errors={}
        for name,(body,g) in elements.items():
            if g.get('mesh') not in local_meshes or g.get('class') not in ['collision','self_collision_only']:continue
            b=model.body(body).id;mid=model.geom(name).id;rot=np.zeros(9);quat=np.array([float(v) for v in g.get('quat','1 0 0 0').split()]);quat/=np.linalg.norm(quat);mujoco.mju_quat2Mat(rot,quat)
            local_rotation=rot.reshape(3,3);body_rotation=data.xmat[b].reshape(3,3);rotation=body_rotation@local_rotation
            position=data.xpos[b]+body_rotation@np.array([float(v) for v in g.get('pos','0 0 0').split()])
            mesh=local_meshes[g.get('mesh')].copy();mesh.vertices=mesh.vertices@rotation.T+position;world[(body,g.get('mesh'))]=mesh;geom_ids[(body,g.get('mesh'))]=mid
            meshid=int(model.geom_dataid[mid]);start=int(model.mesh_vertadr[meshid]);n=int(model.mesh_vertnum[meshid]);compiled=model.mesh_vert[start:start+n]@data.geom_xmat[mid].reshape(3,3).T+data.geom_xpos[mid]
            transform_errors[f'{body}:{g.get("mesh")}']=float(cKDTree(mesh.vertices).query(compiled)[0].max())
        for pair in protocol['pairs']:
            left,right=(pair[0],pair[1]),(pair[2],pair[3]);ma,mb=world[left],world[right];ga,gb=geom_ids[left],geom_ids[right]
            contacts=[c for c in data.contact if {int(c.geom1),int(c.geom2)}=={ga,gb}]
            deepest=min(contacts,key=lambda c:c.dist) if contacts else None
            result={'pose':pose['id'],'pair':pair,'cad_transform_max_compiled_vertex_error_m':max(transform_errors[':'.join(left)],transform_errors[':'.join(right)]),'convex_hull_penetration_m':-float(deepest.dist) if deepest is not None else None,**crossings(ma,mb)}
            if deepest is not None:
                point=np.asarray(deepest.pos).reshape(1,3);result['convex_contact_world_m']=point[0].tolist()
                for label,mesh in [('a',ma),('b',mb)]:
                    near,distance,face=trimesh.proximity.closest_point(mesh,point)
                    result[f'convex_contact_distance_to_cad_{label}_m']=float(distance[0]);result[f'nearest_cad_{label}_point_world_m']=near[0].tolist();result[f'nearest_cad_{label}_triangle']=int(face[0])
                    hull=ConvexHull(mesh.vertices)
                    violation=float((hull.equations[:,:3]@point[0]+hull.equations[:,3]).max())
                    result[f'convex_contact_hull_{label}_maximum_halfspace_value_m']=violation
                    directions=[[.4395064455,.617598629942,.652231566745],[.811,.247,.531],[-.317,.719,.619]]
                    result[f'convex_contact_inside_original_cad_{label}_three_rays']=[bool(trimesh.ray.ray_util.contains_points(mesh.ray,point,check_direction=d)[0]) for d in directions]
                result['local_cavity_witness'] = all(result[f'convex_contact_hull_{label}_maximum_halfspace_value_m'] < -1e-8 for label in ['a','b']) and any(not any(result[f'convex_contact_inside_original_cad_{label}_three_rays']) and result[f'convex_contact_distance_to_cad_{label}_m']>1e-6 for label in ['a','b'])
            # A representative per connected surface component guards against
            # overlooking complete nesting after a no-crossing result. It is
            # separate evidence, not a claim that a handful of vertices proves
            # triangle disjointness.
            component_checks={}
            for label,mesh,other in [('a_in_b',ma,mb),('b_in_a',mb,ma)]:
                components=trimesh.graph.connected_components(mesh.face_adjacency,nodes=np.arange(len(mesh.faces)),min_len=1)
                selected=[int(component[np.argmax(mesh.area_faces[component])]) for component in components]
                points=mesh.triangles_center[selected]
                component_checks[label]={'components':len(components),'representative_triangles':selected,'representative_points_world_m':points.tolist(),'inside_other_three_rays':[[bool(x) for x in trimesh.ray.ray_util.contains_points(other.ray,points,check_direction=d)] for d in [[.4395064455,.617598629942,.652231566745],[.811,.247,.531],[-.317,.719,.619]]]}
            result['surface_component_containment_checks']=component_checks
            results.append(result);print(pose['id'],pair[1],pair[3],result['classification'],'tested',result['aabb_triangle_pairs_tested'],flush=True)
    report={'schema':'v57-original-cad-cavity-audit','physics_steps':0,'mesh_repairs_performed':False,'trimesh_version':trimesh.__version__,'mujoco_version':mujoco.__version__,'quality':quality,'results':results,'boundary':'A robust proper-crossing witness proves original triangle intersection. Absence of these conservative witnesses is not proof of clearance, containment absence, manifold Boolean intersection, or physical accuracy.'}
    (HERE/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    paths=[HERE/'protocol.json',HERE/'inspect_surfaces.py',HERE/'results.json',V57/'manifest.json']+[UP/'assets'/f'{name}.stl' for name in local_meshes]
    (HERE/'manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')


if __name__=='__main__':main()
