"""Plot recorded prefixes only; never fill a terminated case's missing tail."""
from pathlib import Path
import gzip
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

P=Path(__file__).resolve().parent


def main():
    fig,axes=plt.subplots(3,3,figsize=(13,8),layout='constrained')
    modes=['home','passive','replay'];titles=['Fixed HOME hold','Passive settling','Recorded walking actions']
    for column,(mode,title) in enumerate(zip(modes,titles)):
        duration=18 if mode=='replay' else 5
        for model,color,label in [('v11','#237b80','V11 control'),('v62','#c27335','V62 full geometry')]:
            with gzip.open(P/'runs'/f'{model}-{mode}-r1/physics.jsonl.gz','rt') as stream:
                rows=[json.loads(line) for line in stream]
            time=np.array([r['time_s'] for r in rows])
            for axis,(key,scale) in zip(axes[:,column],[('root_z_m',1000),('tilt_deg',1),('ground_penetration_m',1000)]):
                axis.plot(time,[r[key]*scale for r in rows],color=color,lw=1.3,label=label)
            if model=='v62':
                for axis in axes[:,column]:axis.axvspan(time[-1],duration,color='#e8e9e8',alpha=.8,zorder=-1)
                axes[0,column].text(.98,.97,f'V62 ends at {time[-1]:.3f} s',transform=axes[0,column].transAxes,
                    ha='right',va='top',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.85})
        for axis in axes[:,column]:
            axis.set_xlim(0,duration);axis.grid(alpha=.18);axis.spines[['top','right']].set_visible(False)
        axes[0,column].axhline(70,color='#a33b36',ls='--',lw=.8)
        axes[1,column].axhline(70,color='#a33b36',ls='--',lw=.8)
        axes[2,column].axhline(3,color='#a33b36',ls='--',lw=.8)
        axes[0,column].set_ylim(0,140);axes[1,column].set_ylim(0,110)
        axes[2,column].set_ylim(0,11)
        axes[0,column].set_title(title,loc='left',fontweight='bold')
        axes[2,column].set_xlabel('Simulation time (s)')
    for axis,label in zip(axes[:,0],['Root height (mm)','Body tilt (degrees)','Floor penetration (mm)']):axis.set_ylabel(label)
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc='outside lower center',ncol=2,frameon=False)
    fig.suptitle('V63 startup and contact diagnostics\nGrey marks the unobserved V62 tail; both repetitions have identical dynamics',fontweight='bold')
    for suffix in ['png','svg']:
        output=P/f'diagnostics.{suffix}'
        if output.exists():raise RuntimeError('plot already exists')
        fig.savefig(output,dpi=160)


if __name__=='__main__':main()
