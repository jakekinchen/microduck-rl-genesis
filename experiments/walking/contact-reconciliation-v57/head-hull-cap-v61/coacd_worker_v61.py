"""One native CoACD attempt. Parent enforces wall-clock termination."""
from pathlib import Path
import signal
signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGINT,signal.SIGTERM})
import sys,time,json,hashlib
import numpy as np
import coacd

p=Path(__file__).resolve().parent
root=p.parents[3]
protocol=json.loads((p/'protocol.json').read_text())
name=sys.argv[1];assert name in protocol['meshes']
source=root/'experiments/walking/upstream-audit-v56/sources/src/mjlab_microduck/robot/microduck/assets'/f'{name}.stl'
assert hashlib.sha256(source.read_bytes()).hexdigest()==protocol['source_sha256'][source.relative_to(root).as_posix()]
raw=source.read_bytes();n=int.from_bytes(raw[80:84],'little');assert len(raw)==84+n*50
dtype=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
v,ind=np.unique(np.frombuffer(raw,dtype=dtype,offset=84)['vertices'].reshape(-1,3).astype(float),axis=0,return_inverse=True)
start=time.monotonic()
parts=coacd.run_coacd(coacd.Mesh(v,ind.reshape(-1,3)),**protocol['params'])
elapsed=time.monotonic()-start
out=p/'outputs'/name;out.mkdir(parents=True,exist_ok=True)
arrays={}
for i,(vertices,faces) in enumerate(parts):
    arrays[f'v{i:03}']=vertices;arrays[f'f{i:03}']=faces
with (out/'parts.npz.tmp').open('wb') as stream:np.savez_compressed(stream,**arrays)
(out/'parts.npz.tmp').rename(out/'parts.npz')
(out/'complete.json').write_text(json.dumps({'mesh':name,'parts':len(parts),'part_vertices':[len(x[0]) for x in parts],'part_faces':[len(x[1]) for x in parts],'native_seconds':elapsed,'parts_sha256':hashlib.sha256((out/'parts.npz').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(raw).hexdigest()},indent=2)+'\n')
print(json.dumps({'mesh':name,'parts':len(parts),'elapsed':elapsed}),flush=True)
