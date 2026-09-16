# V57 full-CAD copied-pose reconciliation

**Diagnostic complete; no model admitted.** The full-CAD model exposes a
persistent jaw/neck interference hidden by V11's smaller collider set. This is
a geometric rejection result. It does not change any original behavior score,
demonstrate loaded contact or justify disabling a pair to obtain a pass.

## Frozen selection and model variants

`protocol.json` was written before reading pose outcomes. Its selection is the
first row, every 50th control row, and the last row of each source recording:

- Nominal retained obstacle course: **67 of 3,300 controls**, spanning 66 seconds.
- All twelve V56 standing feasibility recordings: **11 of 500 controls each**,
  covering both original/shared actors, motor lags 0/4/6, and initial yaws 0/.12.
- Two explicit contract-HOME poses at z=.125 m, yaws 0/.12.

Total: **201 poses**, including 199 selected from 9,300 stored control rows.
The course's other five domain cases are outside this diagnostic. Sampling about
once a second does not cover every gait phase, transient contact or continuous
interval. V56 standing recordings are development data, not protected tests.

The two new XML files copy pinned upstream revision
`cb70b792312d559a4da09064d92009079671815f`, assign unique names to **every** geom,
and enable bit-1 masks on all 70 intended colliders, including power support.
All colliders use `condim=3` for a declared future diagnostic convention; contact
dimensions have no force interpretation in this kinematic-only run.

- `original-jaw-exclusion/robot.xml` retains upstream's explicit
  `neck_pitch`–`jaw_soft` exclusion.
- `jaw-contact-enabled/robot.xml` removes that one exclusion.
- Retained V11 is loaded directly and unchanged as the original comparison.

`pair-matrices.json` lists every active geom and every internal candidate pair,
including disabled pairs: **2,415 pairs for each 70-collider variant**, and
55 for V11. Eligibility applies bitmasks, same-weld and parent-weld filtering,
and the explicit exclusion. It is not a list of observed contacts.

## Copied-pose result

| Model | Poses above frozen 1 mm internal penetration threshold | Maximum penetration |
|---|---:|---:|
| Retained V11, 11 active colliders | 0/201 | 0 mm |
| Full CAD, original jaw/neck exclusion | 0/201 | 0 mm |
| Full CAD, jaw/neck contact enabled | **201/201** | **5.621 mm** |

The four observed interfering geom pairs are:

| Pair | Maximum overlap |
|---|---:|
| neck bearing → bottom head shell | 5.621 mm |
| neck bearing → jaw | 5.273 mm |
| neck bracket → bottom head shell | 3.244 mm |
| neck bracket → jaw | 2.834 mm |

Both explicit HOME poses overlap by 4.455 mm. Every sampled pose has at least
one over-threshold pair involving a part absent from V11's active collider set.
Upstream's original body exclusion hides all these pairs. The diagnostic
therefore reproduces the general reason upstream gave for its exclusion, but
does **not** establish that the physical assembly has those penetrations.
Convex collision hulls can fill concave cavities; a CAD export or linkage frame
can also be wrong. Those explanations require a separate check.

No other internal contact was observed in this sparse bank. The original
exclusion variant's zero is a useful scoped observation, not permission to
adopt the model. Floor/obstacle contacts and internal contact loads were not
evaluated. Only copied `qpos`, `mj_kinematics` and `mj_collision` were used:
**zero dynamics steps, zero BAM calls, zero policy calls**.

## Seven changed mesh sets

SciPy 1.18.1 is already installed; no dependency was added. All mesh bounds
match exactly. For the seven meshes with changed canonical vertex sets, we
computed convex hulls, symmetric nearest-vertex Hausdorff distances, and support
differences along 256 fixed Fibonacci directions plus the six Cartesian axes.

| Mesh | Vertex-set Hausdorff | Hull-vertex Hausdorff | Maximum sampled hull support change |
|---|---:|---:|---:|
| bottom head shell | .182001 mm | .034685 mm | .000856 mm |
| right foot | .584247 mm | .607639 mm | .001549 mm |
| jaw | below 1e-12 mm | 0 | 0 |
| Raspberry Pi PCB | .060638 mm | 0 | 0 |
| right shell | .000068 mm | 0 | 0 |
| right sole | .695539 mm | .000009 mm | .000000530 mm |
| top head shell | below 1e-12 mm | below 1e-12 mm | below 1e-12 mm |

These figures separate changed tessellation from changed supporting geometry.
For example, the sole's vertex sampling differs by nearly .7 mm while the
sampled convex support differs by less than a nanometer. Nearest-vertex
Hausdorff is **not** triangle-surface Hausdorff. Finite-direction support
differences are **not** a global geometric bound. The largest sampled support
change here is about 1.55 micrometers, much smaller than the millimeter-scale
jaw/neck overlap; this does not prove exact collision-hull equivalence.

## Next model decision

Keep V11 as the declared reference for the already matched posture experiment.
Retain both new models as diagnostics only. Before full-contact admission:

1. Inspect the four implicated pairs using actual triangulated surfaces and
   CAD/linkage frames, separating convex-hull cavity filling from surface
   interference. Do not apply a blanket body exclusion solely to clear a score.
2. If collision hull construction is the cause, derive and separately version
   physically justified collision proxies or convex decompositions. Preserve
   every mesh transform and the power-support fix, with an explicit pair matrix.
3. Freeze a denser copied-pose bank spanning full controls and additional course
   cases, then run separately authorized passive and action-frozen dynamics with
   200 Hz internal-load telemetry. No force or stability inference is available
   from the current pose-only run.

The widened collision audit is a higher-priority model prerequisite for broad
skill admission than assuming the name `complete-contact-v11` covered every
visible component. It need not invalidate a narrowly labeled objective ablation.

## Reproduce and evidence

```sh
.venv-apple/bin/python experiments/walking/upstream-audit-v56/fetch_assets.py
.venv-apple/bin/python experiments/walking/contact-reconciliation-v57/diagnose.py
```

The script verifies all 108 upstream-audit source inputs and all 13 compressed
recording hashes before reading selected poses. It rejects model regeneration
after source drift. `summary.json` records outcomes and mesh diagnostics;
`pose-results.json` preserves every sampled source index, timestamp, pose digest
and geom pair; `manifest.json` binds inputs and generated artifacts.
No shared model, evaluator, policy, queue or original result was edited.
