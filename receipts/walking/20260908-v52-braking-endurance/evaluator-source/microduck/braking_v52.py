"""61D state-conditioned transient residual; V50/V15 base actors stay fixed."""
from pathlib import Path
import json
import numpy as np
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'logs/braking-distill-20260908-v52'

class BrakeNet(nn.Module):
    def __init__(self,mean,std):
        super().__init__();self.register_buffer('mean',mean);self.register_buffer('scale',std.clamp_min(.05))
        self.net=nn.Sequential(nn.Linear(61,64),nn.ELU(),nn.Linear(64,64),nn.ELU(),nn.Linear(64,14))
        nn.init.zeros_(self.net[-1].weight);nn.init.zeros_(self.net[-1].bias)
    def forward(self,obs):return self.net((obs-self.mean)/self.scale)

class BrakeController:
    def __init__(self,session):self.session,self.previous_moving,self.age=session,False,125
    @property
    def active(self):return self.age<125
    def prepare(self,command):
        moving=bool(np.any(command))
        self.age=0 if self.previous_moving and not moving else self.age+1
        if moving:self.age=125
        self.previous_moving=moving
    def delta(self,obs):
        return self.session.run(None,{self.session.get_inputs()[0].name:obs})[0] if self.active else np.zeros((len(obs),14),np.float32)

class Actor:
    def __init__(self,base,brake):self.base,self.brake=base,brake
    def infer(self,obs):
        action,latency=self.base.infer(obs)
        return (action+self.brake.delta(obs)).astype(np.float32),latency

def install(world):
    import onnxruntime as ort
    from experiments.walking.recovery_v49 import digest
    r=json.loads((RUN/'run.json').read_text());assert r['status']=='completed' and r['steps']==2000
    assert digest(RUN/'policy.onnx')==r['policy_sha256']
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    brake=BrakeController(ort.InferenceSession(str(RUN/'policy.onnx'),sess_options=options,providers=['CPUExecutionProvider']))
    world.walking_policy=Actor(world.walking_policy,brake);world.standing_policy=Actor(world.standing_policy,brake)
    old=world.step_command
    def step(command,*args,**kwargs):
        brake.prepare(command);return old(command,*args,**kwargs)
    world.step_command=step;world.brake_v52=brake
    return brake

def retain(folder):
    import shutil
    dest=folder/'braking';dest.mkdir()
    for name in ['run.json','policy.onnx','model.pt']:shutil.copy2(RUN/name,dest/name)
