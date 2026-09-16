# V48 completed and rejected: flat retention does not preserve full compositions

The V47 handoff diagnosis and one bounded V48 standing correction are complete.
**Keep V30 with the original V21 walker and V15 stander.** V48 retains all 63
flat windows but does not solve downhill stopping, loses one long composition,
and loses one previously passing surface session. Fresh sequence and protected
terrain banks remain unrun. No policy was activated.

## Independent acceptance

| Exposed bank | Retained V30 | V48 FINAL499 |
|---|---:|---:|
| Original flat windows | 21/21 | 21/21 |
| Repeated flat windows | 42/42 | 42/42 |
| Complete 180-second compositions | 2/2 | 1/2 |
| Original downhill sessions | 0/2 | 0/2 |
| Public-prior surface sessions | 5/14 | 4/14 |

All four evaluations completed and all required case and session outcomes were
read. The combined endurance/downhill bank passes 14/24 windows and 1/4 sessions.
Seven windows remain unrun after terminal falls. Surface windows increase from
12/28 to 13/28, but whole-session passes decrease: window totals cannot replace
continuous-state acceptance. Four surface windows remain unrun after falls.
Historic `unseen-*` names belong to exposed development, not a newly held-out bank.

Both downhill sessions switch to standing at 13.16 s and fall at **13.86/13.78 s**.
Applied internal loading exceeds 1 N continuously for .165/.130 s, against the
unchanged .05-s limit; load occupancy also exceeds its 1% limit. The first
downhill case additionally fails geometric self-penetration. Missing duration,
non-foot support and missing stop/endurance evidence remain failures. These
loads are the native engine's applied contact loads, not calibrated hardware
forces. Their timing does not establish whether contact initiated the fall.

`continuous-composition-start-1` passes four windows, then switches to standing
at 85.14 s and falls at **86.28 s** in window five. That window also fails the
actual joint-margin gate. Its incoming speed at the standing switch is .0182 m/s
and tilt 2.96 degrees, so the regression cannot be explained simply by the
higher downhill incoming speed. The second composition completes 180 s and
passes; heading endpoint/maximum errors are 8.55/15.53 degrees.

The lost surface pass is `soft-low-traction-start-1`. Both its windows pass,
but its final heading error is **17.03 degrees**, above the 15-degree session
limit. The remaining four passes are both rigid controls,
`soft-low-traction-start-2`, and `unseen-low-medium-start-1`; there are no newly
passing complete sessions. Other surfaces still exhibit early falls, loaded
slip, yaw error and missing evidence. The first nominal flat case retains zero
right-knee samples inside the 5% near-limit band for both actor phases.

## Diagnosis, learning and integrity

[V47](HANDOFF-RESULTS-v47.md) reproduces 2,763 original/V46 downhill action rows
and exact poses. Sixteen complete saved states reproduce 400 further controls
after restoration. Both actor pairs pass matched-flat controls and fail
downhill; downhill arrives faster at the standing handoff. Large first-standing
action jumps also occur in passing flat cases, so action jump alone does not
identify the cause.

V48 trains standing from V15 while freezing V21 walking, both normalizers and
the V15 teacher. It uses 24 terrain/timing/yaw cells, each with HOME and complete
13.00-second pre-brake reset origins, and continuous sequences through 54 s.
Flat online imitation and 24,105 original standing replay rows from all 63 flat
windows and both passing long compositions constrain the update. Replay uses
real retained observations/actions; its maximum teacher difference is
8.345e-7 rad. The flat-domain label is optimizer metadata and is absent from
the 61D deployed actor and critic inputs.

One 2,880-transition smoke precedes the single **576,000-transition** full run,
which completes in **684.387 s** including setup. Only preregistered FINAL499
is evaluated. Each setup separately executes 15,600 original prefix controls;
these are not included in the learning-transition count. Native MuJoCo 3.12,
pinned BAM, contact-v11, 14D raw actions, 50-Hz control, 200-Hz physics, the V16
command ramp and V30 heading control remain fixed. Physical execution and
scoring blocks match the preceding frozen evaluators apart from display labels.

