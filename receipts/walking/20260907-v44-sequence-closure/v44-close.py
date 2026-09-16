from pathlib import Path
import json,shutil,hashlib
ROOT=Path.cwd()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def verify(folder):
 count=0
 for line in (folder/'SHA256SUMS').read_text().splitlines():
  expected,name=line.split('  ',1);path=(folder/name).resolve()
  assert path.is_relative_to(folder.resolve()) and sha(path)==expected,str(path)
  count+=1
 return count
out=ROOT/'receipts/walking/20260907-v44-sequence-closure';out.mkdir(exist_ok=False)
folders=[ROOT/'receipts/walking'/name for name in ['20260907-v44-sequence-conformance','20260907-v44-sequence-flat','20260907-v44-sequence-repeated','20260907-v44-sequence-endurance','20260907-v44-sequence-surfaces','20260907-v44-sequence-verification','20260907-v44-gate-review']]
folders.append(ROOT/'outputs/walking-sequence-v44')
manifests={str(p.relative_to(ROOT)):dict(files=verify(p),sha256=sha(p/'SHA256SUMS')) for p in folders}
freezes={}
for path in sorted((ROOT/'experiments/walking').glob('native-sequence*freeze-v44*.json')):
 r=json.loads(path.read_text())
 for name,digest in r['source_sha256'].items():assert sha(ROOT/name)==digest,name
 freezes[path.name]=sha(path)
 dest=out/'freezes'/path.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(path,dest)
for name in ['.workspace/v44-final-prepare.json','.workspace/v44-final-activity.json','.workspace/v44-focused-tests.log','.workspace/v44-workspace-verification-r2.log','.workspace/v44-smoke.log','.workspace/v44-training.log','.workspace/v44-evidence-verification.log','.workspace/v44-analysis.log','.workspace/v44-video.log','.workspace/v44-flat.log','.workspace/v44-repeated.log','.workspace/v44-endurance.log','.workspace/v44-surfaces.log','.workspace/v44-conformance.log']:
 dest=out/'logs'/Path(name).name;dest.parent.mkdir(exist_ok=True);shutil.copy2(ROOT/name,dest)
for name in ['GOAL.md','TRAINING_ACTUALIZATION.md','docs/workspace/ACTIVE_EXPERIMENT.md','docs/workspace/active-experiment.json','experiments/walking/SEQUENCE-RESULTS-v44.md','scripts/verify_native_sequence_v44.py','scripts/analyze_native_sequence_v44.py','scripts/evaluate_native_sequence_flat_v44_r2.py','scripts/evaluate_native_sequence_surfaces_v44_r2.py','experiment_ops/activity.py','duck_workspace/core.py','tests/test_experiment_ops.py','tests/test_duck_workspace.py','tests/test_sequence_actor_v44.py']:
 dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
for path in (ROOT/'outputs/walking-sequence-v44').iterdir():
 if path.is_file():
  dest=out/'visuals'/path.name;dest.parent.mkdir(exist_ok=True);dest.hardlink_to(path)
video=json.loads((ROOT/'outputs/walking-sequence-v44/rejected-composition.json').read_text())
assert sha(ROOT/'outputs/walking-sequence-v44/rejected-composition.mp4')==video['video_sha256']
prepare=json.loads((ROOT/'.workspace/v44-final-prepare.json').read_text())
assert prepare['ready_for_diagnosis'] and not prepare['errors'] and not prepare['active_training_records']
activity=json.loads((ROOT/'.workspace/v44-final-activity.json').read_text());assert not activity['processes'] and activity['status']=='no_known_training_process'
assert not list((ROOT/'receipts/walking').glob('*v44*fresh*'))
summary=dict(complete=True,candidate_rejected=True,retained_pair='V21 walking / V15 standing / V30 controller',
 required_banks=dict(flat='0/63',diagnostic='0/4',surfaces='0/14'),fresh_sequence_bank_evaluated=False,
 physical_calibration=False,local_compute_finished=True,workspace_tests=139,focused_tests=2,
 receipt_manifests=manifests,source_freezes=freezes,active_case_verified=True,
 next_step='Freeze an exposed component-isolation bank before another retention-constrained correction.')
(out/'closure.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copy2(__file__,out/'v44-close.py')
(out/'SHA256SUMS').write_text(''.join(f'{sha(f)}  {f.relative_to(out)}\n' for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))
print(json.dumps(dict(complete=True,verified_files=verify(out),manifest_sha256=sha(out/'SHA256SUMS'))))
