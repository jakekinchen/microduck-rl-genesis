"""Materialized V22 development perturbations; no calibrated-physics claim."""
import hashlib
import mujoco
import numpy as np
from experiments.walking.filtered_heading_world import FilteredHeadingWalkingWorld

FIELDS = ("body_mass", "body_inertia", "geom_friction")


def nominal_arrays(model):
    arrays = {key: getattr(model, key).copy() for key in FIELDS}
    for value in arrays.values():
        value.flags.writeable = False
    return arrays


def apply_domain(model, nominal, domain):
    if set(domain) != {"mass_inertia_scale", "sliding_friction_scale"}:
        raise ValueError("exact frozen domain factors required")
    mass, friction = domain["mass_inertia_scale"], domain["sliding_friction_scale"]
    if (type(mass) not in (int, float) or type(friction) not in (int, float)
            or mass not in (1., 1.1) or friction not in (.6, 1.)):
        raise ValueError("outside frozen exploratory domain")
    if not np.all(nominal["geom_friction"][:,0] == 1.):
        raise ValueError("this bank requires the original uniform unit sliding friction")
    # Reset from immutable nominal data, never multiply an already varied model.
    model.body_mass[:] = nominal["body_mass"] * mass
    model.body_inertia[:] = nominal["body_inertia"] * mass
    model.geom_friction[:] = nominal["geom_friction"]
    model.geom_friction[:,0] = nominal["geom_friction"][:,0] * friction
    return {"factors": dict(domain), "total_mass_kg": float(model.body_mass.sum()),
            "body_mass_kg": model.body_mass.tolist(), "body_inertia_kg_m2": model.body_inertia.tolist(),
            "geometry_friction": model.geom_friction.tolist(),
            "array_sha256": {key: hashlib.sha256(getattr(model,key).tobytes()).hexdigest() for key in FIELDS}}


class PhysicalDevelopmentWorld(FilteredHeadingWalkingWorld):
    def __init__(self, *args, domain, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.core
        initial = c.data.qpos.copy()
        self.nominal_physics = nominal_arrays(c.model)
        self.materialized_domain = apply_domain(c.model, self.nominal_physics, domain)
        self.expected_physics = {key: getattr(c.model, key).copy() for key in FIELDS}
        mujoco.mj_setConst(c.model, c.data)
        c.reset(initial[:3].tolist(), initial[3:7].tolist())
        np.testing.assert_array_equal(c.data.qpos, initial)
        self.checked_contact_samples = 0

    def step_command(self, command, action_override=None):
        row = super().step_command(command, action_override)
        c = self.core
        for key, expected in self.expected_physics.items():
            np.testing.assert_array_equal(getattr(c.model, key), expected)
        friction = [float(contact.friction[0]) for contact in c.data.contact]
        if friction:
            np.testing.assert_allclose(friction, self.materialized_domain["factors"]["sliding_friction_scale"], rtol=0, atol=1e-12)
            self.checked_contact_samples += len(friction)
        row["observed_contact_sliding_friction"] = friction
        return row
