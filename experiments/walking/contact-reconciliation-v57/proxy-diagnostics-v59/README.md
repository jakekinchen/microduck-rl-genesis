# V59 compiler and independent geometry diagnostics

The isolated compiler change passes its checks. V58's material-error rejection
remains unchanged. No dynamics, policy inference or model admission occurred.

The unchanged V58 XML still fails compilation at bearing fragment 52. A new
XML changes only that mesh asset's `inertia` attribute to `shell`; all vertices,
faces, collision masks, explicit body inertias and other XML attributes stay
unchanged. This follows the documented [MuJoCo mesh-inertia setting](https://mujoco.readthedocs.io/en/stable/XMLreference.html#asset-mesh-inertia).
The setting is a compiler representation choice, not measurement-based
calibration or an assertion that the physical bearing is a thin shell.

The new model compiles with 322 active robot colliders. All 62 checked body,
joint and actuator arrays match the V57 full-CAD reference exactly; body,
joint and actuator order also match. Every original geom's effective contact
properties carry through to its replacement parts. There are no body
exclusions, all geoms have unique names, and power-support/leg pairs remain
eligible. All 256 compiled proxy shapes preserve their input world vertices
to within 3.7393 nanometers, below the frozen 100-nanometer numerical limit.

The fixed 201-pose bank has no recorded internal penetration. This is copied
kinematic-state evidence, not a load, stability or endurance result. The model
still uses V58's four rejected material approximations and cannot enter dynamics
or training as an accepted replacement.

## Geometry verification that survives compiler failure

`material_validation.py` is import-safe and uses no simulator. Each mesh gets
an independent result even if another archive is missing, malformed or fails
geometry processing. Original STL/archive/metadata hashes are checked. The
0.25 mm missing/excess material limits, deterministic 4,096-index sampling,
watertightness, convexity and per-side cavity requirements remain unchanged.
Absent cavity banks are explicitly unevaluated.

All 44 directly compared V58 material fields reproduce exactly, including the
four failures. All eight source-local cavity witnesses pass independently.
The real-mesh regression took 22.629 seconds against a 360-second limit.
Nine synthetic tests cover positive and negative material cases, malformed or
missing inputs, nonconvex geometry, cavity-side semantics and continued checks
after an individual error. All nine pass.

## Records and decision

- `protocol.json` and `implementation.lock.json` bind the two compiler cases
  before execution, with 60/240-second limits and 77 source inputs.
- `baseline/result.json` retains the unchanged compiler failure.
- `shell-fragment/result.json`, `pair-matrix.json`, `compiled-geometry.json`
  and `pose-results.json` retain the newly available model diagnostics.
- `compiler-review.json` records the sole XML change and checked outcomes.
- `material-bank.json` and `material-plan.json` separately freeze the material
  regression; `material-result` is named `material-regression.json` here.
- `material-review.json` records exact agreement with V58's failed metrics.

Compiler-case durations were 0.553 and 0.883 seconds. All owned processes were
reaped. The next bounded geometry experiment is the bearing-only 64-to-256
hull-cap comparison in `../bearing-hull-cap-v60/`. Broader model admission still
requires accurate materials, completed assembly/contact checks, separately
frozen dynamics/load probes and the behavior acceptance standard.
