from pathlib import Path
import hashlib,json,shutil
from scripts.verify_native_retention_v50 import manifest
from scripts.evaluate_laser import digest
root=Path('.')
out=root/'receipts/walking/20260908-v50-activity-closure';out.mkdir(exist_ok=False)
folders=[root/'receipts/walking'/f'20260908-v50-{n}' for n in ['retention-conformance','replay-parity','retention-flat','retention-repeated','retention-endurance','retention-surfaces','retention-verification']]
folders += [root/'experiments/walking/retention-replay-v50',root/'outputs/walking-retention-v50']
media=root/'outputs/walking-retention-v50-video'
shutil.copy2(root/'scripts/render_compressed_surface_receipt.py',media/'render-source.py')
(media/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(media.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
folders.append(media)
refs={str(f):{'files':manifest(f),'manifest_sha256':digest(f/'SHA256SUMS')} for f in folders}
freezes={}
for pattern in ['native-sequence*freeze-v44.json','native-retention*freeze-v46.json','native-standing-retention*freeze-v48.json','recovery-freeze-v49.json','native-retention*freeze-v50.json']:
 for path in (root/'experiments/walking').glob(pattern):
  f=json.loads(path.read_text())
  for name,sha in f['source_sha256'].items():assert digest(root/name)==sha,name
  freezes[str(path)]={'source_files':len(f['source_sha256']),'sha256':digest(path)}
prepared=json.loads((root/'.workspace/v50-final-prepare.json').read_text())
assert prepared['ready_for_diagnosis'] and not prepared['errors'] and not prepared['discovery_errors'] and not prepared['active_training_records']
guard=json.loads((root/'.workspace/v50-final-guard.json').read_text());assert not guard['processes'] and guard['status']=='no_known_training_process'
comparison=json.loads((root/'outputs/walking-retention-v50/comparison.json').read_text());assert comparison['candidate_rejected'] and not comparison['prerequisites_passed']
assert not list((root/'receipts/walking').glob('*v50*fresh*'))
retained=['GOAL.md','TRAINING_ACTUALIZATION.md','docs/workspace/ACTIVE_EXPERIMENT.md','docs/workspace/active-experiment.json',
 'experiments/walking/RETENTION-RESULTS-v50.md','experiments/walking/RETENTION-CORRECTION-v50.md',
 'scripts/analyze_native_retention_v50.py','duck_workspace/core.py','experiment_ops/activity.py','tests/test_experiment_ops.py']
retained += [str(p) for p in (root/'experiments/walking').glob('native-retention*freeze-v50.json')]
retained += [str(p) for p in (root/'.workspace').glob('v50-*') if p.is_file()]
for name in retained:
 p=root/name;dest=out/'retained'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
# The generated report and raw-source references are already independently sealed.
review=dict(activity='V50 bounded downhill yaw correction',activity_complete=True,behavior_accepted=False,
 retained_policy='Original V21 walking + V15 standing, V30 command control',
 walking_prefix_improvement=True,downhill_yaw_gate_passed=False,downhill_sessions_passed=0,
 retained_flat_cases=63,retained_180s_compositions=2,retained_surface_sessions=5,
 full_transitions=864000,smoke_transitions=2880,paired_conformance_controls=341008,
 exact_original_replay_rows=56655,verified_switch_histories=1988,finite_learning_scalars=9638,
 workspace_tests=140,focused_tests=3,source_freezes=freezes,verified_receipt_manifests=refs,
 frozen_stander_teacher_normalizers=True,actual_24_cell_geometry_timing_yaw_and_actor_routing_verified=True,
 all_known_activity_compute_finished=True,fresh_sequence_bank_opened=False,protected_terrain_opened=False,
 calibration=False,physical_transfer=False,paid_compute_used=False,policy_activated=False,
 free_internal_gib=shutil.disk_usage(root).free/2**30,
 offline_analysis_repair='Stopped own slow analysis after profiling repeated NPZ decompression; cache each array once. No frozen learner/evaluator change or outcome selection. Failed attempt source and profiling receipt retained.',
 next_activity='Revalidate or retarget three V49 stop witnesses on V50 incoming states, then a bounded state-conditioned braking correction retaining V15 and the remaining .20 yaw gate plus complete retention.')
(out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
(out/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print({'closure_files':manifest(out),'referenced_files':sum(x['files'] for x in refs.values()),'free_internal_gib':review['free_internal_gib'],'activity_complete':True,'behavior_accepted':False})
