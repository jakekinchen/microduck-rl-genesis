"""Plot V49 recorded continuations and frozen search cost; no rescoring."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import COMPARE,SEARCH,digest,seal


def read(folder):
    with gzip.open(folder/'trajectory.jsonl.gz','rt') as f:return [json.loads(line) for line in f]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    a.output.mkdir(parents=True,exist_ok=False)
    first='matched--downhill-3deg-start-1-650';late='v48--continuous-composition-start-1-4256'
    inputs={'Downhill original':COMPARE/(first+'--original'),'Downhill searched':SEARCH/first,
            'Late original stander':COMPARE/(late+'--original'),'Late V48 stander':COMPARE/(late+'--v48')}
    data={label:dict(source_sha256=digest(folder/'trajectory.jsonl.gz'),rows=read(folder)) for label,folder in inputs.items()}
    fig,axes=plt.subplots(2,2,figsize=(13,7.5),layout='constrained')
    for label,color in [('Downhill original','#b14030'),('Downhill searched','#197a68')]:
        r=data[label]['rows'];axes[0,0].plot([x['session_time_s'] for x in r],[x['tilt_deg'] for x in r],label=label,color=color,lw=1.2)
        axes[1,0].plot([x['session_time_s'] for x in r],[max(s['total_normal_n'] for s in x['self_load_physics']) for x in r],color=color,lw=1.2)
    axes[0,0].set(title='Downhill: first stop survives, second stop falls',ylabel='Trunk tilt (degrees)',xlim=(13,36))
    axes[1,0].set(ylabel='Applied internal load (N)',xlabel='Full-session time (s)',xlim=(13,36))
    for ax in axes[:,0]:
        ax.axvspan(13,18,alpha=.12,color='#777');ax.axvspan(31,36,alpha=.12,color='#777')
    axes[0,0].legend(fontsize=8)
    for label,color in [('Late original stander','#197a68'),('Late V48 stander','#b14030')]:
        r=data[label]['rows'];axes[0,1].plot([x['session_time_s'] for x in r],[x['tilt_deg'] for x in r],label=label,color=color,lw=1)
    axes[0,1].set(title='Same V48 late state: original stander finishes 180 s',ylabel='Trunk tilt (degrees)',xlim=(85,180));axes[0,1].legend(fontsize=8)
    result=json.loads((SEARCH/'result.json').read_text())
    for state in result['states']:
        if 'generation_log' not in state:continue
        g=state['generation_log'];axes[1,1].plot([r['generation']+1 for r in g],[min(r['best_costs']) for r in g],marker='.',label=state['state_id'].replace('matched--downhill-3deg-',''))
    axes[1,1].set(title='Lower proxy cost; all four full sessions still fail',ylabel='Best proxy cost (log scale)',xlabel='Frozen search generation',yscale='log');axes[1,1].legend(fontsize=8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.savefig(a.output/'recovery-diagnostic.png',dpi=150);fig.savefig(a.output/'recovery-diagnostic.pdf');plt.close(fig)
    compact={label:dict(source_sha256=r['source_sha256'],time_s=[x['session_time_s'] for x in r['rows']],tilt_deg=[x['tilt_deg'] for x in r['rows']]) for label,r in data.items()}
    (a.output/'plot-data.json').write_text(json.dumps(compact)+'\n')
    shutil.copy2(Path(__file__),a.output/Path(__file__).name);seal(a.output)

if __name__=='__main__':main()
