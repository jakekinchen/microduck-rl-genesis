"""Nominal command-only MuJoCo gait probe. No reward or policy intervention."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--policy",required=True,type=Path)
    p.add_argument("--motor-delay",type=int,default=0,choices=range(7))
    p.add_argument("--sensor-delay",type=int,default=0,choices=(0,1))
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    import numpy as np
    from experiments.laser.face_world import FaceFirstLaserWorld
    from experiments.laser.gait import GaitProbe,summarize_gait
    from microduck.laser_dynamics import domain_draw
    results=[]
    for name,command in (("forward-slow",[.12,0,0]),("forward-fast",[.25,0,0]),("turn",[0,0,.5])):
        domain=domain_draw(76510,False)
        domain["sensor_delay_steps"]=a.sensor_delay
        world=FaceFirstLaserWorld(a.policy,ROOT/".workspace/bam",domain)
        if a.motor_delay:
            controller=world.core.controller
            pending=controller.q_target.copy()
            history=[pending.copy() for _ in range(a.motor_delay)]
            original_update=controller.update
            def set_target(joint,value): pending[controller.dof_to_q_target[joint]]=value
            def update():
                history.append(pending.copy())
                controller.q_target=history.pop(0)
                original_update()
            controller.set_q_target=set_target
            controller.update=update
        world.command_for=lambda target,visible: np.array(command,np.float32)
        probe=GaitProbe(world.core)
        rows=[]
        for i in range(500):
            rows.append(probe.sample(world.step([0,0])))
            if world.fell:break
        (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        result=summarize_gait(rows)
        result["case"]=name
        result["motor_delay_physics_steps"]=a.motor_delay
        result["sensor_delay_control_steps"]=a.sensor_delay
        results.append(result)
        print(json.dumps(result),flush=True)
        world.close()
    (a.output/"audit.json").write_text(json.dumps(results,indent=2)+"\n")


if __name__=="__main__":main()
