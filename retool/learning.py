"""Transition-aware replay and read-only actor-gradient diagnostics."""
from __future__ import annotations

import itertools
import math
import numpy as np

PHASES = ("initial_stand", "start", "walk", "brake", "settle", "stand", "restart")


def transition_labels(observations, env_ids, episode_ids, control_steps,
                      onset_controls=10, settle_controls=50):
    """Label chronological rows per environment, never crossing episode resets.

    Metadata is mandatory: concatenated cases cannot be treated as one trajectory.
    New episodes must begin at control zero; within-episode gaps are rejected.
    Phase windows are sampling strata, not claims that physical settling occurred.
    """
    obs = np.asarray(observations)
    meta = [np.asarray(x) for x in (env_ids, episode_ids, control_steps)]
    if obs.ndim != 2 or obs.shape[1] != 61 or not len(obs) or not np.isfinite(obs).all():
        raise ValueError("nonempty finite N x 61 observations required")
    if any(a.shape != (len(obs),) or a.dtype.kind not in "iu" or (a < 0).any() for a in meta):
        raise ValueError("nonnegative integer row-aligned environment/episode/control metadata required")
    if not (type(onset_controls) is int and type(settle_controls) is int
            and 0 < onset_controls < settle_controls):
        raise ValueError("positive ordered phase windows required")
    states, labels = {}, []
    for row, env, ep, step in zip(obs, *meta):
        moving = bool(np.any(row[48:51] != 0))
        old = states.get(int(env))
        if old is None or ep != old["episode"]:
            if step != 0 or (old is not None and ep <= old["episode"]):
                raise ValueError("episodes must advance and start at control zero")
            state = dict(episode=int(ep), step=0, moving=moving, age=0,
                         seen_walk=moving, restart=False)
        else:
            if step != old["step"] + 1:
                raise ValueError("missing, duplicated or out-of-order control row")
            state = dict(old, step=int(step), age=old["age"] + 1)
            if moving != old["moving"]:
                state.update(moving=moving, age=0,
                             restart=bool(moving and old["seen_walk"]))
            state["seen_walk"] = old["seen_walk"] or moving
        if moving:
            label = ("restart" if state["restart"] else "start") if state["age"] < onset_controls else "walk"
        elif not state["seen_walk"]:
            label = "initial_stand"
        else:
            label = "brake" if state["age"] < onset_controls else "settle" if state["age"] < settle_controls else "stand"
        states[int(env)] = state
        labels.append(label)
    return np.asarray(labels)


def balanced_replay_indices(labels, rng: np.random.Generator, per_phase=64, phases=PHASES, total_count=None):
    """Equal presentations per declared phase; no silent empty-pool fallback."""
    labels = np.asarray(labels)
    if labels.ndim != 1 or type(per_phase) is not int or per_phase <= 0:
        raise ValueError("one-dimensional labels and positive sample count required")
    phases = tuple(phases)
    if not phases or len(set(phases)) != len(phases) or set(phases) - set(PHASES):
        raise ValueError("unique known phases required")
    pools = [np.flatnonzero(labels == p) for p in phases]
    missing = [p for p, pool in zip(phases, pools) if not len(pool)]
    if missing:
        raise ValueError("missing replay phases: " + ", ".join(missing))
    if total_count is not None:
        if type(total_count) is not int or total_count < len(phases):
            raise ValueError("total replay count must cover every phase")
        base, extra = divmod(total_count, len(phases))
        counts = [base + (i < extra) for i in range(len(phases))]
    else:
        counts = [per_phase] * len(phases)
    return np.concatenate([rng.choice(pool, count, replace=True)
                           for pool, count in zip(pools, counts)])


def actor_gradient_diagnostics(losses: dict, parameters) -> dict:
    """Inspect actor gradients without assigning .grad or consuming random state.

    Pass weighted loss terms to measure their actual contribution to the update.
    None denotes an undefined cosine (a zero gradient), never fake agreement.
    """
    import torch
    params = tuple(p for p in parameters if p.requires_grad)
    if not params or not losses:
        raise ValueError("trainable parameters and named scalar losses required")
    gradients, norms = {}, {}
    for name, loss in losses.items():
        if loss.ndim != 0 or not bool(torch.isfinite(loss)):
            raise ValueError("finite scalar losses required")
        pieces = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True) if loss.requires_grad else (None,) * len(params)
        # Accumulate on CPU in float64 without requiring MPS float64 support.
        flat = torch.cat([(torch.zeros_like(p) if g is None else g).detach().cpu().reshape(-1).double()
                          for p, g in zip(params, pieces)])
        if not bool(torch.isfinite(flat).all()):
            raise ValueError("nonfinite diagnostic gradient")
        gradients[name] = flat
        norms[name] = float(torch.linalg.vector_norm(flat))
    cosine = {}
    for a, b in itertools.combinations(losses, 2):
        denominator = norms[a] * norms[b]
        cosine[a + "/" + b] = (float(torch.dot(gradients[a], gradients[b])) / denominator
                                if denominator else None)
    return {"gradient_l2": norms, "gradient_cosine": cosine}


def standing_face_cost(face_world, standing, weight, target_deg=25., scale_deg=5.):
    """World-space orientation objective. This does not alter the 30-degree gate."""
    face = np.asarray(face_world, dtype=float)
    if face.shape != (3,) or not np.isfinite(face).all() or abs(np.linalg.norm(face) - 1) > 1e-5:
        raise ValueError("finite unit world-space face vector required")
    if not all(math.isfinite(x) for x in (weight, target_deg, scale_deg)) or weight < 0 or not 0 <= target_deg < 90 or scale_deg <= 0:
        raise ValueError("invalid objective parameters")
    pitch = math.degrees(math.asin(float(np.clip(abs(face[2]), 0, 1))))
    return weight * (max(0., pitch - target_deg) / scale_deg) ** 2 if standing else 0.
