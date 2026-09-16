"""Directed dot navigation using the retained motor policies; no pose assistance."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from experiments.walking.terrain_v23 import TerrainWorld
from experiments.walking.collision_model import model_documents
from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
from microduck.heading_servo import imu_heading

DURATION = 66.
MOVE_START, MOVE_END = 1., 61.
STATIONS = [.6, 1.8, 2.4, 3., 4.2, 4.5]

def path_y(x, mirror=1):
    return mirror*.28*math.sin(2*math.pi*x/2.4)

def laser_target(t, mirror=1):
    x=.30+4.50*np.clip((t-MOVE_START)/(MOVE_END-MOVE_START),0,1)
    return np.array([x,path_y(x,mirror)]), MOVE_START <= t < MOVE_END

def navigation_command(target, position, quaternion, visible):
    if not visible:
        return np.zeros(3,np.float32)
    delta=np.asarray(target,float)-np.asarray(position,float)
    if delta.shape!=(2,) or not np.isfinite(delta).all():
        raise ValueError('finite target and position required')
    heading=imu_heading(quaternion)
    error=math.atan2(math.sin(math.atan2(delta[1],delta[0])-heading),
                     math.cos(math.atan2(delta[1],delta[0])-heading))
    distance=float(np.linalg.norm(delta))
    forward=float(np.clip(.45*(distance-.16),0,.12))*max(0.,math.cos(error))
    if abs(error)>1.05: forward=0.
    return np.array([forward,0,np.clip(1.6*error,-.65,.65)],np.float32)

def materialize_course(destination, mirror=1):
    destination=Path(destination)
    docs=model_documents(destination)
    scene=ET.fromstring(docs['scene.xml'])
    body=scene.find('worldbody')
    for light in list(body.findall('light')):body.remove(light)
    visual=scene.find('visual')
    visual.find('headlight').set('ambient','.22 .25 .32')
    visual.find('headlight').set('diffuse','.50 .54 .62')
    ET.SubElement(visual,'quality',shadowsize='4096',offsamples='4')
    asset=scene.find('asset')
    tex=asset.find("texture[@name='groundplane']")
    tex.set('rgb1','.045 .075 .105');tex.set('rgb2','.055 .088 .115')
    tex.set('markrgb','.08 .13 .17')
    asset.find("material[@name='groundplane']").set('reflectance','.08')
    sky=asset.find("texture[@type='skybox']")
    sky.set('rgb1','.025 .045 .085');sky.set('rgb2','.004 .008 .02')
    for name,rgb,emission in [('ice','.15 .85 .95 1','.65'),('gold','.98 .65 .16 1','.25'),('pink','.78 .23 .65 1','.6'),('wall','.11 .15 .21 1','0')]:
        ET.SubElement(asset,'material',name='course_'+name,rgba=rgb,emission=emission,specular='.35',shininess='.6')
    for i,(x,y) in enumerate([(0,-2),(2.4,2),(4.8,-2)]):
        ET.SubElement(body,'light',name=f'course_key_{i}',pos=f'{x} {y} 3',dir='0 0 -1',diffuse='.65 .73 .85',specular='.35 .4 .5',castshadow='true')
    def box(name,pos,size,material,collision=True):
        ET.SubElement(body,'geom',name=name,type='box',pos=' '.join(map(str,pos)),size=' '.join(map(str,size)),material='course_'+material,
                      contype='1' if collision else '0',conaffinity='1' if collision else '0',friction='1 .005 .0001')
    for i,x in enumerate([.6,1.8,3.,4.2]):
        side=-1 if i%2==0 else 1
        y=mirror*side*.25
        box(f'course_barrier_{i}',[x,y,.16],[.10,.24,.16],'wall')
        box(f'stage_barrier_cap_{i}',[x,y,.321],[.102,.242,.004],'gold',False)
    for i,x in enumerate([2.4,4.65]):
        cy=path_y(x,mirror)
        for j,s in enumerate([-1,1]):
            box(f'course_gate_{i}_post_{j}',[x,cy+s*.46,.23],[.045,.045,.23],'wall')
            box(f'stage_gate_{i}_light_{j}',[x-.047,cy+s*.46,.25],[.003,.025,.19],'ice' if i==0 else 'pink',False)
        box(f'course_gate_{i}_beam',[x,cy,.49],[.045,.505,.03],'wall')
        box(f'stage_gate_{i}_light',[x-.047,cy,.489],[.003,.50,.016],'ice' if i==0 else 'pink',False)
    for s in [-1,1]:
        box(f'course_wall_{s}',[2.4,s*.85,.075],[3.15,.035,.075],'wall')
        box(f'stage_rail_{s}',[2.4,s*.845,.152],[3.15,.018,.003],'ice',False)
    for x in np.arange(-.4,5.61,.3):
        for s in [-1,1]:box(f'stage_dash_{x:.2f}_{s}',[x,s*.74,.0006],[.045,.012,.0004],'gold',False)
    for i in range(10):
        box(f'stage_finish_{i}',[4.50,-.68+i*.136,.001],[.025,.042,.0004],'ice' if i%2==0 else 'gold',False)
    # Distant scenic fins are explicitly non-colliding and outside the arena.
    for i in range(16):
        box(f'stage_backdrop_{i}',[-1+i*.45,2.5,.45+(i%4)*.13],[.12,.08,.45+(i%4)*.13],'wall',False)
    ET.indent(scene)
    docs['scene.xml']=ET.tostring(scene,encoding='unicode')+'\n'
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in docs.items():(destination/name).write_text(data)
    return destination/'scene.xml'

class CourseWorld(TerrainWorld):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.heading_servo=Float32HeadingHeadroomServo()
        # The walkable support is the plane. Overhead beams are obstacles,
        # not a heightfield under the robot. Every obstacle is checked separately.
        self.ground.boxes=[]
        self.ground.box_pos=np.zeros((0,3));self.ground.box_size=np.zeros((0,3))
        self.obstacles={i for i in range(self.core.model.ngeom) if self.core.model.geom(i).name.startswith('course_')}

def obstacle_contacts(model,data,obstacles):
    maximum_load=maximum_depth=0.
    names=set()
    for i,c in enumerate(data.contact):
        pair=[int(c.geom1),int(c.geom2)]
        if not any(g in obstacles for g in pair) or not any(model.geom_bodyid[g]!=0 for g in pair):continue
        force=np.zeros(6);mujoco.mj_contactForce(model,data,i,force)
        maximum_load=max(maximum_load,max(0.,float(force[0])))
        maximum_depth=max(maximum_depth,max(0.,-float(c.dist)))
        names.update(model.geom(g).name for g in pair if g in obstacles)
    return {'maximum_load_n':maximum_load,'maximum_penetration_m':maximum_depth,'obstacles':sorted(names)}
