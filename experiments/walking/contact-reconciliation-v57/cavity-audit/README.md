# V57 original-CAD cavity audit

**Convex-hull cavity filling is demonstrated at all eight inspected contact
witnesses.** No original-triangle crossing was found by the conservative
crossing test. This does not certify global pair clearance at every pose, and
it does not establish physical manufacturing clearance.

This is a targeted posthoc mechanism diagnosis of V57's rejection, not a fresh
acceptance bank. The two selected poses are contract HOME (yaw 0, z=.125 m) and
the preregistered sparse course bank's maximum-depth sample: nominal course,
control row 1,399, t=28.00 s. Neither original V57 manifests nor model exclusions
were edited. No physics, actuator, policy or geometry decomposition was run.

## Mesh and transform checks

The four implicated meshes—neck bearing, neck bracket, bottom head shell and
jaw—are each **one connected, watertight, consistently wound triangle surface**,
with positive signed volume and no degenerate triangles. No repairs, hole fills
or approximate vertex welding were performed: vertices were deduplicated only
when their stored coordinates were exactly equal. These topology properties
do not independently exclude self-intersecting surfaces.

Original source STL triangles were transformed through the original XML geom
and body frames. The resulting world vertices agree with the compiled MuJoCo
mesh vertices to at most **3.94e-9 m**. Thus the cavity result is not explained by
using untransformed or differently centered STL geometry.

## Concrete per-pair witnesses

For each pair, the deepest MuJoCo convex contact position was tested against
both original meshes. Every point lies strictly inside both convex hulls, but
three distinct fixed ray directions agree that it is **outside the original
head/jaw CAD solid**. Exact point-to-triangle proximity finds the following
positive distances to that solid's surface:

| Pose / pair | Convex penetration | Contact-point distance to original head/jaw surface |
|---|---:|---:|
| HOME: bearing / bottom shell | 4.455 mm | 4.276 mm |
| HOME: bearing / jaw | 4.285 mm | 21.524 mm |
| HOME: bracket / bottom shell | 2.340 mm | 6.090 mm |
| HOME: bracket / jaw | 2.117 mm | 24.100 mm |
| Worst: bearing / bottom shell | 5.621 mm | 13.211 mm |
| Worst: bearing / jaw | 5.273 mm | 25.363 mm |
| Worst: bracket / bottom shell | 3.244 mm | 13.431 mm |
| Worst: bracket / jaw | 2.834 mm | 27.570 mm |

These are **point-to-surface witness distances**, not minimum pair clearances.
The world-space point, nearest original triangle, nearest point, signed hull
halfspace value and all ray results are retained per case in `results.json`.
They establish that the contact representation fills space absent from the
original CAD solid at each inspected contact witness. They do not exclude an
unrelated real intersection elsewhere on the same pair.

## Crossing and containment checks

The crossing test visits every pair of original triangles whose expanded AABBs
overlap, and tests all six directed triangle edges against the opposite
triangle's interior. A proper-crossing witness requires opposite plane-side
distances above 1e-8 m and an interior barycentric margin of 1e-7. This avoids
claiming a crossing from a numerically ambiguous boundary hit.

- At HOME, **zero triangle-AABB pairs overlap** for any of the four mesh pairs.
  This is exhaustive surface-boundary separation under the floating-point
  AABB calculation; it is stronger than simply finding no vertex inside.
- At the worst pose, bearing/bottom-shell and bracket/bottom-shell require
  **472,732 and 54,631 triangle-pair tests**. No proper crossing or near-coplanar
  edge was found. The other two pairs have no overlapping triangle AABBs.
- Exact tangency, coplanar overlap and crossings arbitrarily close to triangle
  edges are outside the conservative proper-crossing certificate. No Boolean
  intersection or certified minimum triangle-pair distance was computed.

Exploratory largest-face-centroid containment checks were followed by a
**separately frozen canonical-vertex check** (`containment-protocol.json`). For
each one-component mesh, it chooses exact unique vertex 0 in local coordinate
order and queries the opposite solid in three declared directions. All **16
directional mesh queries** report outside in all three rays; the closest of
these representative points is 3.10 mm from the opposite surface. These checks
address complete nesting, rather than replacing the triangle-crossing audit.
They remain numerical ray tests; watertightness and winding consistency alone
are not a certified self-intersection-free CAD Boolean.

The combined evidence strongly supports a convex collision approximation
artifact at these poses. HOME has the stronger boundary-separation evidence.
Global pair clearance at the worst pose remains unproven; no physical clearance
claim follows from either result.

## Next model action

`coacd` **1.0.14** is already installed. A separately versioned convex
decomposition experiment is feasible without adding a compiled dependency.
It was **not started** in this audit.

Freeze a deterministic decomposition of the implicated concave CAD surfaces,
retaining the original triangles and body transforms as references. Validate
the resulting union using signed point/surface distances, cavity occupancy,
coverage and measured approximation errors in meters. Keep inertias explicit
and unchanged, retain uniquely named parts and the power-support mask fix, and
enable the jaw/neck pair. Re-run the two current witnesses and the complete
201-pose bank before choosing a dense pose bank or dynamic probe. Report any
lost contact coverage and new approximation separately; a lower penetration
score alone cannot select the geometry.

This is preferable to adding a blanket body exclusion: it targets the
demonstrated collision representation defect while preserving contact coverage.
Dynamic stability and 200 Hz internal-load validation remain subsequent gates.

## Reproduction and records

```sh
.venv-apple/bin/python experiments/walking/contact-reconciliation-v57/cavity-audit/inspect_surfaces.py
.venv-apple/bin/python experiments/walking/contact-reconciliation-v57/cavity-audit/containment_check.py
```

`protocol.json` binds the selected poses and original V57 manifest;
`results.json` contains topology, transform, crossing, contact-point and
exploratory containment evidence. `containment-results.json` contains the
separately frozen vertex checks. Their distinct manifests preserve source and
result hashes. Trimesh and Rtree were already installed; no new dependencies,
source mesh edits, hardware or paid resources were used.
