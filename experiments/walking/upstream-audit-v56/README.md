# V56 upstream physics compatibility audit

September 15, 2026. **Retain the local V11 model for the matched posture
experiment. Do not replace its physics with upstream VelStand in the same
experiment.** The newer model warrants a separate contact-model reconciliation
and recorded-state diagnostic before any training comparison.

This directory compiles the retained and upstream model and executes the
upstream collision editor in isolation. It does not step physics, run a policy,
start a GPU framework, change a frozen source, operate hardware or establish
physical calibration. Full mjlab/Warp runtime compatibility remains untested.

## Actual contact coverage

| Property | Retained `complete-contact-v11` | Upstream VelStand after pinned spec editor |
|---|---|---|
| Active robot collision geoms / mesh identities | 11 / 9 | 70 / 38 |
| Contact dimensions | all 11 are `condim=3` | 15 XL330 housing geoms are `condim=1`; remaining 55 are `condim=3` |
| Power-support masks | `1/1`; both support–leg pairs eligible | `2/2`; neither support–leg pair eligible |
| Static internal geom-pair eligibility | 49 | 1,837 |
| Explicit body excludes | none | `neck_pitch`–`jaw_soft` |
| Parent-body filtering | enabled | enabled |
| Sole friction and priority | friction `[1,.005,.0001]`, priority 0 | same friction, priority 1 |

The local name **does not mean every CAD part collides**. Its active bodies are
battery, power support, two hips, two legs, two soles and three head/jaw meshes.
Servo housings, trunk shells, upper-leg structure and numerous other visible
parts do not have active collision counterparts in this retained version. The
existing penetration/load results cover those 11 active colliders. They cannot
reject interference involving a disabled part. Preserve those historical
results and state their scope; do not silently broaden their safety meaning.

The upstream model is substantially broader, but still not a safe drop-in:

- Its power support remains isolated from ordinary bit-1 robot and floor
  colliders. V11 deliberately repaired exactly that gap.
- The `neck_pitch`–`jaw_soft` exclusion suppresses all contacts between those
  two bodies. Upstream comments attribute this to an export/linkage overlap;
  that diagnosis is an author claim, not measurement-based clearance evidence.
- Only 17 upstream geoms are named after servo naming: 15 housings and two
  soles. There are 123 unnamed geoms. mjlab 1.3.0's `CollisionCfg` deduplicates
  nonmatching **names**, then resolves each with `spec.geom(name)`. Consequently
  its `disable_other_geoms=True` does not visit every unnamed geom. In this
  model it changes no masks. The generic `_collision` rule does not make the
  53 unnamed non-sole/non-servo colliders frictionless. This was reproduced with
  both MuJoCo 3.10.0 (upstream lock) and 3.12.0 (local interpreter).

Pair counts apply masks, same-weld filtering, parent-weld filtering and explicit
body excludes. They describe **potential** pairs, not observed contact, loaded
contact, penetration or force. Spatial overlap is not tested here. No explicit
geom-pair override exists in either model; the audit fails if one is added.

## Sensor and actuator boundaries

| Property | Local native V54/V55/V11 lane | Pinned upstream VelStand |
|---|---|---|
| Motor/control timing | 200 Hz physics / 50 Hz control; unfiltered position targets | same nominal rates (`.005` timestep, decimation 4) |
| Integrator / solver settings | XML-default Euler / Newton, 100 iterations, 50 line-search iterations; core sets timestep | mjlab implicitfast / Newton, 10 iterations, 20 line-search iterations |
| BAM authority | `62bd8ce12154340be97e06f7f41a0ca8f116d967`, native NumPy/C MuJoCo controller | same locked commit, Torch/Warp BAM implementation plus friction-DR subclass |
| XL330 M6 parameters / firmware gain | bundled JSON / `kp=200` | same parameter bytes / `kp_fw=200` |
| Voltage domain | native evaluator nominal 7.35 V, sag gain 0, floor 6 V | per-environment 6.5–8.2 V, sag gain 0–.2, floor 6 V |
| Motor lag | explicit tested FIFO conditions, 3–6 physics ticks (15–30 ms) | randomized 3–6 physics ticks |
| Observation delay | one shared fixed case lag of 0 or 1 control tick for IMU and joint velocity | IMU 0–1 tick, updated every 64 controls; joint velocity always 1 tick |
| Noise/domain changes | versioned native curricula retain their explicitly materialized conditions | noise, encoder bias, IMU misalignment, gains, armature and friction curricula in upstream task |
| Internal-body force evidence | actual applied normal loads sampled after every 200 Hz physics step; missing evidence fails | self-contact sensor has `found` only; no corresponding internal force-duration acceptance gate identified |
| New impact sensors | not substituted for internal-load evidence | servo/head/trunk **to terrain**, force vector reduced by `netforce`, one slot |

