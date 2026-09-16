"""Read-only video of retained poses; never runs or repairs a policy rollout."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np
import imageio.v2 as imageio
from PIL import Image,ImageDraw


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True)
    p.add_argument('--session',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=json.loads((a.receipt/'probe.json').read_text())
    if not result['complete']:raise ValueError('completed evaluation required')
    session=next(s for s in result['session_reports'] if s['session_id']==a.session)
    source=a.receipt/'trajectory.jsonl';source_sha=sha(source)
    model_path=a.receipt/'terrain-models'/a.session/'scene.xml'
    m=mujoco.MjModel.from_xml_path(str(model_path));d=mujoco.MjData(m)
    m.vis.global_.offwidth,m.vis.global_.offheight=720,480;m.vis.quality.offsamples=1
    renderer=mujoco.Renderer(m,height=480,width=720)
    camera=mujoco.MjvCamera();camera.distance=.6;camera.azimuth=145;camera.elevation=-18
    if a.output.exists():raise ValueError('new video output required')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    writer=imageio.get_writer(a.output,fps=25,codec='libx264',quality=7)
    frames=0;rows=0
    try:
        with source.open() as f:
            for line in f:
                r=json.loads(line)
                if r['session_id']!=a.session:continue
                rows+=1
                if rows%2==0:continue
                d.qpos[:]=r['qpos'];mujoco.mj_forward(m,d)
                camera.lookat[:]=d.qpos[:3]
                renderer.update_scene(d,camera=camera)
                frame=Image.fromarray(renderer.render());draw=ImageDraw.Draw(frame)
                draw.rectangle((0,0,720,44),fill=(16,21,30))
                draw.text((8,5),f"Recorded {result.get('candidate', a.receipt.name)} | {a.session} | {r['session_time_s']:.2f}s",fill='white')
                draw.text((8,24),f"{r['actor_mode']} | full session {'PASS' if session['passed'] else 'FAIL'} | tilt {r['tilt_deg']:.1f} deg",fill='white')
                writer.append_data(np.asarray(frame));frames+=1
    finally:
        writer.close();renderer.close()
    if not rows or sha(source)!=source_sha:raise ValueError('missing or changed source trajectory')
    receipt={'source_trajectory_sha256':source_sha,'input_manifest_sha256':sha(a.receipt/'SHA256SUMS'),
        'session_id':a.session,'source_rows':rows,'rendered_frames':frames,'fps':25,'video_sha256':sha(a.output),
        'model_scene_sha256':sha(model_path),'renderer_source_sha256':sha(__file__),
        'boundary':'Visualization of immutable recorded generalized coordinates at original speed; no physics integration, new evaluation or repaired motion.'}
    a.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
