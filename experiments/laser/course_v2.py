"""Extend the moving dot beyond the final solid gate; unchanged motor adapter."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from experiments.laser.course_v1 import (CourseWorld,navigation_command,obstacle_contacts,
    path_y,DURATION,MOVE_START,MOVE_END,materialize_course as materialize_v1)

STATIONS=[.6,1.8,2.4,3.,4.2,4.65,4.95]

def laser_target(t,mirror=1):
    x=.30+5.10*np.clip((t-MOVE_START)/(MOVE_END-MOVE_START),0,1)
    return np.array([x,path_y(x,mirror)]), MOVE_START<=t<MOVE_END

def materialize_course(destination,mirror=1):
    scene=materialize_v1(destination,mirror)
    root=ET.parse(scene).getroot()
    # Only relocate decorative finish paint; physical obstacles are unchanged.
    for geom in root.findall('./worldbody/geom'):
        if geom.get('name','').startswith('stage_finish_'):
            pos=geom.get('pos').split();pos[0]='4.95';geom.set('pos',' '.join(pos))
    ET.indent(root);Path(scene).write_text(ET.tostring(root,encoding='unicode')+'\n')
    return scene
