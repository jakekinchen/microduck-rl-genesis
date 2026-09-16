"""Figures from recorded arrays only; no extrapolated or rescued trajectories."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import gzip

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
bank=json.loads((BASE/'bank-r2.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
colors=['#197b89','#d67235','#8158aa']
for column,model in enumerate(('v11','v62')):
    for dt,color in zip((.005,.0025,.00125),colors):
        for row,mode in enumerate(('replay','passive')):
            case=next(c for c in bank['cases'] if c['model']==model and c['dt_s']==dt and c['mode']==mode and c['repeat']==1 and c['intervention']=='none')
            path=ROOT/bank['output_root']/case['id']
            with np.load(path/'dynamics.npz') as a:qpos=a['qpos']
            time=np.arange(1,len(qpos)+1)*dt
            if mode=='replay':values=qpos[:,2]*1000
            else:
                with gzip.open(path/'physics.jsonl.gz','rt') as stream:
                    values=np.array([json.loads(line)['ground_penetration_m'] for line in stream])*1000
            ax=axes[row,column]
            ax.plot(time,values,color=color,lw=1.4,label=f'{dt*1000:g} ms integration')
            ax.plot(time[-1],values[-1],'.',color=color,ms=6)
    axes[0,column].set_title(('V11 control' if model=='v11' else 'V62 detailed model')+' — recorded-action replay',fontweight='bold')
    axes[1,column].set_title(('V11 control' if model=='v11' else 'V62 detailed model')+' — passive impact',fontweight='bold')
    axes[0,column].axhline(70,color='#b24545',ls='--',lw=1)
    axes[1,column].axhline(3,color='#b24545',ls='--',lw=1)
    axes[0,column].set(xlim=(0,4),ylim=(50,130),ylabel='Root height (mm)',xlabel='Simulation time (s)')
    axes[1,column].set(xlim=(0,1),ylabel='Floor penetration (mm)',xlabel='Simulation time (s)')
for ax in axes.flat:
    ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
axes[0,0].legend(frameon=False,fontsize=9)
fig.suptitle('V64 integration-step diagnostics\n50 Hz commands · 200 Hz BAM updates · unchanged 20 ms motor delay',fontweight='bold',fontsize=16)
fig.supxlabel('Recorded prefixes only; view limited to first 4 s of replay and first 1 s of passive motion.',fontsize=10)
fig.savefig(BASE/'integration-diagnostics.png',dpi=170)
fig.savefig(BASE/'integration-diagnostics.svg')
plt.close(fig)
