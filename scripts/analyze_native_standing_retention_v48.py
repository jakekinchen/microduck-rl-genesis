"""Post-evaluation comparison against retained V30; does not score or run policies."""
import argparse
from collections import Counter,defaultdict
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import numpy as np
    from microduck.constants import JOINT_NAMES
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a.output.mkdir(parents=True,exist_ok=False)
    pairs=[('flat','20260906-v30-flat-regression','evaluation.json'),
           ('repeated','20260906-v30-repeated-regression-r2','evaluation.json'),
           ('endurance','20260906-v30-heading-endurance','probe.json'),
           ('surfaces','20260906-v30-surface-baseline','probe.json')]
    summary={}
    for suffix,baseline,filename in pairs:
        candidate=ROOT/f'receipts/walking/20260908-v48-standing-retention-{suffix}'
        base=ROOT/'receipts/walking'/baseline
        old,new=json.loads((base/filename).read_text()),json.loads((candidate/filename).read_text())
        if filename=='probe.json':
            assert old['complete'] and new['complete']
            old_pass={s['session_id'] for s in old['session_reports'] if s['passed']}
            new_pass={s['session_id'] for s in new['session_reports'] if s['passed']}
        else:
            old_pass={s['case_id'] for s in old['case_reports'] if s['passed']}
            new_pass={s['case_id'] for s in new['case_reports'] if s['passed']}
        summary[suffix]=dict(baseline_passes=len(old_pass),candidate_passes=len(new_pass),
            lost_previously_passing=sorted(old_pass-new_pass),new_passes=sorted(new_pass-old_pass),
            explicit_fall_windows=sum('fall' in c['failures'] for c in new['case_reports']),
            unrun_windows=sum('not_run_after_terminal_fall' in c['failures'] for c in new['case_reports']),
            failure_counts=dict(Counter(f for c in new['case_reports'] for f in c['failures'])),
            candidate_report_sha256=digest(candidate/filename),baseline_report_sha256=digest(base/filename))
        if filename=='probe.json':
            summary[suffix]['sessions']=[{k:s[k] for k in ['session_id','passed','simulated_duration_s','required_duration_s','failures']} for s in new['session_reports']]
    case='nominal-20-20ms--forward-08'
    trace_data={}
    for label,folder in [('V30 retained','20260906-v30-flat-regression'),('V48 candidate','20260908-v48-standing-retention-flat')]:
        base=ROOT/'receipts/walking'/folder
        path=base/'trajectory.jsonl.gz'
        if not path.exists():path=base/'trajectory.jsonl'
        opener=gzip.open if path.suffix=='.gz' else open
        rows=[]
        with opener(path,'rt') as f:
            for line in f:
                row=json.loads(line)
                if row['case_id']==case:rows.append(row)
        if not rows:
            raise ValueError('missing diagnostic trajectory: '+str(path))
        knee=JOINT_NAMES.index('right_knee')
        role={}
        for actor in ['walking','standing']:
            selected=[r for r in rows if r['actor_mode']==actor and r['time_s']>=1]
            margin=np.array([r['joint_limit_margin_fraction'][knee] for r in selected])
            role[actor]=dict(controls=len(selected),fraction_below_5_percent=float((margin<.05).mean()) if selected else None)
        trace_data[label]=dict(source_trace_sha256=digest(path),case=case,phase_occupancy=role,
            time_s=[r['time_s'] for r in rows],right_knee_margin_fraction=[r['joint_limit_margin_fraction'][knee] for r in rows],
            tilt_deg=[r['tilt_deg'] for r in rows])
    fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True,layout='constrained')
    for label,color in [('V30 retained','#1d796a'),('V48 candidate','#bc4932')]:
        d=trace_data[label];axes[0].plot(d['time_s'],100*np.array(d['right_knee_margin_fraction']),label=label,color=color,lw=1.2)
        axes[1].plot(d['time_s'],d['tilt_deg'],label=label,color=color,lw=1.2)
    axes[0].axhline(5,color='#333',ls='--',lw=1,label='Near-limit band (5% of range)')
    axes[0].set(ylabel='Right-knee margin (% of range)',title='First original flat case: forward 0.08 m/s, nominal delay')
    axes[1].set(xlabel='Continuous simulated time (s)',ylabel='Trunk tilt (degrees)')
    for ax in axes:
        ax.axvspan(13,18,color='#d7dae0',alpha=.4);ax.grid(alpha=.2);ax.set_xlim(0,18)
    axes[0].legend(loc='upper right',fontsize=8)
    fig.savefig(a.output/'knee-and-stop.png',dpi=160);fig.savefig(a.output/'knee-and-stop.pdf');plt.close(fig)
    prerequisites=(summary['flat']['candidate_passes']==21 and summary['repeated']['candidate_passes']==42 and summary['endurance']['candidate_passes']==4 and not summary['surfaces']['lost_previously_passing'])
    summary.update(candidate_rejected=not prerequisites,fresh_sequence_bank_opened=False,physical_calibration=False,
        diagnostic_case=case,phase_occupancy={k:v['phase_occupancy'] for k,v in trace_data.items()},
        interpretation='Original flat regression case under the standing correction; V48 uses original V21 walking with a new standing component. The original gates and all failed cases remain authoritative.')
    (a.output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    (a.output/'plot-data.json').write_text(json.dumps(trace_data)+'\n')
    shutil.copy2(Path(__file__),a.output/Path(__file__).name)
    (a.output/'SHA256SUMS').write_text(''.join(f'{digest(f)}  {f.name}\n' for f in sorted(a.output.iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
    print(json.dumps({k:{n:v for n,v in r.items() if n in ['candidate_passes','baseline_passes','explicit_fall_windows','unrun_windows']} for k,r in summary.items() if isinstance(r,dict)}))

if __name__=='__main__':main()
