"""Explicit interventions for the exposed V64 contact diagnostic, never deployment."""
import numpy as np

SHELLS = ('ankle_left_3_foot_left_collision', 'ankle_right_7_foot_right_collision')
PHYSICAL = ('body_parentid', 'body_pos', 'body_quat', 'body_mass', 'body_inertia',
            'body_ipos', 'body_iquat', 'jnt_type', 'jnt_bodyid', 'jnt_pos', 'jnt_axis',
            'jnt_range', 'jnt_limited', 'jnt_stiffness', 'jnt_solref', 'jnt_solimp',
            'dof_armature', 'dof_damping', 'dof_frictionloss', 'dof_solref', 'dof_solimp',
            'actuator_trnid', 'actuator_gear', 'actuator_gainprm', 'actuator_biasprm',
            'actuator_forcerange', 'actuator_ctrlrange')


def clock_subdivisions(dt):
    if dt not in (.005, .0025, .00125):
        raise ValueError('Only preregistered integration steps are permitted')
    return round(.005 / dt)


def match_export(robot, reference):
    """Copy body/inertial/joint XML only. Keep every original candidate geom."""
    bodies = {b.get('name'): b for b in robot.findall('.//body')}
    originals = {b.get('name'): b for b in reference.findall('.//body')}
    if list(bodies) != list(originals):
        raise ValueError('body identity/order mismatch')
    changes = []
    for name, body in bodies.items():
        source = originals[name]
        if body.attrib != source.attrib:
            changes.append({'body': name, 'element': 'body', 'before': dict(body.attrib), 'after': dict(source.attrib)})
        body.attrib.clear(); body.attrib.update(source.attrib)
        for tag in ('inertial', 'joint', 'freejoint'):
            left, right = body.findall(tag), source.findall(tag)
            if len(left) != len(right):
                raise ValueError(f'{name}: {tag} count mismatch')
            for old, new in zip(left, right):
                if old.get('name') != new.get('name'):
                    raise ValueError('joint identity mismatch')
                if old.attrib != new.attrib:
                    changes.append({'body': name, 'element': tag, 'before': dict(old.attrib), 'after': dict(new.attrib)})
                old.attrib.clear(); old.attrib.update(new.attrib)
    return changes


def mask_shell_floor(robot, scene):
    """Compile distinct floor bit; retain the internal-body bit on both shells."""
    found = []
    for geom in robot.findall('.//worldbody//geom'):
        if geom.get('contype') == '1' and geom.get('conaffinity') == '1':
            if geom.get('name') in SHELLS:
                found.append(geom.get('name'))
            else:
                geom.set('conaffinity', '3')
    if set(found) != set(SHELLS):
        raise ValueError('Both explicit full-model shell colliders are required')
    floor = scene.find(".//geom[@name='floor']")
    floor.set('contype', '2'); floor.set('conaffinity', '2')


def mask_changes(before_type, before_affinity, after_type, after_affinity):
    """Exhaustively compare the undirected compatibility predicate, in chunks."""
    n = len(before_type); changed = []
    for begin in range(0, n, 128):
        end = min(n, begin + 128)
        old = ((before_type[begin:end, None] & before_affinity) |
               (before_affinity[begin:end, None] & before_type)) != 0
        new = ((after_type[begin:end, None] & after_affinity) |
               (after_affinity[begin:end, None] & after_type)) != 0
        for row, col in np.argwhere(old != new):
            row += begin
            if row < col:
                changed.append([int(row), int(col), bool(old[row-begin, col]), bool(new[row-begin, col])])
    return changed


def load_gate(rows, duration, dt):
    """The same physical load limits, evaluated at every integration step."""
    expected = round(duration / dt); failures = []
    if len(rows) != expected:
        failures.append('incomplete_duration')
    flags = []; run = longest = 0
    for i, row in enumerate(rows):
        total, largest = row['total_normal_n'], row['largest_pair_normal_n']
        if (not np.isfinite([total, largest, row['time_s']]).all() or total < 0 or
                largest < 0 or largest > total + 1e-9 or abs(row['time_s']-(i+1)*dt) > 1e-8):
            failures.append('invalid_or_unordered_load_evidence')
        flag = total > 1.; flags.append(flag)
        run = run + 1 if flag else 0; longest = max(longest, run)
    fraction = sum(flags) / len(flags) if flags else None
    if fraction is not None and fraction > .01 + 1e-12:
        failures.append('sustained_self_load_occupancy')
    if longest * dt > .05 + 1e-12:
        failures.append('continuous_body_bracing')
    return {'passed': not failures, 'failures': failures, 'observed_samples': len(rows),
            'expected_samples': expected, 'total_over_1n_fraction': fraction,
            'longest_over_1n_s': longest*dt,
            'thresholds': {'total_load_n': 1., 'max_fraction': .01, 'max_continuous_s': .05},
            'boundary': 'Applied forces at every integration step; no physical calibration claim.'}
