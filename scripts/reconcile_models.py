#!/usr/bin/env python3
"""Reconcile committed official Microduck models with the repo-local bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
from importlib import metadata
from pathlib import Path

import mujoco

ROOT = Path(__file__).resolve().parents[1]
LOCAL_ROOT = ROOT / "microduck" / "assets" / "microduck"
OFFICIAL_SUBTREE = Path("src/mjlab_microduck/robot/microduck")
DEFAULT_OUTPUT = ROOT / "microduck_contract" / "model" / "reconciliation-v1.json"
VARIANTS = {
    "walk": "scene_walk.xml",
    "allcollisions": "scene.xml",
    "walk_backlash": "scene_walk_backlash.xml",
    "allcollisions_backlash": "scene_backlash.xml",
    "rollers": "scene_rollers.xml",
    "rollers_backlash": "robot_allcollisions_rollers_backlash.xml",
}
COMPILED_MANIFEST_SIGNIFICANT_DIGITS = 14


def command(*args: str, cwd: Path) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_compiled_manifest(value: object) -> object:
    """Remove only host floating tails from compiled-model evidence.

    MuJoCo's mesh inertia compiler differs by one or a few ULPs between the
    Darwin arm64 and Linux x86-64 builds. Fourteen significant decimal digits
    retains substantially more precision than any model acceptance threshold
    while mapping those measured tails to one representation.
    """
    if isinstance(value, float):
        canonical = float(format(value, f".{COMPILED_MANIFEST_SIGNIFICANT_DIGITS}g"))
        return 0.0 if canonical == 0.0 else canonical
    if isinstance(value, list):
        return [canonical_compiled_manifest(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_compiled_manifest(item) for key, item in value.items()}
    return value


def name(model: mujoco.MjModel, obj_type, index: int) -> str:
    return mujoco.mj_id2name(model, obj_type, index) or f"<unnamed:{index}>"


def compiled_manifest(path: Path) -> dict:
    model = mujoco.MjModel.from_xml_path(os.fspath(path))
    bodies = [
        {
            "name": name(model, mujoco.mjtObj.mjOBJ_BODY, index),
            "mass_kg": float(model.body_mass[index]),
            "inertia_kg_m2": model.body_inertia[index].astype(float).tolist(),
            "inertial_position_m": model.body_ipos[index].astype(float).tolist(),
        }
        for index in range(model.nbody)
    ]
    joints = [
        {
            "name": name(model, mujoco.mjtObj.mjOBJ_JOINT, index),
            "type": int(model.jnt_type[index]),
            "range": model.jnt_range[index].astype(float).tolist(),
            "limited": int(model.jnt_limited[index]),
            "armature": float(model.dof_armature[model.jnt_dofadr[index]]),
            "damping": float(model.dof_damping[model.jnt_dofadr[index]]),
            "frictionloss": float(model.dof_frictionloss[model.jnt_dofadr[index]]),
        }
        for index in range(model.njnt)
    ]
    actuators = []
    for index in range(model.nu):
        target_id = int(model.actuator_trnid[index, 0])
        target = (
            name(model, mujoco.mjtObj.mjOBJ_JOINT, target_id)
            if int(model.actuator_trntype[index]) == int(mujoco.mjtTrn.mjTRN_JOINT)
            else f"object:{target_id}"
        )
        actuators.append(
            {
                "name": name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, index),
                "target": target,
                "transmission_type": int(model.actuator_trntype[index]),
                "gain_type": int(model.actuator_gaintype[index]),
                "bias_type": int(model.actuator_biastype[index]),
                "control_range": model.actuator_ctrlrange[index]
                .astype(float)
                .tolist(),
                "force_range": model.actuator_forcerange[index]
                .astype(float)
                .tolist(),
            }
        )
    collision_geoms = [
        {
            "name": name(model, mujoco.mjtObj.mjOBJ_GEOM, index),
            "body": name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[index])),
            "type": int(model.geom_type[index]),
            "contype": int(model.geom_contype[index]),
            "conaffinity": int(model.geom_conaffinity[index]),
            "group": int(model.geom_group[index]),
        }
        for index in range(model.ngeom)
        if model.geom_contype[index] or model.geom_conaffinity[index]
    ]
    keyframes = [
        {
            "name": name(model, mujoco.mjtObj.mjOBJ_KEY, index),
            "qpos": model.key_qpos[index].astype(float).tolist(),
            "ctrl": model.key_ctrl[index].astype(float).tolist(),
        }
        for index in range(model.nkey)
    ]
    return {
        "counts": {
            field: int(getattr(model, field))
            for field in (
                "nq",
                "nv",
                "nu",
                "nbody",
                "njnt",
                "ngeom",
                "nkey",
            )
        },
        "bodies": bodies,
        "joints": joints,
        "actuators": actuators,
        "collision_geoms": collision_geoms,
        "keyframes": keyframes,
    }


def relevant_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".part"}
    )


def materialize_official(repo: Path, commit: str, destination: Path) -> Path:
    archive = destination / "official.tar"
    subprocess.check_call(
        [
            "git",
            "archive",
            "--format=tar",
            "-o",
            os.fspath(archive),
            commit,
            os.fspath(OFFICIAL_SUBTREE),
        ],
        cwd=repo,
    )
    with tarfile.open(archive) as stream:
        stream.extractall(destination, filter="data")
    return destination / OFFICIAL_SUBTREE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-repo", required=True, type=Path)
    parser.add_argument("--official-commit", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo = args.official_repo.resolve()
    commit = command("git", "rev-parse", f"{args.official_commit}^{{commit}}", cwd=repo)
    tree = command("git", "show", "-s", "--format=%T", commit, cwd=repo)
    commit_date = command("git", "show", "-s", "--format=%aI", commit, cwd=repo)

    with tempfile.TemporaryDirectory(prefix="microduck-model-authority-") as temp:
        official_root = materialize_official(repo, commit, Path(temp))
        sources = []
        unresolved = []
        deferred = []
        for local_path in relevant_files(LOCAL_ROOT):
            relative = local_path.relative_to(LOCAL_ROOT)
            official_path = official_root / relative
            local_digest = sha256(local_path)
            official_digest = sha256(official_path) if official_path.exists() else None
            if local_digest == official_digest:
                classification = "byte-identical-input"
            elif relative.as_posix() == "ball.xml":
                classification = "unresolved-divergence-outside-slice"
            else:
                classification = "unresolved-divergence"
            row = {
                "path": relative.as_posix(),
                "local_sha256": local_digest,
                "official_sha256": official_digest,
                "classification": classification,
            }
            sources.append(row)
            if classification == "unresolved-divergence":
                unresolved.append({"scope": "source", **row})
            elif classification == "unresolved-divergence-outside-slice":
                deferred.append(
                    {
                        "scope": "ball-model-outside-slice-006",
                        **row,
                        "note": (
                            "Official ball geom adds priority=1; repo-local ball omits "
                            "it. Ball semantics remain open and are not used by the "
                            "six reconciled variants."
                        ),
                    }
                )

        official_only = sorted(
            path.relative_to(official_root).as_posix()
            for path in official_root.rglob("*.part")
        )
        variants = {}
        for variant, relative in VARIANTS.items():
            local_path = LOCAL_ROOT / relative
            official_path = official_root / relative
            local_manifest = compiled_manifest(local_path)
            official_manifest = compiled_manifest(official_path)
            equal = local_manifest == official_manifest
            differences = sorted(
                key
                for key in local_manifest
                if local_manifest[key] != official_manifest[key]
            )
            classification = (
                "semantically-identical-compiled-model"
                if equal
                else "unresolved-divergence"
            )
            variants[variant] = {
                "root": relative,
                "input_classification": (
                    "byte-identical-input"
                    if sha256(local_path) == sha256(official_path)
                    else "unresolved-divergence"
                ),
                "compiled_classification": classification,
                "local_manifest_sha256": digest_json(local_manifest),
                "official_manifest_sha256": digest_json(official_manifest),
                "differing_sections": differences,
                "manifest": local_manifest,
            }
            if not equal:
                unresolved.append(
                    {
                        "scope": "compiled-model",
                        "variant": variant,
                        "differing_sections": differences,
                    }
                )

    walk_digest = variants["walk"]["local_manifest_sha256"]
    relationships = {
        variant: {
            "relative_to": "walk",
            "classification": (
                "same-variant" if variant == "walk" else "expected-variant-difference"
            ),
            "semantic_manifest_equal": row["local_manifest_sha256"] == walk_digest,
        }
        for variant, row in variants.items()
    }
    model_locks = {}
    for path in sorted((ROOT / "microduck_contract" / "model").glob("*.lock.json")):
        if path.name == "reconciliation-v1.lock.json":
            continue
        model_locks[path.name] = sha256(path)
    payload = {
        "schema_version": "microduck.model-reconciliation/v1",
        "official_authority": {
            "repository": "pollen-robotics/microduck-rl",
            "commit": commit,
            "tree": tree,
            "commit_date": commit_date,
            "subtree": OFFICIAL_SUBTREE.as_posix(),
        },
        "generation": {
            "script": "scripts/reconcile_models.py",
            "mujoco_version": metadata.version("mujoco"),
        },
        "local_model_locks": model_locks,
        "source_comparison": {
            "files": sources,
            "official_only_nonruntime_part_files": official_only,
        },
        "variants": variants,
        "variant_relationships": relationships,
        "unresolved_divergences": unresolved,
        "deferred_divergences": deferred,
        "evidence_boundary": (
            "Structural and selected numerical model agreement only; no contact, "
            "task, policy, transfer, or physical-success claim."
        ),
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json_bytes(payload))
    try:
        display = output.relative_to(ROOT)
    except ValueError:
        display = output
    print(
        f"wrote {display}: {len(sources)} sources, "
        f"{len(variants)} variants, {len(unresolved)} in-scope unresolved, "
        f"{len(deferred)} deferred"
    )
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
