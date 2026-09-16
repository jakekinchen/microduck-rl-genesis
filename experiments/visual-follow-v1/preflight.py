"""Apply frozen domain validation to array stubs, without physics integration."""
from types import SimpleNamespace

import numpy as np
from experiments.walking.physical_domain import apply_domain


def check_cases(cases):
    records = []
    for case in cases:
        nominal = {"body_mass": np.ones(2), "body_inertia": np.ones((2, 3)), "geom_friction": np.ones((2, 3))}
        stub = SimpleNamespace(**{key: value.copy() for key, value in nominal.items()})
        domain = {"mass_inertia_scale": case["mass"], "sliding_friction_scale": case["friction"]}
        error = None
        try:
            apply_domain(stub, nominal, domain)
            if case["motor_ticks"] not in range(7):
                raise ValueError("unsupported motor lag")
        except ValueError as exc:
            error = str(exc)
        records.append({"case": case["id"], "domain": domain, "supported": error is None, "error": error})
    return {"all_supported": all(r["supported"] for r in records), "cases": records,
            "boundary": "Actual frozen apply_domain on numeric array stubs; no simulator model, stepping, rendering or behavioral evidence."}
