"""Multiple camera views of immutable, physics-integrated course recordings."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
import imageio.v2 as imageio
from PIL import Image,ImageDraw,ImageFont

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',action='store_true');p.add_argument('--preview-only',action='store_true');p.add_argument('--azimuth',type=float);p.add_argument('--preview-seconds',type=float,default=8);a=p.parse_args()
    if a.output.exists():raise ValueError('fresh output required')
    for line in (a.receipt/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split(maxsplit=1)
        if sha(a.receipt/name)!=digest:raise ValueError('receipt manifest mismatch: '+name)
    source=a.receipt/'motion.npz';before=sha(source)
    data=np.load(source);result=json.loads((a.receipt/'evaluation.json').read_text())
    m=mujoco.MjModel.from_xml_path(str(a.receipt/'model/scene.xml'));d=mujoco.MjData(m)
    m.vis.global_.offwidth=1280;m.vis.global_.offheight=720;m.vis.quality.offsamples=4
    # Render-model lighting only; recorded dynamics and geometry stay immutable.
    m.vis.headlight.ambient[:]=[.42,.46,.54]
    m.vis.headlight.diffuse[:]=[.85,.88,.95]
    renderer=mujoco.Renderer(m,height=720,width=1280)
    camera=mujoco.MjvCamera()
    font='/System/Library/Fonts/Avenir Next.ttc'
    big=ImageFont.truetype(font,22,index=0);small=ImageFont.truetype(font,15,index=7)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    writer=None if a.preview_only else imageio.get_writer(a.output,fps=25,codec='libx264',quality=8,ffmpeg_params=['-movflags','+faststart'])
    frames=0;cuts=[]
    try:
        indices=[min(len(data['qpos'])-1,round(a.preview_seconds*50))] if a.preview_only else range(0,len(data['qpos']),2)
        for i in indices:
            t=(i+1)*.02
            d.qpos[:]=data['qpos'][i];d.qvel[:]=data['qvel'][i]
            mujoco.mj_forward(m,d)
            pos=d.qpos[:3];target=data['target'][i]
            if a.reference or t<3:
                shot='COURSE WIDE';camera.lookat[:]=[2.25,0,.10];camera.distance=5.7;camera.azimuth=90;camera.elevation=-52
            elif t<16:
                shot='LOW TRACKING';camera.lookat[:]=pos+[.15,0,.045];camera.distance=.95;camera.azimuth=270;camera.elevation=-25
            elif t<29:
                shot='GATE APPROACH';camera.lookat[:]=pos+[.20,0,.07];camera.distance=1.3;camera.azimuth=75;camera.elevation=-34
            elif t<35:
                shot='OVERHEAD';camera.lookat[:]=pos+[.25,0,0];camera.distance=2.0;camera.azimuth=90;camera.elevation=-77
            elif t<46:
                shot='THREE QUARTER';camera.lookat[:]=pos+[.20,0,.07];camera.distance=1.15;camera.azimuth=285;camera.elevation=-30
            elif t<56:
                shot='CHICANE';camera.lookat[:]=pos+[.20,0,.07];camera.distance=1.4;camera.azimuth=105;camera.elevation=-38
            else:
                shot='FINISH';camera.lookat[:]=pos+[.12,0,.04];camera.distance=1.2;camera.azimuth=75;camera.elevation=-32
            if a.azimuth is not None:camera.azimuth=a.azimuth
            if not cuts or cuts[-1]['shot']!=shot:cuts.append({'frame':frames,'time_s':t,'shot':shot})
            renderer.update_scene(d,camera=camera)
            sc=renderer.scene
            if data['visible'][i]:
                for radius,alpha,z in [(.018,.18,.002),(.009,1.,.004)]:
                    g=sc.geoms[sc.ngeom]
                    mujoco.mjv_initGeom(g,mujoco.mjtGeom.mjGEOM_SPHERE,np.array([radius,radius,.002]),np.r_[target,z],np.eye(3).ravel(),np.array([1.,.025,.06,alpha]))
                    g.emission=1.;sc.ngeom+=1
            frame=Image.fromarray(renderer.render());draw=ImageDraw.Draw(frame)
            draw.rectangle((0,0,1280,48),fill='#071826')
            draw.text((24,10),'MICRODUCK  /  NIGHT SHIFT',font=big,fill='#efc847')
            gate_checks=result.get('course',{}).get('gate_crossings',[])
            validated=result['passed'] and len(gate_checks)==2 and all(g['cleared'] and g['crossing_time_s'] is not None for g in gate_checks)
            status='LOCAL COURSE PASS' if validated else 'DEVELOPMENT RUN · NOT ACCEPTED'
            draw.text((735,14),f'{status}   {t:05.2f}s',font=small,fill='#d2e5ed')
            draw.rectangle((0,688,1280,720),fill='#071826')
            draw.text((24,695),'Recorded physics · V21 walker / V15 stander · Moving coordinate laser · Real-time playback',font=small,fill='#abc4d3')
            draw.text((1080,695),shot,font=small,fill='#efc847')
            if a.preview_only:frame.save(a.output)
            else:writer.append_data(np.asarray(frame))
            frames+=1
            if frames%250==0:print(json.dumps({'frames':frames,'time_s':t,'shot':shot}),flush=True)
    finally:
        if writer:writer.close()
        renderer.close()
    if sha(source)!=before:raise ValueError('recorded motion changed')
    receipt={'source_motion_sha256':before,'source_receipt':str(a.receipt),'output_sha256':sha(a.output),'frames':frames,'fps':25,'cuts':cuts,
             'original_speed':True,'generated_robot_frames':False,'physics_integration_in_renderer':False,
             'boundary':'Render-only views of the same recorded continuous simulation; no motion edits. Physical transfer unvalidated.'}
    a.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
