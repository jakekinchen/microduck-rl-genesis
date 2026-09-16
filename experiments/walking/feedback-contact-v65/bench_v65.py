"""Static construction and metrics for an explicitly guided CAD ankle-load drop."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import mujoco
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
GEOM_FIELDS=('solref','solimp','friction','priority','solmix','condim','margin','gap')
OPTIONS=('integrator','solver','cone','iterations','tolerance','ls_iterations',
         'ls_tolerance','disableflags','enableflags','ccd_iterations','ccd_tolerance')


def load(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def fmt(a):return ' '.join(format(float(v),'.17g') for v in np.atleast_1d(a))
def rotation(q):
    r=np.empty(9);mujoco.mju_quat2Mat(r,np.asarray(q,dtype=float));return r.reshape(3,3)
def quat(r):
    q=np.empty(4);mujoco.mju_mat2Quat(q,np.asarray(r).ravel());return q
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def mesh_arrays(m,gid):
    mid=m.geom_dataid[gid]
    start=m.mesh_vertadr[mid];n=m.mesh_vertnum[mid]
    face=m.mesh_faceadr[mid];nf=m.mesh_facenum[mid]
    return m.mesh_vert[start:start+n].copy(),m.mesh_face[face:face+nf].copy()


def source_asset(path,geomname):
    xml=ET.parse(path).getroot()
    geom=next(g for g in xml.findall('.//worldbody//geom') if g.get('name')==geomname)
    asset=next(m for m in xml.findall('.//asset/mesh') if m.get('name',Path(m.get('file','')).stem)==geom.get('mesh'))
    assert not any(asset.get(k) for k in ('refpos','refquat','scale'))
    directory=(path.parent/xml.find('compiler').get('meshdir')).resolve()
    return geom,(directory/asset.get('file')).resolve()


def build_static(bank,out):
    import trimesh
    from scipy.spatial import cKDTree
    reference=ROOT/bank['v64_root']/'runs/v11-replay-base-r1'
    model=mujoco.MjModel.from_xml_path(str(reference/'scene.xml'))
    d=mujoco.MjData(model)
    with np.load(reference/'initial-state.npz') as state:d.qpos[:]=state['qpos']
    mujoco.mj_fwdPosition(model,d)
    models={v:mujoco.MjModel.from_xml_path(str(ROOT/bank['v64_root']/'runs'/f'{v}-replay-base-r1/scene.xml')) for v in bank['models']}
    checks={}
    for foot,refname in zip(('left','right'),bank['models']['v11']['sole_geoms']):
        gid=model.geom(refname).id;bid=model.geom_bodyid[gid]
        rg,refasset=source_asset(ROOT/bank['models']['v11']['robot_xml'],refname)
        body_rotation=d.xmat[bid].reshape(3,3)
        localpos=np.fromstring(rg.get('pos','0 0 0'),sep=' ')
        localquat=np.fromstring(rg.get('quat','1 0 0 0'),sep=' ')
        pose_rotation=body_rotation@rotation(localquat)
        pose_position=body_rotation@localpos
        rawref=np.asarray(trimesh.load(refasset,force='mesh',process=False).vertices)
        origin_z=.005-float((rawref@pose_rotation.T+pose_position)[:,2].min())
        for variant in bank['models']:
            name=bank['models'][variant]['sole_geoms'][('left','right').index(foot)]
            _,asset=source_asset(ROOT/bank['models'][variant]['robot_xml'],name)
            xml=ET.Element('mujoco',model=f'v65_{variant}_{foot}_guided_ankle_drop')
            ET.SubElement(xml,'compiler',angle='radian',inertiafromgeom='false')
            ET.SubElement(xml,'option',timestep='.005',gravity=fmt(model.opt.gravity),
                integrator='Euler',solver='Newton',cone='pyramidal',iterations=str(model.opt.iterations),
                tolerance=str(model.opt.tolerance),ls_iterations=str(model.opt.ls_iterations),
                ls_tolerance=str(model.opt.ls_tolerance),ccd_iterations=str(model.opt.ccd_iterations),
                ccd_tolerance=str(model.opt.ccd_tolerance))
            assets=ET.SubElement(xml,'asset');ET.SubElement(assets,'mesh',name='sole_mesh',file=str(asset))
            world=ET.SubElement(xml,'worldbody')
            floor=ET.SubElement(world,'geom',name='floor',type='plane',size='0 0 .05',pos='0 0 0')
            body=ET.SubElement(world,'body',name='ankle_load',pos=fmt([0,0,origin_z]))
            ET.SubElement(body,'joint',name='vertical_guide',type='slide',axis='0 0 1',limited='false',damping='0',frictionloss='0',armature='0')
            ET.SubElement(body,'inertial',mass=fmt(model.body_mass[bid]),pos=fmt(body_rotation@model.body_ipos[bid]),
                quat=fmt(quat(body_rotation@rotation(model.body_iquat[bid]))),diaginertia=fmt(model.body_inertia[bid]))
            sole=ET.SubElement(body,'geom',name='sole',type='mesh',mesh='sole_mesh',
                pos=fmt(pose_position),quat=fmt(quat(pose_rotation)))
            for element,oldid in ((floor,model.geom('floor').id),(sole,gid)):
                element.set('contype','1');element.set('conaffinity','1')
                for field in GEOM_FIELDS:
                    value=getattr(model,'geom_'+field)[oldid]
                    element.set(field,str(int(value)) if field in ('priority','condim') else fmt(value))
            path=out/f'{variant}-{foot}.xml';path.write_text(ET.tostring(xml,encoding='unicode')+'\n')
            m=mujoco.MjModel.from_xml_path(str(path));data=mujoco.MjData(m);mujoco.mj_fwdPosition(m,data)
            assert (m.nq,m.nv,m.nu,m.ngeom,m.npair,m.nexclude)==(1,1,0,2,0,0)
            assert not m.dof_damping.any() and not m.dof_frictionloss.any() and not m.dof_armature.any()
            for option in OPTIONS:assert getattr(m.opt,option)==getattr(model.opt,option),option
            mid=m.geom('sole').id;verts,faces=mesh_arrays(m,mid)
            sourceverts,sourcefaces=mesh_arrays(models[variant],models[variant].geom(name).id)
            np.testing.assert_array_equal(verts,sourceverts);np.testing.assert_array_equal(faces,sourcefaces)
            compiled=verts@data.geom_xmat[mid].reshape(3,3).T+data.geom_xpos[mid]
            raw=np.asarray(trimesh.load(asset,force='mesh',process=False).vertices)
            expected=raw@pose_rotation.T+pose_position+np.array([0,0,origin_z])
            error=float(max(cKDTree(expected).query(compiled)[0].max(),cKDTree(compiled).query(expected)[0].max()))
            assert error<=1e-7 and abs(compiled[:,2].min()-.005)<=1e-7
            check={'static_passed':True,'asset':str(asset),'asset_sha256':sha(asset),'source_geom':name,
                'source_compiled_mesh_arrays_exact':True,'vertices':len(verts),'faces':len(faces),
                'cad_compiled_vertex_error_m':error,'clearance_m':float(compiled[:,2].min()),
                'mass_kg':float(m.body_mass[1]),'body_inertia':m.body_inertia[1].tolist(),
                'body_ipos':m.body_ipos[1].tolist(),'body_iquat':m.body_iquat[1].tolist(),
                'reference_body':model.body(bid).name,'body_pos':m.body_pos[1].tolist(),
                'options':{key:getattr(m.opt,key) for key in OPTIONS},
                'contact_parameters':{field:getattr(m,'geom_'+field).tolist() for field in GEOM_FIELDS},
                'integration_steps':0}
            checks[f'{variant}-{foot}']=check
        a=checks[f'v11-{foot}'];b=checks[f'v62-{foot}']
        for key in ('mass_kg','body_inertia','body_ipos','body_iquat','body_pos','options','contact_parameters'):
            assert a[key]==b[key],key
    return {'static_passed':True,'models':checks,'integration_steps':0,
        'boundary':'Isolated CAD ankle mass on a vertical guide; no articulated load sharing, BAM or physical calibration.'}


def bench_metrics(rows,mass,duration,dt):
    count=round(duration/dt);failures=[]
    if len(rows)!=count:failures.append('incomplete_duration')
    if not rows:return {'passed':False,'failures':failures+['missing_evidence']}
    impulse=sum(r['contact_force_z_n']*dt for r in rows)
    balance=mass*(rows[-1]['velocity_m_s']-rows[0]['velocity_before_m_s'])+mass*9.81*len(rows)*dt
    residual=abs(impulse-balance)
    peak=max(r['penetration_m'] for r in rows)
    tail=[r for r in rows if r['time_s']>duration-.2+1e-9]
    maxspeed=max((abs(r['velocity_m_s']) for r in tail),default=None)
    if peak>.003:failures.append('ground_penetration')
    if len(tail)!=round(.2/dt) or maxspeed is None or maxspeed>.02:failures.append('not_settled')
    if residual>1e-8:failures.append('momentum_balance')
    if any(r['warnings'] for r in rows):failures.append('mujoco_warning')
    return {'passed':not failures,'failures':failures,'completed':len(rows)==count,
        'physics_samples':len(rows),'peak_penetration_m':peak,'normal_impulse_ns':impulse,
        'momentum_balance_ns':balance,'momentum_residual_ns':residual,'final_tail_max_speed_m_s':maxspeed,
        'first_loaded_impact_s':next((r['interval_start_s'] for r in rows if r['normal_load_n']>1e-8),None),
        'physical_acceptance':False,'walking_accepted':False}
