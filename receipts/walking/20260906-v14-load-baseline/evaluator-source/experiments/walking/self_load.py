"""Read applied native internal contact loads; never forward physical data."""
from contextlib import contextmanager
import math
import mujoco
import numpy as np

LOAD_N = 1.0
MAX_FRACTION = .01
MAX_CONTINUOUS_S = .05
DT = .005


def read_self_load(model, data):
    pairs = {}
    for index, contact in enumerate(data.contact):
        pair = tuple(sorted((int(contact.geom1), int(contact.geom2))))
        if not all(model.geom_bodyid[g] for g in pair):
            continue
        force = np.zeros(6)
        mujoco.mj_contactForce(model, data, index, force)
        if not np.isfinite(force).all():
            raise ValueError("nonfinite applied contact load")
        pairs[pair] = pairs.get(pair, 0.) + max(0., float(force[0]))
    return {"total_normal_n": sum(pairs.values()),
            "largest_pair_normal_n": max(pairs.values(), default=0.)}


@contextmanager
def record_self_loads(world):
    """Isolated-process observer; restores mj_step even after an exception."""
    original, samples = mujoco.mj_step, []

    def observed_step(model, data, *args, **kwargs):
        original(model, data, *args, **kwargs)
        if model is not world.core.model or data is not world.core.data:
            raise ValueError("unexpected physics step in isolated load observer")
        samples.append({"interval_start_s": len(samples)*DT, **read_self_load(model, data)})

    try:
        mujoco.mj_step = observed_step
        yield samples
    finally:
        mujoco.mj_step = original


def evaluate_self_load(samples, duration_s=18.):
    expected = round(duration_s/DT)
    failures = []
    if len(samples) != expected:
        failures.append("incomplete_duration")
    flags = []
    for index, sample in enumerate(samples):
        t, total, largest = (sample.get(k) for k in
                             ("interval_start_s", "total_normal_n", "largest_pair_normal_n"))
        if (not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (t, total, largest))
                or total < 0 or largest < 0 or largest > total + 1e-9
                or abs(t-index*DT) > 1e-8):
            failures.append("invalid_or_unordered_load_evidence")
            break
        flags.append(total > LOAD_N)
    fraction = sum(flags)/len(flags) if flags else None
    run = longest = 0
    for loaded in flags:
        run = run+1 if loaded else 0
        longest = max(longest, run)
    if fraction is not None and fraction > MAX_FRACTION + 1e-12:
        failures.append("sustained_self_load_occupancy")
    if longest*DT > MAX_CONTINUOUS_S + 1e-12:
        failures.append("continuous_body_bracing")
    return {"passed": not failures, "failures": failures,
            "observed_samples": len(samples), "expected_samples": expected,
            "total_over_1n_fraction": fraction, "longest_over_1n_s": longest*DT,
            "thresholds": {"total_load_n": LOAD_N, "max_fraction": MAX_FRACTION,
                           "max_continuous_s": MAX_CONTINUOUS_S},
            "boundary": "Applied 200-Hz native internal loads, not floor support or calibrated hardware forces."}
