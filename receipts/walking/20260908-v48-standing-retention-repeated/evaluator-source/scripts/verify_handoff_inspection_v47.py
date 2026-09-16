"""Verify V47 original controls and decoded complete-state continuations."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest
from scripts.verify_native_retention_v46 import manifest


def read_rows(folder, downhill_only=False):
    path = folder / 'trajectory.jsonl.gz'
    if not path.exists():
        path = folder / 'trajectory.jsonl'
    opener = gzip.open if path.suffix == '.gz' else open
    result = {}
    with opener(path, 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            if downhill_only and not row['session_id'].startswith('downhill'):
                continue
            result.setdefault(row['session_id'], []).append(row)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    from experiments.walking.terrain_v23 import TerrainWorld
    from experiments.walking.handoff_inspection_v47 import restore_state
    from experiments.walking.snapshots_v43 import load_state
    from microduck.heading_headroom_v30 import Float32HeadingHeadroomServo
    from microduck.native_standing_env_v42 import clone_world
    args.output.mkdir(parents=True, exist_ok=False)
    controls, continuations, details = {}, [], {}
    for pair, original in [('original', '20260906-v30-heading-endurance'),
                           ('v46', '20260907-v46-retention-endurance')]:
        folder = ROOT / f'receipts/walking/20260908-v47-{pair}-handoff'
        manifest(folder)
        reference = ROOT / 'receipts/walking' / original
        manifest(reference)
        rows, old = read_rows(folder), read_rows(reference, downhill_only=True)
        control_count = 0
        for name in old:
            assert len(rows[name]) == len(old[name])
            for now, before in zip(rows[name], old[name]):
                assert np.array_equal(now['qpos'], before['qpos'])
            for path in folder.glob(name + '*-actions-float32.npy'):
                x, y = np.load(path), np.load(reference / path.name)
                assert x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes()
                control_count += len(x)
        controls[pair] = dict(action_rows=control_count, action_tensor_bytes_identical=True, numeric_poses_exact=True)
        suite = json.loads((folder / 'suite.json').read_text())
        result = json.loads((folder / 'probe.json').read_text())
        assert result['complete']
        details[pair] = {'sessions': result['session_reports'], 'handoffs': {}}
        for session in suite['sessions']:
            name = session['id']
            # Use the exact retained materialized scene and unchanged engines.
            scene = folder / 'terrain-models' / name / 'scene.xml'
            world = TerrainWorld(folder / 'policy.onnx', ROOT / '.workspace/bam',
                standing_policy=folder / 'standing/policy.onnx',
                model_directory=ROOT / 'experiments/walking/models/contact-v11', terrain_scene=scene,
                domain=session['domain'], motor_ticks=6, sensor_ticks=1, yaw=session['yaw'], seed=session['seed'])
            world.heading_servo = Float32HeadingHeadroomServo()
            try:
                recorded = rows[name]
                actions = np.load(folder / (name + '--window-1-actions-float32.npy'))
                for step in suite['capture_after_control_steps']:
                    path = folder / 'states' / f'{name}-step-{step}.json'
                    # The containing receipt manifest was verified before deserialization.
                    state = load_state(path, folder / 'snapshot-blobs')
                    assert np.array_equal(state['data'].qpos, recorded[step-1]['qpos'])
                    target = clone_world(world)
                    try:
                        restore_state(target, state)
                        reproduced = 0
                        for index in range(step, min(step+25, len(recorded))):
                            expected = recorded[index]
                            target.step_command(expected['command'])
                            assert target.last_action.tobytes() == actions[index].tobytes()
                            assert target.last_observation[0].tobytes() == np.asarray(expected['actor_observation'], np.float32).tobytes()
                            assert np.array_equal(target.core.data.qpos, expected['qpos'])
                            assert np.array_equal(target.core.data.qvel, expected['qvel'])
                            reproduced += 1
                        continuations.append(dict(pair=pair, session=name, start_step=step,
                            source_index_sha256=digest(path), exact_controls=reproduced))
                    finally:
                        target.close()
                    if step == 657:
                        actor = world.standing_policy
                        stand_action = actor.infer(np.asarray(recorded[step]['actor_observation'], np.float32)[None])[0][0]
                        fifo = np.asarray(state['motor_history'])
                        details[pair]['handoffs'][name] = dict(
                            pre_handoff_tilt_deg=recorded[step-1]['tilt_deg'],
                            pre_handoff_speed_m_s=recorded[step-1]['speed_m_s'],
                            first_standing_action_jump_rad=float(abs(stand_action-state['last_action']).max()),
                            fifo_min_rad=float(fifo.min()), fifo_max_rad=float(fifo.max()),
                            yaw_at_13_3_s_rad_s=recorded[664]['yaw_rate_rad_s'],
                            tilt_at_13_5_s_deg=recorded[674]['tilt_deg'])
            finally:
                world.close()
    assert len(continuations) == 16 and all(r['exact_controls'] == 25 for r in continuations)
    report = dict(complete=True, controls=controls, continuations=continuations, details=details,
                  boundary='Matched exposed diagnosis and exact continuation, not actor causality or physical calibration.')
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    shutil.copy2(__file__, args.output / Path(__file__).name)
    (args.output / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n'
        for p in sorted(args.output.iterdir()) if p.is_file() and p.name != 'SHA256SUMS'))
    print(json.dumps(dict(complete=True, reproduced_controls=sum(x['action_rows'] for x in controls.values()),
                         exact_state_continuations=len(continuations), details={k:v['handoffs'] for k,v in details.items()})))


if __name__ == '__main__':
    main()