Verification passes for 79,984 paired conformance controls across all 24 cells
and both reset origins; all 576,000 recorded action/observation rows; 1,447
actual switch histories; exact component splits; byte-identical walking and
teacher tensors; 6,496 finite learning scalars; and five source freezes. The
main freeze binds 213 files. The largest measured flat/repeated export error
is 1.669e-6 rad. Switch histories contain actuator and sensor arrays but are
not themselves complete MjData restart snapshots. **139 workspace tests and
two focused actor/environment tests pass.**

Stochastic learning reaches the sequence endpoint 182 times: 87 from HOME
(54-second cycles) and 95 from pre-brake (41-second continuations). These are
curriculum observations, not acceptance rates. The two longest-delay downhill
yaw cells have zero completions from either origin and 114 falls combined.
The maximum learning horizon remains 54 s despite replay from longer reference
runs; replay retention did not preserve the candidate's 180-second closed-loop
behavior. This combined intervention does not isolate each loss or reset choice.

## Next step

Run a bounded **recovery-feasibility diagnostic before another PPO correction**.
Freeze the original downhill pre-brake/handoff states and reproduce/capture the
new late-composition failure with full body, actuator, sensor and controller
history. Search for a safe short action sequence under the same joint, torque,
delay, body-contact and stopping gates, then test continuation and restart.
Compare original and V48 standing from identical incoming states, preserving
the original action stream in the reproduction arm. Label any optimized action
sequence as a separate privileged diagnostic, not a deployed 61D policy.

Predictive sampling is a documented trajectory-search approach in
[Google DeepMind's MuJoCo MPC](https://github.com/google-deepmind/mujoco_mpc).
Using a bounded search in this repository's existing native world is a proposed
diagnostic, not evidence that recovery will succeed or a requirement to install
another simulator. A successful search would supply a concrete recovery target;
an unsuccessful finite search means unresolved within its budget, not proof of
physical impossibility. Future learning must include candidate-state retention
through full 180-second compositions as well as the five original surface
passes. Keep broader terrain expansion behind the original downhill gates.

## Storage and evidence

[Storage recovery](../../docs/workspace/STORAGE-RECOVERY-20260908.md) removed nine
external Time Machine snapshots, recovering 790.08 GiB before offload. A verified
seven-file, 9,464,940,983-byte inactive checkpoint archive restored internal
headroom from .23 to 8.97 GiB at the maintenance audit. Its original path is a
compatibility symlink. The newer checkpoint, separate offloads and latest raw
backup directory remain. Time Machine has no configured destination; neither
external volume was erased. Free space changes as new receipts are written.

- Run: `logs/standing-retention-native-20260908-v48/run.json`.
- Joint FINAL SHA-256: `6c3cc47ecd033e73715b2dd546fdceb8efb859d35ef5093c4ca96722f52e10b1`.
- Evaluated original walker checkpoint: `7b5e166c13a8086fdd21b5ad237a0e69aa75828ad6f8fb5536f3ea057535a322`.
- Evaluated standing checkpoint: `eb56e2b8d2572a532f71af0abea8cac5c9e134c9ec5e3bbb716c29d0c3185ff6`.
- Evaluations: `receipts/walking/20260908-v48-standing-retention-{flat,repeated,endurance,surfaces}`.
- Integrity and retained training: `receipts/walking/20260908-v48-standing-retention-verification`.
- Comparison: `outputs/walking-standing-retention-v48`.
- Downhill trace plot: `outputs/walking-downhill-v48`.
- Closing review/status/test receipts: `receipts/walking/20260908-v48-activity-closure`.

All activity compute is finished. The bounded activity is complete with a
negative candidate result. Calibrated Ducky physics, carpet generalization,
physical transfer, library admission and hardware operation remain unmet.
