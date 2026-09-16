"""Plot recorded V30/V48 downhill motion; never fill missing trajectories."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    args.output.mkdir(parents=True, exist_ok=False)
    data = {}
    case = 'downhill-3deg-start-1--window-1'
    for label, receipt in [('V30 retained', '20260906-v30-heading-endurance'),
                           ('V48 candidate', '20260908-v48-standing-retention-endurance')]:
        folder = ROOT / 'receipts/walking' / receipt
        path = folder / 'trajectory.jsonl.gz'
        if not path.exists():
            path = folder / 'trajectory.jsonl'
        opener = gzip.open if path.suffix == '.gz' else open
        rows = []
        with opener(path, 'rt') as stream:
            for line in stream:
                row = json.loads(line)
                if row['case_id'] == case:
                    rows.append(row)
                elif rows:
                    break
        assert rows
        data[label] = dict(trace_sha256=digest(path), rows=len(rows),
            time_s=[r['time_s'] for r in rows], tilt_deg=[r['tilt_deg'] for r in rows],
            yaw_rad_s=[r['yaw_rate_rad_s'] for r in rows], speed_m_s=[r['speed_m_s'] for r in rows],
            internal_load_n=[max(s['total_normal_n'] for s in r['self_load_physics']) for r in rows],
            fell=any(r['fell'] for r in rows))
    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True, layout='constrained')
    metrics = [('tilt_deg','Trunk tilt (degrees)'), ('yaw_rad_s','Yaw rate (rad/s)'),
               ('speed_m_s','Speed (m/s)'), ('internal_load_n','Applied internal load (N)')]
    for label, color in [('V30 retained','#1d796a'),('V48 candidate','#bc4932')]:
        d = data[label]
        for ax, (key, ylabel) in zip(axes, metrics):
            ax.plot(d['time_s'],d[key],color=color,lw=1.2,label=label)
            ax.set_ylabel(ylabel)
    for ax in axes:
        ax.axvspan(13,18,color='#d7dae0',alpha=.4)
        ax.grid(alpha=.2)
        ax.set_xlim(12.5,18)
    axes[0].set_title('First original downhill stop: full recorded motion, unchanged physics')
    axes[0].legend(loc='upper left',fontsize=9)
    axes[-1].set_xlabel('Continuous simulated time (s); gray = requested STOP')
    fig.savefig(args.output/'downhill-stop.png',dpi=160)
    fig.savefig(args.output/'downhill-stop.pdf')
    plt.close(fig)
    (args.output/'plot-data.json').write_text(json.dumps(data)+'\n')
    shutil.copy2(Path(__file__),args.output/Path(__file__).name)
    (args.output/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n'
        for p in sorted(args.output.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
    print(json.dumps({k:{n:v for n,v in d.items() if n in ['rows','fell']} for k,d in data.items()}))


if __name__ == '__main__':
    main()
