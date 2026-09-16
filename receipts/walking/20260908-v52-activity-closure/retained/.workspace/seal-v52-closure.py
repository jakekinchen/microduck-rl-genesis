from pathlib import Path
import json,shutil,sys
from datetime import datetime,timezone
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import digest,manifest,seal
out=ROOT/'outputs/walking-braking-v52'
shutil.copy2(ROOT/'scripts/render_compressed_surface_receipt.py',out/'render-source.py')
seal(out);manifest(out)
dest=ROOT/'receipts/walking/20260908-v52-activity-closure';dest.mkdir(exist_ok=False)
refs={}
for name in ['20260908-v51-recovery-capture','20260908-v51-recovery-comparisons','20260908-v51-recovery-search',*[f'20260908-v52-braking-{bank}' for bank in ['flat','repeated','endurance','surfaces']]]:
 p=ROOT/'receipts/walking'/name;count=manifest(p);refs[str(p.relative_to(ROOT))]={'manifest_sha256':digest(p/'SHA256SUMS'),'verified_files':count}
for p in [ROOT/'logs/braking-distill-20260908-v52',ROOT/'experiments/walking/braking-replay-v52',out]:refs[str(p.relative_to(ROOT))]={'manifest_sha256':digest(p/'SHA256SUMS'),'verified_files':manifest(p)}
paths=['GOAL.md','TRAINING_ACTUALIZATION.md','docs/workspace/ACTIVE_EXPERIMENT.md','docs/workspace/active-experiment.json','experiments/walking/BRAKING-RESULTS-v52.md','experiments/walking/BRAKING-FEASIBILITY-v51.md','experiments/walking/BRAKING-DISTILLATION-v52.md','experiment_ops/activity.py','tests/test_experiment_ops.py','duck_workspace/core.py','tests/test_braking_v51.py','tests/test_braking_v52.py','.workspace/verify-v51.py','.workspace/v51-verification.json','.workspace/v51-verification.log','.workspace/audit-braking-v52.py','.workspace/finish-v52.py','.workspace/seal-v52-closure.py','.workspace/v52-audit.log','.workspace/v52-workspace-tests.log','.workspace/v52-focused-tests.log','.workspace/v52-training.log','.workspace/v52-render.log','.workspace/v52-final-prepare.json','.workspace/v52-final-doctor.json','.workspace/v52-final-status.txt','.workspace/v52-final-guard.json']
paths += [str(p.relative_to(ROOT)) for p in (ROOT/'experiments/walking').glob('braking-*freeze-v52.json')]+['experiments/walking/recovery-freeze-v51.json']
paths += [f'.workspace/v52-{bank}{suffix}' for bank in ['flat','repeated','endurance','surfaces'] for suffix in ['.log','-guard.json']]
for name in paths:
 p=ROOT/name;target=dest/'retained'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
verification=json.loads((out/'verification.json').read_text());prepare=json.loads((ROOT/'.workspace/v52-final-prepare.json').read_text());doctor=json.loads((ROOT/'.workspace/v52-final-doctor.json').read_text());guard=json.loads((ROOT/'.workspace/v52-final-guard.json').read_text())
assert verification['passed'] and not verification['behavior_accepted'] and prepare['ready_for_diagnosis'] and not prepare['errors'] and doctor['ready_for_evaluator_setup'] and not guard['processes']
result=dict(schema='microduck.activity-closure/v1',completed_at=datetime.now(timezone.utc).isoformat(),activity_complete=True,behavior_accepted=False,candidate_promoted=False,policy_activated=False,held_out_opened=False,new_rl_transitions=0,supervised_updates=2000,all_evaluations_complete=True,downhill_sessions_survived=2,downhill_sessions_passed=0,flat_passed=38,flat_total=63,endurance_passed=0,endurance_total=2,surface_passed=3,surface_total=14,verified_controls=73242,exact_prebraking_prefix_controls=36952,workspace_tests_passed=140,focused_tests_passed=4,source_receipts=refs,retained_controller='Original V21 walking / V15 standing with V30 command controller',next_step='Freeze retention-constrained braking: successful-stop zero-label fitting and verified corrections on learner-visited diverging states; preserve downhill gains and all existing gates.',free_bytes=shutil.disk_usage(ROOT).free,known_compute_processes=guard['processes'],compute_boundary=guard['boundary'],paid_compute_started=False,hardware_operated=False,boundary='Completed negative local simulation experiment. No calibrated physical accuracy, carpet transfer, or general walking acceptance.')
(dest/'result.json').write_text(json.dumps(result,indent=2)+'\n');seal(dest);print('Closure verified:',manifest(dest),'files; free GiB',round(result['free_bytes']/2**30,2))
