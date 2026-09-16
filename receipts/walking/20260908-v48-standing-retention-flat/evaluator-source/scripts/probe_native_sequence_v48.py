"""Verify 24 materialized cells and both full-state reset origins twice."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_laser import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    from microduck.native_sequence_env_v48 import make_templates, preview, AssignedAction, request_at, BUCKETS
    from microduck.native_standing_env_v42 import clone_world
    from experiments.walking.handoff_inspection_v47 import restore_state
    from scripts.train_native_standing_retention_v48 import binding, FREEZE
    assert binding() == json.loads(FREEZE.read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    templates = make_templates(args.output)
    reports = []
    for bucket, (original, home, prebrake) in enumerate(templates):
        candidate = clone_world(original)
        adapter = AssignedAction()
        candidate.walking_policy = candidate.standing_policy = adapter
        try:
            for kind, state, start in [('home', home, 0), ('prebrake', prebrake, 650)]:
                reference, repeats = [], []
                for repeat in range(2):
                    for world in (original, candidate):
                        restore_state(world, state)
                    for offset in range(900):
                        command = request_at(start+offset, bucket, 0)
                        predicted = preview(candidate, command)
                        row = original.step_command(command)
                        adapter.expected, adapter.action, adapter.calls = predicted, original.last_action.copy(), 0
                        candidate.step_command(command)
                        assert adapter.calls == 1
                        for field in ['last_action', 'last_observation']:
                            assert getattr(original, field).tobytes() == getattr(candidate, field).tobytes(), field
                        for field in ['qpos', 'qvel', 'ctrl', 'qfrc_constraint', 'qfrc_actuator', 'efc_force']:
                            np.testing.assert_array_equal(getattr(original.core.data, field), getattr(candidate.core.data, field))
                        if repeat == 0:
                            reference.append(original.core.data.qpos.copy())
                        else:
                            np.testing.assert_array_equal(reference[offset], original.core.data.qpos)
                        if row['fell']:
                            break
                    repeats.append(offset+1)
                assert repeats[0] == repeats[1]
                reports.append(dict(bucket=bucket, cell=BUCKETS[bucket][0], origin=kind,
                    controls_per_repeat=repeats, exact_observation_action_bytes=True,
                    exact_physical_continuation=True, exact_nonaccumulating_full_reset=True,
                    baseline_fell=original.fell, materialized_motor_ticks=original.motor_ticks,
                    materialized_sensor_ticks=original.sensor_ticks, materialized_terrain=original.materialized_terrain,
                    materialized_domain=original.materialized_domain, home_qpos=home['data'].qpos.tolist()))
                print(json.dumps({k:reports[-1][k] for k in ['cell','origin','controls_per_repeat','baseline_fell']}), flush=True)
        finally:
            candidate.close()
            original.close()
    assert len(reports) == 48 and binding() == json.loads(FREEZE.read_text())
    (args.output / 'probe.json').write_text(json.dumps(dict(complete=True, passed=True, reports=reports), indent=2)+'\n')
    (args.output / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(args.output)}\n'
        for p in sorted(args.output.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS'))


if __name__ == '__main__':
    main()
