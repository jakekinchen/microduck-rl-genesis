"""Preregistered zero-command standing feasibility; not a learned candidate."""
import gzip
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.walking.posture_v56 import new_output,digest,write_manifest

PROTOCOL=ROOT/'experiments/walking/posture-feasibility-v56.json'

def main():
    from experiments.walking.terrain_v23 import TerrainWorld,TerrainGaitProbe,materialize_terrain
    from experiments.walking.self_load import record_self_loads,evaluate_self_load
    from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
    from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
    from scripts.analyze_components_v45 import verify_manifest
    from scripts.train_yaw_v55 import require_freeze
    from evaluator.core import OnnxPolicy
    require_freeze()
    cfg=json.loads(PROTOCOL.read_text())
    for path,sha in cfg['sources'].items():
        if digest(ROOT/path)!=sha:raise ValueError('feasibility source drift: '+path)
    out=new_output('receipts/walking/20260916-v56-posture-feasibility')
    (out/'protocol.json').write_text(PROTOCOL.read_text())
    model=ROOT/'experiments/walking/models/contact-v11'
    geometry=SelfContactProbe(model/'scene.xml')
    reports=[]
    for role,source in cfg['policies'].items():
        folder=ROOT/source['folder'];verify_manifest(folder)
        actor=folder/source['actor']
        if digest(actor)!=source['sha256']:raise ValueError('actor drift')
        verifier=OnnxPolicy(actor,json.loads((ROOT/'evaluator/config-v1.json').read_text())['inference'])
        for motor in cfg['motor_ticks']:
            for yaw in cfg['initial_yaws']:
                name=f'{role}-motor{motor}-yaw{yaw}'
                scene=materialize_terrain(out/'models'/name,{'kind':'slope','axis':'y','degrees':3.})
                w=TerrainWorld(actor,ROOT/'.workspace/bam',standing_policy=actor,model_directory=model,
                    terrain_scene=scene,domain={'mass_inertia_scale':1.,'sliding_friction_scale':1.},
                    motor_ticks=motor,sensor_ticks=1,yaw=yaw,seed=cfg['seed'])
                w.heading_servo=Float32HeadingHeadroomServo();probe=TerrainGaitProbe(w.core)
                rows=[];actions=[]
                try:
                    with record_self_loads(w) as loads:
                        for tick in range(500):
                            if w.fell:break
                            row=probe.sample(w.step_command([0,0,0]))
                            assert row['actor_mode']=='standing'
                            row['actor_observation']=w.last_observation[0].tolist()
                            row['self_load_physics']=loads[-4:]
                            assert len(row['self_load_physics'])==4
                            actions.append(w.last_action.copy());rows.append(row)
                    contact=evaluate_self_contact(rows,geometry,500)
                    load=evaluate_self_load(loads,10.)
                    final=rows[-100:] if len(rows)==500 else []
                    face=[float(np.degrees(np.arcsin(np.clip(abs(r['face_world'][2]),0,1)))) for r in final]
                    metrics=dict(samples=len(rows),mean_final_face_pitch_deg=float(np.mean(face)) if face else None,
                        max_final_speed_m_s=max((r['speed_m_s'] for r in final),default=None),
                        max_final_yaw_rate_rad_s=max((abs(r['yaw_rate_rad_s']) for r in final),default=None),
                        max_final_tilt_deg=max((r['tilt_deg'] for r in final),default=None),
                        nonfoot_contact_frames=sum(bool(r['nonfoot_ground_contacts']) for r in rows),
                        maximum_joint_stop_fraction=float(np.max(np.mean(np.asarray([r['joint_limit_margin_fraction'] for r in rows[50:]])<.05,axis=0))) if len(rows)>50 else None,
                        max_actual_limit_violation_rad=max((max(r['joint_limit_violation_rad']) for r in rows),default=None),
                        max_applied_torque_nm=max((float(np.max(np.abs(r['motor_torque_physics_nm']))) for r in rows),default=None))
                    failures=[]
                    if len(rows)!=500 or any(r['fell'] for r in rows):failures.append('incomplete_or_fallen')
                    for key,limit in cfg['limits'].items():
                        if metrics[key] is None or metrics[key]>limit:failures.append(key)
                    failures+=['self_contact:'+f for f in contact['failures']]
                    failures+=['self_load:'+f for f in load['failures']]
                    for row,action in zip(rows,actions):
                        exact,_=verifier.infer(np.asarray(row['actor_observation'],np.float32)[None])
                        if exact[0].tobytes()!=action.reshape(14).tobytes():raise ValueError('offline actor action mismatch')
                    report=dict(case=name,policy_sha256=source['sha256'],metrics=metrics,passed=not failures,
                        failures=failures,self_contact=contact,self_load=load,
                        exact_offline_onnx_rows=len(rows),
                        materialized_domain=w.materialized_domain,materialized_terrain=w.materialized_terrain,
                        motor_ticks=w.motor_ticks,sensor_ticks=w.sensor_ticks)
                    reports.append(report)
                    np.save(out/(name+'-actions-float32.npy'),np.asarray(actions,np.float32))
                    with gzip.open(out/(name+'.jsonl.gz'),'wt') as f:
                        for row in rows:f.write(json.dumps(row)+'\n')
                    print(json.dumps({k:report[k] for k in ['case','passed','failures','metrics']}),flush=True)
                finally:w.close()
    result=dict(complete=len(reports)==12,reports=reports,
        all_cases_passed=all(r['passed'] for r in reports),
        policies_with_all_six_feasible=[role for role in cfg['policies'] if all(r['passed'] for r in reports if r['case'].startswith(role+'-'))],
        protocol_sha256=digest(PROTOCOL),
        boundary='Zero-command HOME-start downhill feasibility; no transition, training, physical calibration or behavior admission.')
    (out/'feasibility.json').write_text(json.dumps(result,indent=2)+'\n');write_manifest(out)

if __name__=='__main__':main()
