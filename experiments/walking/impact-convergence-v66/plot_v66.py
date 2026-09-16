"""Post-evaluation display of all phase buckets; no new acceptance rules."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent


def main():
    result=json.loads((BASE/'comparison.json').read_text())
    assert json.loads((BASE/'all-review.json').read_text())['verification_passed']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4.8),layout='constrained')
    x=np.arange(4)
    for ax,key,title in zip(axes,('position_max_m','penetration_peak_delta_m'),
                           ('Maximum position difference','Peak penetration difference')):
        for finest,offset,color,label in ((False,-.18,'#b6642a','0.625 vs 0.3125 ms'),
                                        (True,.18,'#2869a7','0.3125 vs 0.15625 ms')):
            values=[max(r[key] for r in result['numerical_screens'] if r['phase_bucket']==p and r['finest_pair']==finest)*1000 for p in range(4)]
            ax.bar(x+offset,values,width=.34,color=color,label=label)
            for i,value in enumerate(values):ax.text(i+offset,value+.003,f'{value:.3f}',ha='center',fontsize=8)
        ax.axhline(.1,color='#a52d32',ls='--',lw=1,label='Unchanged 0.100 mm limit')
        ax.set_xticks(x,['P0\n0 μs','P1\n195.3 μs','P2\n390.6 μs','P3\n585.9 μs'])
        ax.set(title=title,ylabel='Worst of four models (mm)',xlabel='Initial advance along the same free fall',ylim=(0,.155))
    axes[0].legend(frameon=False,fontsize=8,loc='upper left')
    fig.suptitle('Ducky V66 — all 16 finest-step timing buckets pass\n96 verified drops · 358,400 physics samples · guided bench only',fontsize=14)
    fig.savefig(BASE/'results.png',dpi=160);fig.savefig(BASE/'results.pdf')


if __name__=='__main__':main()
