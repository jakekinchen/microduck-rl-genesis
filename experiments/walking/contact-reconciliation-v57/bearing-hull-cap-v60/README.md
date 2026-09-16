# V60 bearing hull-cap comparison

The bearing passes the sampled geometry and compiler-compatibility checks.
This is one component's result; the complete robot model is not admitted.

Only `max_convex_hull` changes from V58's 64 to 256. The source STL, worker
bytes, CoACD version, seed, metric threshold and every other generation
setting are retained. One attempt completed in 7.690 seconds, followed by
13.352 seconds of independent validation, within 120/180-second limits.
No retries or parameter searches occurred.

| Check | V58, cap 64 | V60, cap 256 | Requirement |
|---|---:|---:|---:|
| Maximum sampled excess material | 0.343090 mm | 0.217129 mm | ≤0.25 mm |
| Maximum sampled missing material | 0.141548 mm | 0.162090 mm | ≤0.25 mm |
| Watertight parts | 64/64 | 256/256 | Every part |
| Convex parts | 63/64 | 256/256 | Every part |

The fixed source bank has 8,192 points. The V60 proxy bank has 10,801 points,
including every proxy vertex and the same deterministic face-sampling rule.
The changed proxy tessellation changes the available proxy samples; this is
not a global error bound or an identical point-by-point proxy-surface bank.
No cavity-pair acceptance is claimed by the bearing-only material evaluation.

A separately frozen assembly check replaces only the neck bearing in the
V57 full-CAD reference, using shell mesh inertia on generated assets and
preserving explicit body inertia. All 62 checked physical/actuator arrays,
orders, source geom contact properties and power-support coverage match. The
325-collider diagnostic model compiles; all 256 proxy vertex clouds preserve
world position to within 0.520 nanometers. Assembly inspection took 2.575 seconds.

Its 201 copied poses still contain overlap from the unrepaired head/jaw shapes.
That expected partial-model failure is preserved in `assembly/pose-results.json`.
Neither the bearing pass nor compiler success certifies the full robot or any
dynamic behavior.

`protocol.json`/`plan.json`, raw generated archives, `material-result.json`,
`assembly-bank.json`/`assembly-plan.json` and `assembly/result.json` bind the
two distinct stages. The passing bearing permits one fixed application of the
same recipe to the remaining three shapes in `../head-hull-cap-v61/`. The
complete-material, cavity, assembly and dynamic/load gates remain separate.
