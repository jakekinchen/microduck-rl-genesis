# V61 remaining head proxies: improved, still rejected

One fixed 256-part recipe improves all three remaining approximations, but
none meets the unchanged 0.25 mm sampled excess-material limit. The passing
V60 bearing is retained separately. No complete replacement model, dynamics,
policy or training result is admitted by this comparison.

The source meshes, CoACD library and worker bytes match V58. Only the hull-cap
generation parameter changes from 64 to 256. There is one attempt per shape,
with a 120-second limit each, followed by one 360-second material evaluation.
No retry or timeout occurred. Wall times are receipts, not a controlled
performance benchmark.

| Shape | V58 excess material | V61 excess material | V61 missing material | Result |
|---|---:|---:|---:|---|
| Neck bracket | 1.150462 mm | 0.286053 mm | 0.185453 mm | Fail excess |
| Bottom head shell | 2.468068 mm | 0.939718 mm | 0.144674 mm | Fail excess |
| Jaw | 1.065621 mm | 0.663937 mm | 0.225550 mm | Fail excess |
| Retained V60 bearing | — | 0.217129 mm | 0.162090 mm | Component pass |

Each set has 256 watertight, convex parts. Missing-material checks pass for
all four, and all eight original cavity-point checks pass. That pointwise
cavity result does not establish complete pair clearance or override material
outside the source CAD elsewhere. The retained bearing's complete per-mesh
record repeats exactly in this combined bank.

Generation took 8.131 seconds for the bracket, 100.393 seconds for the shell,
and 21.597 seconds for the jaw. Independent material verification took 64.775
seconds. All subprocesses were reaped. The frozen rule stops this comparison
at failed material gates: no further decomposition, complete-model assembly
or dynamic probes were launched under this protocol.

## Next diagnostic and model gate

The separate posthoc localization is complete in 18.173 seconds, with all three
maxima reproduced exactly. The bracket has three over-limit face centroids in
parts 152 and 192. The shell has 192 violating samples across 101 parts; the jaw
has 49 across 25 parts. In total, 243 of 244 violations are face centroids and
one is a shell vertex. This supports investigating convex faces spanning source
recesses, without claiming semantic CAD identification or global error coverage.

`excess-witnesses.json` retains the top 20 positive-excess points per mesh,
originating part/face indices, nearest original triangles, and local coordinates,
volumes and bounds. `excess-witnesses.png` shows source-local projections; only
three of its 20 bracket markers exceed the threshold. The 15-input frozen
localization plan and original source/archive hashes verify. No geometry changed.

Next test one source-aware partition/refinement in the two implicated bracket
regions before convexification. Preserve other source material and the passing
bearing, and freeze the candidate/budget before generation. Do not respond with
an unrestricted hull-count or parameter sweep.

Before a complete replacement can progress, require all four material sets,
fixed cavity witnesses, full compiled physical/actuator arrays, named contact
coverage and the 201-pose bank. Then freeze distinct controlled-HOME-hold and
exact-action BAM/load probes. A HOME-holding motor policy is not passive, and
unchanged actions on a changed collision model need not reproduce old states.

Records: `protocol.json`, `plan.json`, `processes.json`, the three raw part
archives and native logs, `material-bank.json`, and `material-result.json`.
The older V58/V59/V60 receipts remain immutable. This is CAD-based simulation
diagnosis; physical calibration and carpet transfer remain separate gates.
