"""Offline, post-evaluation review and immutable closure; runs no policy."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'receipts/walking/20260907-v46-activity-closure'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_manifest(folder):
    entries = {}
    for line in (folder / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        path = (folder / name).resolve()
        assert path.is_relative_to(folder.resolve()), name
        assert sha(path) == expected, path
        entries[name] = expected
    assert entries
    return {'files': len(entries), 'manifest_sha256': sha(folder / 'SHA256SUMS')}


def seal(folder):
    (folder / 'SHA256SUMS').write_text(''.join(
        f'{sha(p)}  {p.relative_to(folder)}\n'
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))


class DisplayLabel(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = node.value.replace('V44', 'V46')
        return node


def physical_scoring_block(path):
    tree = ast.parse(path.read_text())
    blocks = [node for node in ast.walk(tree) if isinstance(node, ast.With)
              and any(isinstance(i.context_expr, ast.Call)
                      and ast.unparse(i.context_expr.func) == 'gzip.open'
                      for i in node.items)]
    assert len(blocks) == 1, path
    return ast.dump(DisplayLabel().visit(blocks[0]), include_attributes=False)


OUT.mkdir(exist_ok=False)
review = {'complete': False, 'gate_review': {}, 'source_freezes': {}, 'manifests': {}}
for bank, old in [('flat', 'flat_v44_r2'), ('endurance', 'endurance_v44'),
                  ('surfaces', 'surfaces_v44_r2'), ('fresh', 'fresh_v44')]:
    before = ROOT / f'scripts/evaluate_native_sequence_{old}.py'
    after = ROOT / f'scripts/evaluate_native_retention_{bank}_v46.py'
    assert physical_scoring_block(before) == physical_scoring_block(after), bank
    review['gate_review'][bank] = dict(
        physical_stepping_and_scoring_ast_identical=True,
        permitted_difference='V44/V46 display label only within execution block',
        reference_sha256=sha(before), candidate_sha256=sha(after))

freezes = sorted((ROOT / 'experiments/walking').glob('native-retention*freeze-v46.json'))
freezes += sorted((ROOT / 'experiments/walking').glob('component-*-freeze-v45.json'))
assert len(freezes) == 7
for path in freezes:
    data = json.loads(path.read_text())
    for name, expected in data['source_sha256'].items():
        assert sha(ROOT / name) == expected, name
    review['source_freezes'][path.name] = dict(files=len(data['source_sha256']), sha256=sha(path))

gate = ROOT / 'receipts/walking/20260907-v45-gate-review'
if not (gate / 'SHA256SUMS').exists():
    seal(gate)
folders = [p for p in (ROOT / 'receipts/walking').glob('20260907-v45-*') if p.is_dir()]
folders += [p for p in (ROOT / 'receipts/walking').glob('20260907-v46-*') if p.is_dir() and p != OUT]
folders += [ROOT / 'outputs/walking-retention-v46', ROOT / 'experiments/walking/retention-replay-v46']
for folder in sorted(folders):
    review['manifests'][str(folder.relative_to(ROOT))] = verify_manifest(folder)

prepare = json.loads((ROOT / '.workspace/v46-final-prepare.json').read_text())
assert prepare['ready_for_diagnosis'] and not prepare['errors'] and not prepare['discovery_errors']
assert not prepare['active_training_records']
assert all(item['matches'] for item in prepare['source_bindings'])
comparison = json.loads((ROOT / 'outputs/walking-retention-v46/comparison.json').read_text())
assert comparison['candidate_rejected'] and not comparison['fresh_sequence_bank_opened']
assert all(not comparison[bank]['lost_previously_passing'] for bank in ['flat', 'repeated', 'endurance', 'surfaces'])
review['decision'] = 'V46 not promoted: retains old passing cases but both required downhill sessions fail. Keep V30.'
review['fresh_bank_receipts_found'] = [str(p.relative_to(ROOT)) for p in (ROOT / 'receipts').rglob('*')
    if p.is_dir() and p.name.startswith('20260907-v46-') and 'fresh' in p.name]
assert not review['fresh_bank_receipts_found']
review['downhill_phase_observations'] = {}
trace = ROOT / 'receipts/walking/20260907-v46-retention-endurance/trajectory.jsonl.gz'
with gzip.open(trace, 'rt') as stream:
    for line in stream:
        row = json.loads(line)
        name = row['session_id']
        if not name.startswith('downhill'):
            break
        obs = review['downhill_phase_observations'].setdefault(name, {'phase_changes': [], 'first_load_above_1n_s': None})
        if not obs['phase_changes'] or obs['phase_changes'][-1]['actor'] != row['actor_mode']:
            obs['phase_changes'].append({'time_s': row['session_time_s'], 'actor': row['actor_mode']})
        for sample in row['self_load_physics']:
            if sample['total_normal_n'] > 1 and obs['first_load_above_1n_s'] is None:
                obs['first_load_above_1n_s'] = sample['interval_start_s']
        obs['last_row'] = {key: row[key] for key in ['session_time_s', 'actor_mode', 'fell', 'tilt_deg']}

paths = [ROOT / path for path in [
    'GOAL.md', 'TRAINING_ACTUALIZATION.md', 'docs/workspace/ACTIVE_EXPERIMENT.md',
    'docs/workspace/active-experiment.json', 'experiments/walking/COMPONENT-RESULTS-v45.md',
    'experiments/walking/RETENTION-RESULTS-v46.md', 'scripts/verify_native_retention_v46.py',
    'scripts/analyze_native_retention_v46.py', 'duck_workspace/core.py', 'experiment_ops/activity.py',
    'tests/test_duck_workspace.py', 'tests/test_experiment_ops.py',
    '.workspace/v46-workspace-tests-r2.log', '.workspace/v46-focused-tests.log',
    '.workspace/v46-final-prepare.json', '.workspace/v46-final-activity.json',
    '.workspace/v46-training.log', '.workspace/v46-smoke.log',
    '.workspace/v46-conformance.log', '.workspace/v46-evidence-verification.log',
    '.workspace/v46-analysis.log', '.workspace/v46-flat.log', '.workspace/v46-repeated.log',
    '.workspace/v46-endurance.log', '.workspace/v46-surfaces.log']]
paths += freezes + [Path(__file__)]
for path in paths:
    destination = OUT / 'retained' / path.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
review.update(complete=True, physical_calibration=False, policy_activated=False,
              paid_compute_used=False, hardware_used=False, disk_free_bytes=shutil.disk_usage(ROOT).free,
              boundary='Post-evaluation integrity and simulation acceptance review; no new policy execution or physical authority.')
(OUT / 'review.json').write_text(json.dumps(review, indent=2) + '\n')
seal(OUT)
verify_manifest(OUT)
print(json.dumps({'complete': True, 'gate_blocks': len(review['gate_review']),
                  'source_freezes': len(review['source_freezes']),
                  'receipt_manifests': len(review['manifests']), 'decision': review['decision']}))
