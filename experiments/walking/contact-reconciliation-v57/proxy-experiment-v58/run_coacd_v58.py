"""Serial, one-attempt coordinator with hard native-process deadlines."""
from pathlib import Path
import os,sys,time,json,signal,subprocess,hashlib

p=Path(__file__).resolve().parent
root=p.parents[3]
protocol=json.loads((p/'protocol.json').read_text())
if (p/'attempt-started.json').exists() or (p/'generation.json').exists():raise RuntimeError('generation already attempted; no implicit rerun')
for name,digest in json.loads((p/'implementation.lock.json').read_text()).items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
for path,digest in protocol['source_sha256'].items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
def interrupted(signum,frame):
    raise InterruptedError(f'coordinator interrupted by signal {signum}')
signal.signal(signal.SIGINT,interrupted);signal.signal(signal.SIGTERM,interrupted)
with (p/'attempt-started.json').open('x') as marker:
    json.dump({'pid':os.getpid(),'start_unix':time.time(),'protocol_sha256':hashlib.sha256((p/'protocol.json').read_bytes()).hexdigest()},marker)
env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
records=[];start=time.monotonic()
def launch(script,args,timeout,log):
    with log.open('wb') as stream:
        child=None;timed_out=False
        previous_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM})
        try:
            child=subprocess.Popen([sys.executable,str(p/script),*args],stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)
            try:child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:timed_out=True
        except BaseException as error:
            (p/'interruption.json').write_text(json.dumps({'script':script,'args':args,'error':repr(error),'unix_time':time.time()},indent=2)+'\n')
            raise
        finally:
            # Block further cancellation while reaping the owned group.
            signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN)
            signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)
            try:
                if child is not None and child.poll() is None:
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=3)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            finally:
                signal.signal(signal.SIGINT,interrupted);signal.signal(signal.SIGTERM,interrupted)
        return {'exit_code':child.returncode,'timed_out':timed_out}
for name in protocol['meshes']:
    remaining=protocol['budget']['generation_total_wall_seconds']-(time.monotonic()-start)
    if remaining<=0:
        result={'mesh':name,'status':'not_started_total_budget_exhausted'}
    else:
        print(f'START {name}',flush=True);t=time.monotonic()
        result={'mesh':name,**launch('coacd_worker_v58.py',[name],min(remaining,protocol['budget']['per_mesh_wall_seconds']),p/f'{name}.log')}
        result['elapsed_seconds']=time.monotonic()-t
        file=p/'outputs'/name/'complete.json'
        result['complete_artifact_present']=file.exists()
        if file.exists():result['artifact']=json.loads(file.read_text())
        print('END '+json.dumps(result),flush=True)
    records.append(result)
    (p/'generation.json').write_text(json.dumps({'attempts':records,'complete':len(records)==4,'elapsed_seconds':time.monotonic()-start,'omp2_is_effective_native_thread_cap':False},indent=2)+'\n')
print('START independent geometry validation',flush=True)
t=time.monotonic();validation=launch('validate_proxy_v58.py',[],protocol['budget']['validation_wall_seconds'],p/'validation.log');validation['elapsed_seconds']=time.monotonic()-t
(p/'validation-process.json').write_text(json.dumps(validation,indent=2)+'\n');print('END validation '+json.dumps(validation),flush=True)
