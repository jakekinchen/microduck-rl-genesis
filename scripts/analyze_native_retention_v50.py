"""Offline full-gate retention and downhill absolute-yaw comparison for V50."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from scripts.verify_native_retention_v50 import manifest


def prefix(folder):
    path=folder/'trajectory.jsonl.gz'
    if not path.exists():path=folder/'trajectory.jsonl'
    opener=gzip.open if path.suffix=='.gz' else open
    traces={f'downhill-3deg-start-{i}--window-1':[] for i in [1,2]}
    with opener(path,'rt') as f:
        for line in f:
            row=json.loads(line)
            if row['case_id'] in traces:traces[row['case_id']].append(row)
    import numpy as np
    result={}
    for case,rows in traces.items():
        selected=[r for r in rows if 2.-1e-9<=r['time_s']<=13.+1e-9]
        complete=len(selected)==551 and not any(r['fell'] for r in selected)
        error=np.array([r['yaw_rate_rad_s']-r['command'][2] for r in selected])
        result[case]=dict(controls=len(selected),complete_common_prefix=complete,mean_absolute_yaw_error_rad_s=float(abs(error).mean()) if len(error) else None,
            signed_mean_yaw_error_rad_s=float(error.mean()) if len(error) else None,p95_absolute_yaw_error_rad_s=float(np.percentile(abs(error),95)) if len(error) else None,
            prefix_yaw_gate_only=bool(complete and abs(error).mean()<=.20),trace_sha256=digest(path),
            first_fall_s=next((r['time_s'] for r in rows if r['fell']),None),
            time_s=[r['time_s'] for r in rows],yaw_rate_rad_s=[r['yaw_rate_rad_s'] for r in rows],
            forward_velocity_m_s=[r['body_velocity_m_s'][0] for r in rows],tilt_deg=[r['tilt_deg'] for r in rows])
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pairs=[('flat','20260906-v30-flat-regression','evaluation.json'),
           ('repeated','20260906-v30-repeated-regression-r2','evaluation.json'),
           ('endurance','20260906-v30-heading-endurance','probe.json'),
           ('surfaces','20260906-v30-surface-baseline','probe.json')]
    summary={}
    for suffix,baseline,filename in pairs:
        candidate=ROOT/f'receipts/walking/20260908-v50-retention-{suffix}'
        base=ROOT/'receipts/walking'/baseline
        manifest(base);manifest(candidate)
        old,new=json.loads((base/filename).read_text()),json.loads((candidate/filename).read_text())
        assert not new.get('exception')
        assert {c['case_id'] for c in old['case_reports']}=={c['case_id'] for c in new['case_reports']}
        key='session_reports' if filename=='probe.json' else 'case_reports'
        identity='session_id' if filename=='probe.json' else 'case_id'
        if filename=='probe.json':assert old['complete'] and new['complete']
        old_pass={s[identity] for s in old[key] if s['passed']}
        new_pass={s[identity] for s in new[key] if s['passed']}
        summary[suffix]=dict(baseline_passes=len(old_pass),candidate_passes=len(new_pass),
            lost_previously_passing=sorted(old_pass-new_pass),new_passes=sorted(new_pass-old_pass),
            passing_windows=sum(c['passed'] for c in new['case_reports']),required_windows=len(new['case_reports']),
            failure_counts=dict(Counter(f for c in new['case_reports'] for f in c['failures'])),
            candidate_report_sha256=digest(candidate/filename),baseline_report_sha256=digest(base/filename))
        if filename=='probe.json':
            summary[suffix]['sessions']=[{k:s[k] for k in ['session_id','passed','simulated_duration_s','required_duration_s','failures']} for s in new[key]]
    prerequisites=summary['flat']['candidate_passes']==21 and summary['repeated']['candidate_passes']==42 and summary['endurance']['candidate_passes']==4 and not summary['surfaces']['lost_previously_passing']
    traces={label:prefix(ROOT/'receipts/walking'/folder) for label,folder in [('V30 retained','20260906-v30-heading-endurance'),('V50 candidate','20260908-v50-retention-endurance')]}
    summary.update(prerequisites_passed=prerequisites,candidate_rejected=not prerequisites,
        physical_calibration=False,interpretation='Absolute yaw is scored before braking; prefix improvement cannot pass a failed full sequence.')
    import numpy as np
    import onnxruntime as ort
    replay=np.load(ROOT/'experiments/walking/retention-replay-v50/replay.npz')
    replay_obs,replay_actions=replay['observations'],replay['actions']
    replay.close()
    provenance=json.loads((ROOT/'experiments/walking/retention-replay-v50/provenance.json').read_text())
    policy=ROOT/'receipts/walking/20260908-v50-retention-flat/policy.onnx'
    options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
    session=ort.InferenceSession(str(policy),sess_options=options,providers=['CPUExecutionProvider'])
    shift=[]
    for i in range(len(replay_obs)):
        action=session.run(None,{session.get_inputs()[0].name:replay_obs[i:i+1]})[0][0]
        assert np.isfinite(action).all()
        shift.append(abs(action-replay_actions[i]))
    shift=np.array(shift)
    offset=0;groups={}
    for source in provenance['sources']:
        part=shift[offset:offset+source['rows']];offset+=source['rows']
        groups[source['receipt']]=dict(rows=len(part),mean_abs_action_change_rad=float(part.mean()),
            p95_worst_joint_action_change_rad=float(np.percentile(part.max(1),95)),maximum_action_change_rad=float(part.max()))
    assert offset==len(shift)
    summary['retention_replay_action_shift']=dict(policy_sha256=digest(policy),groups=groups,
        boundary='Action changes on original recorded states; closed-loop retention remains the full-bank result.')
    summary['downhill_prefix']={label:{case:{k:v for k,v in row.items() if not isinstance(v,list)} for case,row in data.items()} for label,data in traces.items()}
    a.output.mkdir(parents=True,exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(11,6),sharex=True,layout='constrained')
    for col,case in enumerate(traces['V30 retained']):
        for label,color in [('V30 retained','#197a6b'),('V50 candidate','#bd4938')]:
            d=traces[label][case]
            axes[0,col].plot(d['time_s'],d['yaw_rate_rad_s'],color=color,label=label,lw=.8)
            axes[1,col].plot(d['time_s'],d['forward_velocity_m_s'],color=color,label=label,lw=.9)
        axes[0,col].set_title(case.replace('--window-1',''))
        axes[0,col].set_ylabel('Actual yaw rate (rad/s)')
        axes[1,col].set_ylabel('Forward speed (m/s)');axes[1,col].set_xlabel('Session time (s)')
        axes[1,col].axhline(.12,color='#666',ls='--',lw=.7)
        for row in range(2):
            axes[row,col].axvspan(13,18,color='#aaa',alpha=.15)
            axes[row,col].set_xlim(1,14.5);axes[row,col].grid(alpha=.2)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Downhill walking and first stop — full-session acceptance is reported separately')
    fig.savefig(a.output/'downhill-yaw.png',dpi=160);fig.savefig(a.output/'downhill-yaw.pdf');plt.close(fig)
    (a.output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    (a.output/'plot-data.json').write_text(json.dumps(traces)+'\n')
    (a.output/'analysis-source.py').write_bytes(Path(__file__).read_bytes())
    (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.name}\n' for f in sorted(a.output.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
    print(json.dumps({k:{n:v for n,v in r.items() if n in ['candidate_passes','baseline_passes','lost_previously_passing']} for k,r in summary.items() if isinstance(r,dict)}))

if __name__=='__main__':main()
