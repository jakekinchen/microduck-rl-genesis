"""Failure margins and paired development summaries, never automatic promotion."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class Gate:
    name: str
    threshold: float
    unit: str
    direction: str = "max"
    hard_failure: bool = False

    def __post_init__(self):
        if not self.name or not self.unit or self.direction not in ("max", "min"):
            raise ValueError("named gate, unit and max/min direction required")
        if isinstance(self.threshold, bool) or not math.isfinite(self.threshold):
            raise ValueError("finite numeric threshold required")

    def score(self, value: float | None) -> dict:
        result = asdict(self)
        if value is None or isinstance(value, bool) or not math.isfinite(value):
            return dict(result, value=None, status="missing", margin=None,
                        relative_margin=None)
        margin = self.threshold - value if self.direction == "max" else value - self.threshold
        return dict(result, value=value, status="pass" if margin >= 0 else "fail",
                    margin=margin,
                    relative_margin=margin / abs(self.threshold) if self.threshold else None)


def score_case(gates: Iterable[Gate], values: dict) -> dict:
    gates = list(gates)
    if not gates or len({g.name for g in gates}) != len(gates):
        raise ValueError("nonempty, uniquely named gates required")
    scored = [g.score(values.get(g.name)) for g in gates]
    return {"passed": all(g["status"] == "pass" for g in scored), "gates": scored,
            "hard_failures": [g["name"] for g in scored
                              if g["hard_failure"] and g["status"] == "fail"],
            "missing": [g["name"] for g in scored if g["status"] == "missing"],
            "proof_class": "exposed_development", "physical_acceptance": False}


def paired_summary(records: list[dict], seeds: list[int], arms: tuple[str, str]) -> dict:
    """Require one completed run/arm/seed and the same frozen comparison identity.

    A run summary must include all required cases, even failed/missing ones.
    Independent training seeds are not inferred from repeated evaluation rows.
    """
    if len(seeds) < 3 or len(set(seeds)) != len(seeds) or len(set(arms)) != 2:
        raise ValueError("at least three unique seeds and two distinct arms required")
    if any(type(s) is not int for s in seeds):
        raise ValueError("integer training seeds required")
    expected = {(s, a) for s in seeds for a in arms}
    runs = {}
    identities = set()
    for r in records:
        key = (r["training_seed"], r["arm"])
        if key not in expected or key in runs:
            raise ValueError("unexpected or duplicate seed/arm")
        if r["status"] != "completed" or r["split"] != "exposed_development":
            raise ValueError("completed exposed-development runs required")
        ids = tuple(sorted(r["required_case_ids"]))
        if not ids or len(set(ids)) != len(ids) or set(r["cases"]) != set(ids):
            raise ValueError("complete unique case denominator required")
        if any(type(v) is not bool for v in r["cases"].values()):
            raise ValueError("case results must be booleans; missing is not a pass")
        identities.add((r["comparison_sha256"], r["bank_sha256"],
                        r["model_sha256"], r["gates_sha256"], ids))
        runs[key] = r
    if set(runs) != expected or len(identities) != 1:
        raise ValueError("missing run or unmatched protocol/model/bank/gates")
    return {"training_seeds": seeds, "arms": list(arms),
            "per_seed": [{"seed": s, "passes": {a: sum(runs[s, a]["cases"].values())
                          for a in arms}} for s in seeds],
            "required_cases_per_run": len(next(iter(identities))[-1]),
            "all_cases_pass": {a: all(all(runs[s, a]["cases"].values()) for s in seeds)
                               for a in arms},
            "automatic_promotion": False, "physical_acceptance": False}
