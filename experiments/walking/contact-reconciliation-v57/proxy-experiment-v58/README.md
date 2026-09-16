# V58 bounded convex-proxy attempt — rejected

**All four generated proxies fail the sampled material-error gate.** The
combined model also fails MuJoCo compilation on a tiny bearing fragment. No
proxy, collision-model replacement or behavior is admitted. The original
models, scores, exclusions and frozen evaluator source remain unchanged.

One CoACD configuration was frozen before the first native call, with the
coordinator, worker, validator, input meshes and installed library hashes.
All four meshes received one attempt; no tuning or retry occurred.

## Frozen configuration and actual runtime

CoACD 1.0.14, seed 26091657: real-metric concavity threshold **0.00025 m**,
maximum 64 hulls, preprocessing off, resolution 1,000, MCTS nodes 20,
iterations 30, depth 3, merge on, PCA/decimation/extrusion off. The source
triangles were already watertight. Original CAD geometry was not repaired.

The four attempts were sequential, with a hard **120-second limit per mesh**
and **480-second total generation limit**. Independent validation had a separate
**360-second limit**. Generation finished in **152.766 seconds**; validation
terminated with an explicit error after **23.249 seconds**, without timing out.

| Mesh | Generation time | Hulls | Maximum sampled missing material | Maximum sampled excess material |
|---|---:|---:|---:|---:|
| Neck bearing | 10.793 s | 64 | .142 mm | **.343 mm** |
| Neck bracket | 12.441 s | 64 | .133 mm | **1.150 mm** |
| Bottom head shell | 103.916 s | 64 | .145 mm | **2.468 mm** |
| Jaw | 25.614 s | 64 | .226 mm | **1.066 mm** |

The tolerance is **.25 mm in either direction**. All four fail excess material.
Every native run separately warned that the 64-hull limit forced concavity
above its requested threshold. A successful native exit/export is not a pass.

The validator sampled deterministic source vertices and face centroids, all
proxy vertices and deterministic proxy face centroids: **32,204 source samples
and 31,598 proxy samples** in total. These are sampled surface/material errors,
not global Hausdorff, volume-union or contact-fidelity bounds. Three mesh sets
pass the tested convexity check; bearing part 37 fails Trimesh's convexity
predicate. All 256 parts are watertight.

`OMP_NUM_THREADS=2` was set but **did not enforce a native thread cap**. The
installed macOS build uses `std::thread::hardware_concurrency()` rather than
OpenMP. The isolated, timeout-bounded run with default native threading was
explicitly authorized. No library or system setting was patched. An advisory
guard check immediately preceded launch; no physics/rendering ran alongside it.

## Compile failure and unavailable gates

MuJoCo rejects `proxy_seeed_bearing__configuration__22x16x4_52` because its mesh
volume is too small. The unmodified fragment has six vertices, eight faces,
convex-hull volume **1.431e-16 m³**, and axis extents approximately
**4.89 × 17.19 × 10.90 micrometers**. It is watertight and genuinely
three-dimensional at stored precision; this is a compiler-scale compatibility
problem, not a license to silently delete the fragment.

The frozen validator stops at that compile failure. The following gates are
therefore **not evaluated**, and none is reported as a pass:

- Combined model's compiled mass, inertia, joint and actuator array equality.
- Its compiled unique names, power-support pair eligibility and full pair matrix.
- The complete frozen 201-pose penetration bank.
- The original validator's world-space cavity checks after model compilation.

The written XML intends 322 active robot colliders (70 minus four replaced
instances plus 256 convex parts), but there is **no successfully compiled
322-collider model**. The failed XML is preserved in `proxy-robot.xml`.
We did not apply MuJoCo's suggested shell-inertia setting, remove parts,
change exclusions, raise the tolerance or rerun generation in this pass.

## Separate posthoc checks

`review_artifacts_v58.py` verifies the frozen implementation hashes and every
saved part archive, then diagnoses the immutable outputs without compiling
the failed proxy model. It uses the original model's kinematic frames and
SciPy convex hulls of the generated vertices; no dynamics are stepped.

All **eight original contact-point cavity witnesses are preserved**: each side
whose point was outside the original CAD solid by more than .25 mm remains
outside that side's proxy union. This checks each side independently; moving
the other mesh away cannot hide a false-filled cavity. These pointwise results
show that decomposition addresses the identified cavity mechanism, but they
do not override the material-error failures or establish pair clearance.

The posthoc review is explicitly separate from the frozen validator. It neither
changes the initial failure nor fills the missing combined-model gates.

## Recommended next experiment

First resolve the **representation/validation prerequisite** on these immutable
outputs: classify all small fragments before model assembly and keep geometry
checks runnable when compilation fails. A separately versioned compiler probe
can test whether per-mesh shell inertia preserves exact body/actuator arrays
without changing any collision vertices. It must retain V58's rejected status;
dropping fragments or relaxing .25 mm is not an automatic fix.

Once that prerequisite is resolved, the next matched decomposition test should
change **only the hull cap from 64 to 256**, retaining the metric threshold,
seed, source meshes and other settings. The native warnings directly identify
forced merging at the existing cap as a source of excess approximation. Keep
finite time/storage limits and the same independent missing/excess material,
cavity and pose gates. Higher hull count may still fail; no new decomposition
or dynamic run was started as part of this recommendation.

## Records

- `protocol.json` and `implementation.lock.json`: pre-execution freezes.
- `generation.json`, per-mesh logs and `outputs/*/complete.json`: all four
  attempts, actual counts, durations and source/output hashes.
- `validation.json`, `validation.log`, `validation-process.json`: complete
  sampled error results and the terminal compilation failure.
- `posthoc-part-audit.json`, `posthoc-cavity-review.json`: separate immutable
  artifact diagnosis; no replacement of the original evaluator result.
- `closure.json`: final artifact hashes, failed/missing gates and process state.

CoACD's source documents the [real-metric API and parallel backends](https://github.com/SarahWeiii/CoACD/tree/1401ce2a7ae1ed89c65ab958b48d489350c233c7).
Pinned source excerpts and their hashes are retained under `source/` and
`source-provenance.json`. The installed library was used without installation
or modification. No owned process remained at the closing guard check.
