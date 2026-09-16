"""Post-evaluation figures; no new acceptance rules or simulation."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text())


def main():
    feedback=load(BASE/'feedback-comparison.json');bench=load(BASE/'bench-comparison.json')
    fb=load(BASE/'feedback-bank.json');bb=load(BASE/'bench-bank.json')
    assert load(BASE/'all-feedback-review.json')['verification_passed']
    assert load(BASE/'bench-review.json')['verification_passed']
    colors={'v11':'#2457a6','v62':'#b35722'}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    ax=axes[0,0]
    screens=feedback['numerical_screens']
    for i,r in enumerate(screens):
        value=r['root_max_m']*1000
        ax.bar(i,value,color=colors[r['model']],alpha=.95 if r['feedback']=='native' else .55)
        ax.text(i,value+.5,f'{value:.2f}',ha='center',fontsize=9)
    ax.axhline(1.,color='#922727',ls='--',lw=1,label='1 mm limit')
    ax.set_xticks(range(4),['V11\nnative','V11\nfixed 5 ms','V62\nnative','V62\nfixed 5 ms'])
    ax.set(ylabel='Maximum root difference (mm)',title='Replay: 2.5 vs 1.25 ms',ylim=(0,35));ax.legend(frameon=False)
    ax=axes[0,1]
    for model in ('v11','v62'):
        for mode,style in (('native','-'),('fixed_5ms','--')):
            cases=[next(c for c in fb['cases'] if c['model']==model and c['feedback']==mode and c['dt_s']==dt and c['repeat']==1) for dt in (.0025,.00125)]
            values=[next(r['time_s'] for r in feedback['cases'] if r['case']==c['id']) for c in cases]
            ax.plot([2.5,1.25],values,style,marker='o',color=colors[model],label=f"{model.upper()} {'native' if mode=='native' else 'fixed 5 ms'}")
    ax.set(xlabel='Integration step (ms)',ylabel='Time to fall (s)',title='Fixed-age feedback does not rescue replay',xticks=[1.25,2.5],ylim=(1.60,1.76))
    ax.legend(frameon=False,fontsize=8)
    ax=axes[1,0]
    for model in bb['models']:
        rows=[r for r in bench['cases'] if r['case']['model']==model]
        ax.plot([r['case']['dt_s']*1000 for r in rows],[r['peak_penetration_m']*1000 for r in rows],
                marker='o',lw=1.1,alpha=.75,label=model)
    ax.axhline(3.,ls='--',color='#922727',lw=1,label='3 mm diagnostic limit')
    ax.set(xlabel='Integration step (ms)',ylabel='Peak penetration (mm)',title='Guided drops: four matched assets overlap',ylim=(0,3.3))
    ax.legend(frameon=False,fontsize=8,ncol=2)
    ax=axes[1,1]
    for dt,style in ((.00125,'-'),(.000625,'--')):
        name=f'bench-v11-left-dt{round(dt*1e6)}us-r1'
        config=load(BASE/'runs'/name/'configuration.json')
        with np.load(BASE/'runs'/name/'dynamics.npz') as a:q=a['position_m']+config['clearance_m']
        t=np.arange(1,len(q)+1)*dt
        ax.plot(t[t<=.15]*1000,q[t<=.15]*1000,style,label=f'{dt*1000:g} ms step')
    ax.axhline(0,color='black',lw=.7)
    ax.set(xlabel='Simulation time (ms)',ylabel='Post-step sole clearance (mm)',title='First impact still depends on integration step')
    ax.text(.97,.93,'0.159 mm trajectory difference\n0.100 mm frozen limit',transform=ax.transAxes,ha='right',va='top',fontsize=9)
    ax.legend(frameon=False,loc='lower right')
    fig.suptitle('Ducky V65 — timing and sole-contact diagnostics\n56 verified runs · 56,302 physics samples · no walking or physical acceptance',fontsize=14)
    fig.savefig(BASE/'results.png',dpi=160)
    fig.savefig(BASE/'results.pdf')


if __name__=='__main__':main()
