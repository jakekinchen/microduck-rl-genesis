"""Plot current unit-stable material and independent additive measurements."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    path = Path(__file__).resolve().parent
    report = json.loads((path/'unit-stable-material-result.json').read_text())
    assert report['all_requested_checks_passed']
    current = report['meshes']
    dense = {}
    for filename in ['bearing-dense-result.json', 'bracket-dense-result.json',
                     'jaw-dense-result.json', 'parallel-shell-dense-result.json']:
        result = json.loads((path/filename).read_text())
        assert result['all_passed']
        dense.update(result['meshes'])
    names = ['seeed_bearing__configuration__22x16x4', 'neck_pitch', 'bottom_head_shell', 'jaw']
    labels = ['Bearing (retained)\n256 parts', 'Neck bracket\n614 parts',
              'Bottom head shell\n4,875 parts', 'Jaw\n1,781 parts']
    fig, ax = plt.subplots(figsize=(11, 5.2), layout='constrained')
    series = [
        ('max_sampled_missing_material_m', current, 'Source coverage error', '#5b7290'),
        ('max_sampled_excess_material_m', current, 'Proxy excess', '#218478'),
        ('maximum_excess_m', dense, 'Additional surface samples', '#af8639'),
    ]
    for offset, (key, source, label, color) in zip([-.25, 0, .25], series):
        values = np.array([source[n][key] for n in names])*1000
        bars = ax.bar(np.arange(4)+offset, values, .23, label=label, color=color)
        ax.bar_label(bars, labels=['<0.001' if v < .001 else f'{v:.3f}' for v in values],
                     fontsize=9, padding=3)
    ax.axhline(.25, color='#a43e37', linestyle='--', linewidth=1.4,
               label='Unchanged 0.25 mm limit')
    ax.set_xticks(np.arange(4), labels, fontsize=10)
    ax.set_ylabel('Maximum sampled distance (mm)')
    ax.set_ylim(0, .30)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', alpha=.15)
    ax.set_axisbelow(True)
    fig.legend(*ax.get_legend_handles_labels(), loc='outside lower center',
               ncol=2, frameon=False, fontsize=10)
    fig.suptitle('V62 collision geometry against original CAD\n'
                 'Unit-stable queries · Eight cavity witnesses pass · Geometry only',
                 fontsize=13, fontweight='bold')
    for suffix in ['png', 'svg']:
        output = path/f'material-validation.{suffix}'
        if output.exists():
            raise RuntimeError('plot already exists')
        fig.savefig(output, dpi=180)


if __name__ == '__main__':
    main()
