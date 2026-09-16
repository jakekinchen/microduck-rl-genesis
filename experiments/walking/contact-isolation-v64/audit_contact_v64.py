"""Copied-state CAD support audit. No integration and no inferred applied forces."""
from pathlib import Path
import gzip
import hashlib
import json
import signal
import sys
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
import trimesh
from contact_v64 import SHELLS

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def rotation(quat):
    result=np.zeros(9);mujoco.mju_quat2Mat(result,np.array(quat,dtype=float))
    return result.reshape(3,3)


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
    bank=json.loads((HERE/'bank.json').read_text())
    for path,digest in bank['input_sha256'].items():
        with (ROOT/path).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest,path
    old=ROOT/bank['v63_root']
    with gzip.open(old/'runs/v62-replay-r1/physics.jsonl.gz','rt') as stream:
        trace=[json.loads(line) for line in stream]
    samples=[]
    for target in bank['geometry_audit_times_s']:
        row=min(trace,key=lambda row:abs(row['time_s']-target))
        assert abs(row['time_s']-target)<1e-8
        samples.append(row)
    model=mujoco.MjModel.from_xml_path(str(old/'runs/v62-replay-r1/scene.xml'))
    data=mujoco.MjData(model)
    xml=ET.parse(ROOT/bank['models']['v62']['robot_xml']).getroot()
    directory=Path(xml.find('compiler').get('meshdir'))
    geoms={g.get('name'):g for g in xml.findall('.//worldbody//geom')}
    meshfiles={m.get('name',Path(m.get('file','')).stem):m for m in xml.findall('.//mesh') if m.get('file')}
    names=(*bank['models']['v62']['sole_geoms'],*SHELLS)
    raw={};sources={}
    for name in names:
        geom=geoms[name];mesh=meshfiles[geom.get('mesh')]
        assert not any(mesh.get(k) for k in ('refpos','refquat','scale'))
        path=directory/mesh.get('file')
        with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        raw[name]=np.asarray(trimesh.load(path,force='mesh',process=False).vertices)
        sources[name]={'file':str(path),'sha256':digest,'vertex_count':len(raw[name])}
    output=[]
    for row in samples:
        data.qpos[:]=row['qpos_before'];data.qvel[:]=0.;mujoco.mj_forward(model,data)
        frame={'time_s':row['time_s'],'pose_time_s':row['interval_start_s'],'features':{}}
        for name in names:
            gid=model.geom(name).id;bid=model.geom_bodyid[gid];mid=model.geom_dataid[gid]
            geom=geoms[name]
            pos=np.fromstring(geom.get('pos','0 0 0'),sep=' ')
            quat=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
            body_rotation=data.xmat[bid].reshape(3,3)
            world=raw[name]@(body_rotation@rotation(quat)).T+data.xpos[bid]+body_rotation@pos
            start=model.mesh_vertadr[mid];count=model.mesh_vertnum[mid]
            compiled=model.mesh_vert[start:start+count]@data.geom_xmat[gid].reshape(3,3).T+data.geom_xpos[gid]
            minimum=float(world[:,2].min());compiled_min=float(compiled[:,2].min())
            assert abs(minimum-compiled_min)<5e-8,(name,minimum,compiled_min)
            frame['features'][name]={'source_minimum_z_m':minimum,'compiled_minimum_z_m':compiled_min,
                'support_point_m':world[np.argmin(world[:,2])].tolist(),
                'vertices_below_floor':int(np.count_nonzero(world[:,2]<0)),
                'source_compiled_support_error_m':abs(minimum-compiled_min)}
        frame['recorded_shell_contacts']=[c for c in row['contacts'] if any(model.geom(i).name in SHELLS for i in c['geom_ids'])]
        output.append(frame)
    result={'passed':True,'sources':sources,'copied_states':output,'integration_steps':0,
            'boundary':'CAD support coordinates at copied pre-integration poses; recorded forces are V63 measurements, not newly inferred forces. Convex hull and source share plane support extrema; no global mesh-fidelity claim.'}
    (HERE/'geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'copied_states':len(samples),'support_checks':len(names)*len(samples)}))


if __name__=='__main__':main()