The three new impact sensors cannot observe robot–robot bracing. Their net
force reduction also differs from our sum of positive per-contact normal loads.
Do not compare those scalar magnitudes across sensors or engines as equivalent
measurements. Reward terms are not independent acceptance tests.

The native timing case couples IMU and joint-velocity lag; upstream fixes
joint-velocity lag independently. A future compatibility experiment should
separate those factors rather than relabel an existing native case as the
upstream distribution. The current audit leaves both implementations intact.

## CAD and mechanical identity

Both models compile to `nq=21`, `nv=20`, 14 actuators in the same order, and total
body mass 0.73724318 kg. Body positions, joint axes and positions, and raw XML
damping/armature/friction arrays match exactly. Body orientation quaternions
match after resolving the equivalent `q`/`-q` signs. The largest joint-range
difference is only 1.14e-13 rad; inertial-position differences are at most
1e-7 m and principal-inertia differences at most 1.24e-11 kg m². These are
export-level differences, not evidence of a materially different robot size.

All 38 STL byte hashes differ, while all axis-aligned bounds match exactly.
31 meshes have identical unique vertex sets despite reordered triangles.
Seven have different vertex sets; `foot_right` changes from 19,914 to 19,952
triangles, and `sole_right` from 15,888 to 15,902. Byte differences alone do not
prove different collision hulls. The changed meshes need a geometric hull and
pose reconciliation before asserting identical contact surfaces.

The BAM JSON bytes equal the authoritative pinned package's XL330 M6 file:
`61c699362fb3fabdde93eeba5e1ad3bf4ef9ca2f71d03e316b1924ff005b20d3`.
Shared parameters and interface dimensions do not prove controller, observation
semantics or dynamic trajectory equivalence.

## Follow-through decision

1. Keep the matched standing-posture ablation's V11 physics frozen so its result
   can answer the intended objective question. Label its contact scope precisely.
2. Before broad skill admission, construct a separately versioned model with
   explicit unique collider names and a declared pair matrix. Reconcile the
   38 mesh identities, the support fix and jaw/neck geometry. Do not blanket
   disable a pair merely to remove a bad score.
3. Replay retained observed poses as a geometric rejection diagnostic against
   the reconciled model, then conduct passive and action-frozen dynamic probes.
   Changed-model findings get new receipts; original scores remain untouched.
4. Only after the geometry question is resolved, compare solver/integrator,
   BAM implementations and independent delay channels using byte-identical
   actions and a frozen state/timing bank. Keep one physical change per test.
5. Carry the internal-load gate into later recovery with task-specific allowed
   support contacts. Floor-impact penalties alone do not close this gate.

The broader current model is a high-leverage reference for contact auditing;
the present evidence does not justify replacing the retained training physics
mid-ablation or claiming real carpet transfer.

## Reproduce and inspect

```sh
.venv-apple/bin/python experiments/walking/upstream-audit-v56/fetch_assets.py
.venv-apple/bin/python experiments/walking/upstream-audit-v56/audit.py
```

`fetch_assets.py` restores only the 38 pinned upstream CAD files (21.6 MB) under
this directory, with SHA-256 verification and no dependency installation. Those
bulk files are ignored; their immutable URLs and hashes are in `sources.lock.json`.
All 108 source inputs, including 51 local model/evaluator inputs, are hash-checked
before the audit compiles anything. `audit.json` contains every geom and eligible
pair, physical-array differences, mesh hashes and vertex/bounds comparisons.

`audit-mujoco-3.10.json` repeats the same static audit using the upstream-locked
MuJoCo version. Its wheel provenance is in `runtime-mujoco-3.10.source.json`;
the wheel was extracted under this directory and used via `PYTHONPATH`, without
modifying the active environment. No physics or policy was executed in either
run. Source-editor execution is narrower than a complete GPU scene build.
`verification.json` records 11 successful consistency and evidence-boundary
checks, including the same effective contact inventory in both MuJoCo versions.

Upstream revision:
[`cb70b792312d559a4da09064d92009079671815f`](https://github.com/pollen-robotics/microduck_rl/tree/cb70b792312d559a4da09064d92009079671815f).
Framework source is extracted from the hash-verified mjlab 1.3.0 wheel in the
upstream lock (`e3b544bf3e7b69d6de0641c0f98fa3c9bb9d8ff662951ad83dcaba4db4fe47cf`).
No upstream training claim is adopted as local evidence.
