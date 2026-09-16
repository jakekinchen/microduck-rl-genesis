"""Review nested hybrid lineage; approximate CoACD coverage is a separate gate."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[4]


def same_part(first, i, second, j):
    return all(np.array_equal(first[f'{key}{i:03}'], second[f'{key}{j:03}']) for key in ('v', 'f'))


def main():
    bank = json.loads(Path(sys.argv[1]).read_text())
    failures = []
    for path, digest in bank['input_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            failures.append('changed_input:'+path)
    meta = json.loads((ROOT/bank['complete_json']).read_text())
    records = json.loads((ROOT/bank['progress']).read_text())['parents']
    offset, unchanged, hybrid, local_unchanged, source_partitions = 0, 0, 0, 0, 0
    worst_volume_residual = 0.
    with np.load(ROOT/bank['parts_npz'], allow_pickle=False) as final, np.load(ROOT/bank['parent_parts_npz'], allow_pickle=False) as original:
        if [r['parent_part'] for r in records] != list(range(len(original.files)//2)):
            failures.append('incomplete_parent_coverage')
        for record in records:
            parent, count = record['parent_part'], record['output_count']
            if record['output_start'] != offset:
                failures.append(f'bad_parent_offset:{parent}')
            if record['decision'] == 'unchanged':
                unchanged += 1
                if count != 1 or not same_part(final, offset, original, parent):
                    failures.append(f'changed_unchanged_parent:{parent}')
            elif record['decision'] == 'local_coacd_source_partition':
                hybrid += 1
                directory = ROOT/record['region_directory']
                for filename, key in [('coacd-parts.npz', 'coarse_sha256'), ('refined-parts.npz', 'refined_sha256')]:
                    if hashlib.sha256((directory/filename).read_bytes()).hexdigest() != record[key]:
                        failures.append(f'region_digest:{parent}:{filename}')
                with np.load(directory/'coacd-parts.npz', allow_pickle=False) as coarse, np.load(directory/'refined-parts.npz', allow_pickle=False) as polished:
                    if count*2 != len(polished.files) or record['coarse_parts']*2 != len(coarse.files):
                        failures.append(f'region_count:{parent}')
                    if any(not same_part(final, offset+i, polished, i) for i in range(count)):
                        failures.append(f'changed_region_assembly:{parent}')
                    local_offset = 0
                    if [x['parent_part'] for x in record['local_refinement']] != list(range(record['coarse_parts'])):
                        failures.append(f'local_coverage:{parent}')
                    for local in record['local_refinement']:
                        if local['output_start'] != local_offset:
                            failures.append(f'local_offset:{parent}')
                        if local['decision'] == 'unchanged':
                            local_unchanged += 1
                            if local['output_count'] != 1 or not same_part(polished, local_offset, coarse, local['parent_part']):
                                failures.append(f'changed_local_retained:{parent}')
                        elif local['decision'] == 'source_partition':
                            source_partitions += 1
                            leaves = [x for x in local['partition_events'] if x['decision'] == 'retain']
                            volume = local['intersected_source_volume_m3']
                            residual = abs(sum(x['source_volume_m3'] for x in leaves)-volume)
                            worst_volume_residual = max(worst_volume_residual, residual)
                            if len(leaves) != local['output_count'] or residual > max(1e-18, abs(volume)*1e-8):
                                failures.append(f'local_source_volume:{parent}')
                            for i, event in enumerate(leaves):
                                part = trimesh.Trimesh(polished[f'v{local_offset+i:03}'], polished[f'f{local_offset+i:03}'], process=False)
                                if abs(part.volume-event['convex_volume_m3']) > max(1e-18, abs(part.volume)*1e-8):
                                    failures.append(f'local_hull_volume:{parent}')
                        elif local['decision'] != 'empty_source_intersection' or local['output_count'] != 0 or local['intersected_source_volume_m3'] != 0:
                            failures.append(f'unknown_local_decision:{parent}')
                        local_offset += local['output_count']
                    if local_offset != count:
                        failures.append(f'local_output_count:{parent}')
            elif record['decision'] != 'empty_source_intersection' or count != 0 or record['intersected_source_volume_m3'] != 0:
                failures.append(f'unknown_parent_decision:{parent}')
            offset += count
    if offset != meta['parts']:
        failures.append('final_count')
    report = {'passed': not failures, 'failures': failures, 'original_parents': len(records), 'parts': offset,
              'unchanged_parents_exact': unchanged, 'hybrid_regions': hybrid,
              'local_unchanged_parts_exact': local_unchanged, 'source_partitions': source_partitions,
              'maximum_partition_volume_residual_m3': worst_volume_residual,
              'boundary': 'CoACD is approximate; this lineage check does not replace independent whole-CAD missing/excess evaluation'}
    with (ROOT/bank['output']).open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
