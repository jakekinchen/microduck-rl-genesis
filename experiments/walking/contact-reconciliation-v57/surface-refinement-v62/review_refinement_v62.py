"""Check final lineage, unchanged regions and conservation from retained files."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[4]


def main():
    bank = json.loads(Path(sys.argv[1]).read_text())
    failures, results = [], {}
    for path, digest in bank['input_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            failures.append('changed_input:'+path)
    for name, spec in bank['components'].items():
        records = json.loads((ROOT/spec['progress']).read_text())['parents']
        meta = json.loads((ROOT/spec['complete_json']).read_text())
        old_meta = json.loads((ROOT/spec['parent_complete_json']).read_text())
        if len(records) != old_meta['parts'] or [r['parent_part'] for r in records] != list(range(old_meta['parts'])):
            failures.append(name+':incomplete_parent_coverage')
        unchanged, refined, empty, offset = 0, 0, 0, 0
        worst_volume_residual = 0.
        with np.load(ROOT/spec['parts_npz'], allow_pickle=False) as new, np.load(ROOT/spec['parent_parts_npz'], allow_pickle=False) as old:
            for record in records:
                if record['output_start'] != offset:
                    failures.append(name+':output_mapping')
                parent, count = record['parent_part'], record['output_count']
                if record['decision'] == 'unchanged':
                    unchanged += 1
                    if count != 1 or any(not np.array_equal(new[f'{prefix}{offset:03}'], old[f'{prefix}{parent:03}']) for prefix in ('v', 'f')):
                        failures.append(name+f':changed_retained_parent_{parent}')
                elif record['decision'] == 'source_partition':
                    refined += 1
                    leaves = [e for e in record['partition_events'] if e['decision'] == 'retain']
                    volume = record['intersected_source_volume_m3']
                    residual = abs(sum(e['source_volume_m3'] for e in leaves)-volume)
                    worst_volume_residual = max(worst_volume_residual, residual)
                    if len(leaves) != count or residual > max(1e-18, abs(volume)*1e-8):
                        failures.append(name+f':source_volume_conservation_{parent}')
                    for j, event in enumerate(leaves):
                        part = trimesh.Trimesh(new[f'v{offset+j:03}'], new[f'f{offset+j:03}'], process=False)
                        if (abs(part.volume-event['convex_volume_m3']) > max(1e-18, abs(part.volume)*1e-8)
                                or part.volume+1e-18 < event['source_volume_m3']):
                            failures.append(name+f':leaf_volume_{offset+j}')
                elif record['decision'] == 'empty_source_intersection':
                    empty += 1
                    if count != 0 or record['intersected_source_volume_m3'] != 0:
                        failures.append(name+f':invalid_empty_intersection_{parent}')
                else:
                    failures.append(name+':unknown_decision')
                offset += count
            if offset != meta['parts'] or len(new.files) != 2*offset:
                failures.append(name+':incomplete_output_coverage')
        results[name] = {'parents': len(records), 'parts': offset, 'unchanged_parents_exact': unchanged,
                         'refined_parents': refined, 'empty_intersections': empty,
                         'maximum_source_volume_residual_m3': worst_volume_residual}
    report = {'passed': not failures, 'failures': failures, 'components': results,
              'boundary': 'lineage and conservation check; material and assembly gates separate'}
    output = ROOT/bank['output']
    with output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
