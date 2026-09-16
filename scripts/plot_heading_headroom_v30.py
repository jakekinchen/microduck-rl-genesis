"""Plot recorded V23/V30 heading error without altering either evaluator."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    rows={f'continuous-composition-start-{i}':[] for i in (1,2)}
    with (ROOT/'receipts/walking'/name/'trajectory.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['session_id'] in rows and r['session_time_s']>=2-1e-9:rows[r['session_id']].append(r)
    result={}
    for key,rs in rows.items():
        t=np.array([r['session_time_s'] for r in rs])
        w,x,y,z=np.array([r['qpos'][3:7] for r in rs]).T
        yaw=np.unwrap(np.arctan2(2*(x*y+w*z),1-2*(y*y+z*z)))
        cmd=np.array([r['command'][2] for r in rs])
        error=np.rad2deg(yaw-yaw[0]-np.r_[0,np.cumsum(cmd[:-1]*.02)])
        result[key]=(t,error)
    return result


def main():
    a=load('20260906-v23-endurance');b=load('20260906-v30-heading-endurance')
    fig,axes=plt.subplots(2,1,figsize=(10,6),sharex=True,constrained_layout=True)
    for i,(key,ax) in enumerate(zip(a,axes)):
        ax.plot(*a[key],label='V23: reference follows STOP drift',color='#a6473c',linewidth=1.5)
        ax.plot(*b[key],label='V30: course persists, with correction headroom',color='#187f82',linewidth=1.5)
        ax.axhline(20,color='#777',linestyle='--',linewidth=.8)
        ax.axhline(-20,color='#777',linestyle='--',linewidth=.8)
        ax.set_ylabel('Heading error (degrees)');ax.set_title(f'Independent start {i+1}',loc='left')
        ax.grid(alpha=.15)
    axes[0].legend(loc='upper left',fontsize=8)
    axes[-1].set_xlabel('Continuous simulation time (seconds)')
    fig.suptitle('Course preservation across repeated walking, turning and stopping\nExposed simulation comparison; identical motor policies and physics',fontsize=12)
    out=ROOT/'receipts/walking/20260906-v25-verification/heading-persistence-v30.png'
    fig.savefig(out,dpi=150);plt.close(fig)

if __name__=='__main__':main()
