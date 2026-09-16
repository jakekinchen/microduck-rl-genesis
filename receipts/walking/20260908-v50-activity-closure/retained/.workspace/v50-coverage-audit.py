"""Post-run checks of compiled physical cells, actual actor routing and reward coverage."""
import gzip,json
from pathlib import Path
import numpy as np
from microduck.native_sequence_env_v50 import BUCKETS
root=Path('.')
probe=json.loads((root/'receipts/walking/20260908-v50-retention-conformance/probe.json').read_text())
reports={}
for run,expected in [('retention-native-20260908-v50-smoke',2880),('retention-native-20260908-v50',864000)]:
 folder=root/'logs'/run;r=json.loads((folder/'run.json').read_text());coverage=r['final_coverage']
 assert r['status']=='completed' and r['new_transitions']==expected
 assert len(coverage['materialized_timing_cells'])==len(probe['reports'])==24
 for i,(actual,ref,expected_cell) in enumerate(zip(coverage['materialized_timing_cells'],probe['reports'],BUCKETS)):
  assert actual['terrain']==ref['materialized_terrain'] and actual['domain']==ref['materialized_domain']
  assert actual['motor_ticks']==ref['motor_ticks']==expected_cell[3]
  assert actual['sensor_ticks']==ref['sensor_ticks']==expected_cell[4]
  assert actual['domain']['factors']=={'mass_inertia_scale':1.,'sliding_friction_scale':1.}
  half=np.deg2rad(expected_cell[1])/2
  np.testing.assert_allclose(actual['terrain']['arrays']['geom_quat'],[[np.cos(half),0,np.sin(half),0]],rtol=0,atol=1e-12)
  np.testing.assert_allclose(ref['home_qpos'][3:7],[np.cos(expected_cell[5]/2),0,0,np.sin(expected_cell[5]/2)],rtol=0,atol=1e-12)
  assert all(ref[k] for k in ['exact_observation_action_bytes','exact_physical_continuation','exact_nonaccumulating_full_reset'])
 n=r['args']['num_envs'];steps=expected//n
 obs=np.frombuffer(gzip.open(folder/'all-observations-float32.bin.gz','rb').read(),dtype='<f4').reshape(steps,n,61)
 rew=np.frombuffer(gzip.open(folder/'all-reward-components-float32.bin.gz','rb').read(),dtype='<f4').reshape(steps,n,6)
 np.testing.assert_array_equal((obs[:,:,48:51]==0).all(2),rew[:,:,5])
 counts=np.array([(rew[:,i::24,5]==0).sum() if cell[1]>0 else 0 for i,cell in enumerate(BUCKETS)])
 np.testing.assert_array_equal(counts,coverage['downhill_yaw_cost_steps'])
 assert np.isfinite(np.asarray(coverage['observation_min'])).all() and np.isfinite(np.asarray(coverage['observation_max'])).all()
 assert all(x>0 for x in coverage['reset_counts'])
 assert r['train_cfg']['obs_groups']['actor']==['policy'] and r['train_cfg']['obs_groups']['critic']==['policy']
 reports[run]=dict(controls=expected,actual_24_cell_geometry_timing_yaw_verified=True,
  optimizer_label_excluded_from_actor_and_critic=True,every_recorded_actor_role_verified=True,
  yaw_cost_moving_controls_per_cell=counts.tolist(),complete_180s_episodes=coverage['complete_180s_episodes'])
path=root/'.workspace/v50-coverage-audit.json';path.write_text(json.dumps(dict(passed=True,reports=reports),indent=2)+'\n')
print({k:{'controls':v['controls'],'complete_180s_episodes':sum(v['complete_180s_episodes'])} for k,v in reports.items()})
