"""Reward-independent classification for the frozen V63 local probes."""
import hashlib
import numpy as np
from experiments.walking.self_load import evaluate_self_load


def strict_action(value):
    value = np.asarray(value)
    if value.dtype != np.dtype('float32') or value.shape != (14,) or not np.isfinite(value).all():
        raise ValueError('expected exactly fourteen finite float32 action values')
    return value.copy()


def classify(rows, case, thresholds, timing):
    expected = round(case['duration_s']/.005)
    failures = []
    complete = len(rows) == expected
    if not complete:
        failures.append('incomplete_duration')
    if not rows:
        return {'passed': False, 'failures': failures+['missing_physics_evidence']}
    values = np.array([[r['time_s'], r['root_z_m'], r['tilt_deg'], r['speed_m_s'],
                        r['angular_speed_rad_s'], r['internal_penetration_m'], r['ground_penetration_m'],
                        r['total_normal_n'], r['largest_pair_normal_n'], r['joint_margin_rad'],
                        r['motor_torque_max_nm'], r['nonsole_ground_load_n']] for r in rows])
    if not np.isfinite(values).all() or any(abs(r['time_s']-(i+1)*.005)>1e-8 for i,r in enumerate(rows)):
        failures.append('invalid_or_unordered_physics_evidence')
    load = evaluate_self_load([
        {'interval_start_s': i*.005, 'total_normal_n': r['total_normal_n'],
         'largest_pair_normal_n': r['largest_pair_normal_n']} for i,r in enumerate(rows)], case['duration_s'])
    if max(r['internal_penetration_m'] for r in rows) > thresholds['maximum_internal_penetration_m']:
        failures.append('internal_penetration')
    if max(r['ground_penetration_m'] for r in rows) > thresholds['maximum_ground_penetration_m']:
        failures.append('ground_penetration')
    if min(r['joint_margin_rad'] for r in rows) < -thresholds['maximum_joint_overshoot_rad']:
        failures.append('joint_stop_overshoot')
    if any(r['warnings'] for r in rows):
        failures.append('mujoco_warning')
    fallen = [r for r in rows if r['fell']]
    tail = [r for r in rows if r['time_s'] > case['duration_s']-1.]
    if case['mode'] == 'passive':
        if any(r['motor_torque_max_nm'] != 0 or r['actuator_force_max_nm'] != 0 for r in rows):
            failures.append('nonzero_passive_motor_torque')
        if len(tail) != 200 or max(r['speed_m_s'] for r in tail) > thresholds['passive_final_speed_m_s']:
            failures.append('passive_not_settled_linear')
        if len(tail) != 200 or max(r['angular_speed_rad_s'] for r in tail) > thresholds['passive_final_angular_speed_rad_s']:
            failures.append('passive_not_settled_angular')
        bracing_applicable = False
    else:
        bracing_applicable = True
        if fallen:
            failures.append('fall')
        if min(r['joint_margin_rad'] for r in rows) < thresholds['active_minimum_joint_margin_rad']:
            failures.append('actual_joint_margin')
        failures.extend(load['failures'])
        if any(r['nonsole_ground_load_n'] > thresholds['maximum_nonsole_ground_load_n'] for r in rows):
            failures.append('nonsole_support')
        if max(r['motor_torque_max_nm'] for r in rows) > thresholds['motor_torque_limit_nm']+1e-9:
            failures.append('motor_torque_limit')
        if case['mode'] == 'home':
            settled = [r for r in rows if r['time_s'] >= 1.]
            if not settled or max(r['tilt_deg'] for r in settled) > thresholds['home_max_tilt_deg']:
                failures.append('home_tilt')
            if not settled or max(r['xy_displacement_m'] for r in settled) > thresholds['home_max_drift_m']:
                failures.append('home_drift')
    cycle_ns = np.asarray(timing['control_ns'], dtype=np.int64)
    physics_ns = np.asarray(timing['physics_ns'], dtype=np.int64)
    perf = {'physics_step_median_ms': float(np.median(physics_ns)/1e6),
            'physics_step_p99_ms': float(np.quantile(physics_ns,.99)/1e6),
            'measured_control_intervals': len(cycle_ns),
            'control_p99_ms': float(np.quantile(cycle_ns,.99)/1e6) if len(cycle_ns) else None,
            'control_deadline_miss_fraction': float(np.mean(cycle_ns>20e6)) if len(cycle_ns) else None,
            'scope': 'serial local execution; control includes BAM, physics and load observation, excludes file encoding'}
    perf['provisional_50hz_budget_passed'] = bool(complete and len(cycle_ns)==expected//4
        and perf['control_p99_ms']<=20. and perf['control_deadline_miss_fraction']<=.01)
    return {'passed': not failures, 'failures': sorted(set(failures)), 'completed': complete,
            'observed_physics_steps': len(rows), 'expected_physics_steps': expected,
            'first_fall_s': fallen[0]['time_s'] if fallen else None,
            'maximum_tilt_deg': max(r['tilt_deg'] for r in rows),
            'minimum_root_height_m': min(r['root_z_m'] for r in rows),
            'maximum_internal_penetration_m': max(r['internal_penetration_m'] for r in rows),
            'maximum_ground_penetration_m': max(r['ground_penetration_m'] for r in rows),
            'maximum_internal_load_n': max(r['total_normal_n'] for r in rows),
            'maximum_nonsole_ground_load_n': max(r['nonsole_ground_load_n'] for r in rows),
            'minimum_joint_margin_rad': min(r['joint_margin_rad'] for r in rows),
            'near_joint_stop_fraction': float(np.mean([r['joint_margin_rad'] < thresholds['active_minimum_joint_margin_rad'] for r in rows])),
            'load_gate': load, 'upright_bracing_gate_applicable': bracing_applicable,
            'performance': perf, 'walking_accepted': False, 'physical_acceptance': False}


def dynamics_digest(arrays):
    result = hashlib.sha256()
    for name,value in sorted(arrays.items()):
        array = np.ascontiguousarray(value)
        result.update(name.encode()+str(array.shape).encode()+array.dtype.str.encode()+array.tobytes())
    return result.hexdigest()
