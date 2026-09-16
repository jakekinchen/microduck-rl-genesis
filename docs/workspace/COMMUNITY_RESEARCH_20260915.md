# MicroDuck community research and next priorities

September 15, 2026. Research and proposed work, not a new training result or
permission to deploy. X was searched directly in Safari; technical claims were
checked against the authors' current public repositories. This is a targeted
sample, not an exhaustive survey of X. No external policy was executed.

**September 16 execution update:** the subsequent
[runtime rehearsal](../../experiments/runtime-rehearsal-v1/RESULTS.md) found
that the documented BAM body actually uses static XML position actuators in
the pinned executable. The default scene is ground-contact, and startup enters
a HOME ramp. The [contact audit](../../experiments/walking/upstream-audit-v56/README.md)
also resolves the effective upstream collision settings. Read those executable
findings before treating the documentation summaries below as runtime behavior.
The [standing feasibility result](../../experiments/walking/POSTURE-FEASIBILITY-RESULTS-v56.md)
leaves the proposed posture training prerequisite unmet.

## Decision

Keep the Genesis development lane and the native MuJoCo/BAM evaluator. Refresh
the upstream comparison before the next learning experiment, finish the bounded
walk/stop refinement, and then build sensor-driven tasks around the retained
locomotion controller. Buy capability through reusable commands, perception and
tested handoffs. A new motor policy is warranted when the task changes the
required contact dynamics, not just the destination.

There is credible evidence that this platform can support a much richer skill
set. The community results reviewed here do not supply calibrated carpet physics
or a hardware-tested replacement for our walking controller.

## Our actual starting point

- [The September 13 course](../../experiments/laser/COURSE-RESULTS-v2.md) passes
  six exposed 66-second flat-floor cases using V21 walking, V15 standing and V30
  heading. It uses simulated target coordinates and a prescribed route. It does
  not establish visual following, obstacle perception or unseen-layout success.
- [V55](../../experiments/walking/YAW-RESULTS-v55.md) remains rejected. Both finals
  retain 63/63 flat cases and the original 5/14 surface passes. The yaw6 final
  survives four downhill sessions, but all eight walking/stop windows fail yaw
  and final face pitch; one of two full compositions also fails heading. Both
  training arms reach complete long episodes in only 22/24 conditions.
- Existing public carpet sources and the 30,709-row ISRD inspection remain
  [scoped priors](../../experiments/walking/public-surfaces-v1/RESEARCH-NOTES.md),
  not Ducky-foot material measurements. No new matching physical dataset was
  identified in this review.

## What X led to

| Directly inspected post | What the linked primary source establishes | Useful implication |
|---|---|---|
| Hannes von Essen: [climbing, September 13](https://x.com/HannesVonEssen/status/2099195903672488291), [basketball, September 7](https://x.com/HannesVonEssen/status/2096916066601439474), [swing, September 2](https://x.com/HannesVonEssen/status/2095193921060049010), and [training repository](https://x.com/HannesVonEssen/status/2099258223333171542) | [MicroDuck Playground](https://github.com/Vottivott/microduck-playground/tree/e7c82578852683978783e751ecf1e8e909d32a5b) publishes experiments, checkpoints, hardware geometry and evaluation records. The author [explicitly says the climbing trial on a robot is still ahead](https://x.com/HannesVonEssen/status/2099238970077171863). | Reuse experiment designs and inspect complete evaluations. A video or an accessory model is not physical validation. |
| witcheer: [real daemons driving a simulated body, September 14](https://x.com/witcheer/status/2099410056353550787) | The post labels its results as simulation. Pollen's [current runtime documentation](https://github.com/pollen-robotics/microduck/blob/fead66bb21195971fcbb2858a19b1e290a9f2031/docs/robot/simulation.md) describes `robotd`, `tofd`, camera streaming and the ordinary command interface against a MuJoCo/BAM body. Device drivers remain absent. | Rehearse the software that will actually issue commands and switch policies. Verify local host support and timing before relying on this path. |
| kabilan KB: [Isaac Lab/Newton training, September 13](https://x.com/kabilankb2003/status/2099204430772203788) | The associated [public port](https://github.com/kabilankb/isaaclab-microduck/blob/4310fe050b7a1b01e7b2f4bada103dea81d71fb2/README.md) reports nonworking locomotion and missing BAM, observation delays and encoder bias. The post may involve unpublished changes; those were not available for review. | A new simulator name is not evidence of better physics or transfer. Do not migrate on the strength of this post. |
| Antoine Pirrone: [question about relaxed sim-to-real constraints, August 30](https://x.com/antoinepirrone/status/2094126917641245038) | The developer asks for the ONNX and whether constraints were relaxed before a proposed physical trial. It is a proposed trial, not a reported successful deployment. | Compare the actual artifact, model and constraints before importing a community skill. |

The closest Genesis source remains [Macmachi's port](https://github.com/Macmachi/microduck-rl-genesis/blob/9d1f213879650f2623e3bbd7bf06fe63dbf71a10/README.md).
It preserves the deployment interface and reports actuator conformance, while
explicitly stating that no exported policy has been validated on a real
MicroDuck. Its course reuses training terrain; waypoint commands guide the
blind policy. This supports using it as a technical reference, not as proof of
unseen terrain, navigation or calibrated physical accuracy. The targeted X
Genesis search did not uncover a stronger independently verifiable transfer result.

## New information since our September 8 audit

Pollen's current [VelStand factory](https://github.com/pollen-robotics/microduck_rl/blob/cb70b792312d559a4da09064d92009079671815f/src/mjlab_microduck/tasks/microduck_velstand_env_cfg.py#L390)
now selects `MICRODUCK_ALLCOLLISIONS_ROBOT_CFG`, expands the contact budget and
adds separate servo/head/trunk-to-terrain force sensors and impact costs.
The [robot configuration](https://github.com/pollen-robotics/microduck_rl/blob/cb70b792312d559a4da09064d92009079671815f/src/mjlab_microduck/robot/microduck_constants.py#L142)
uses three-dimensional foot contacts and one-dimensional contacts for other
matching collision geoms. A nearby comment saying no task uses the full model
is stale: the factory assignment is concrete source evidence.

This corrects the applicability of our older audit; it does not invalidate its
pinned September 8 findings. It also does not establish equivalence with our
complete-contact-v11 model. In particular, these new force sensors match the
terrain, so they do not replace our internal body-loading gate. The default
walking task still uses a different collision configuration from VelStand.

The [upstream training lessons](https://github.com/pollen-robotics/microduck_rl/blob/cb70b792312d559a4da09064d92009079671815f/AGENTS.md)
also support checking static target feasibility, explicit zero-command and
turning exposure, reward contributions and actual episode progress. They warn
that penalizing instantaneous head motion can suppress walking. For us, that
supports a standing-only posture experiment; it does not justify relaxing the
frozen yaw or face-pitch thresholds or adding an output filter.

Two concrete community results illustrate why architecture should follow a
diagnosis:

- [Basketball](https://github.com/Vottivott/microduck-playground/blob/e7c82578852683978783e751ecf1e8e909d32a5b/experiments/basketball/README.md)
  reports 2,980/3,072 simulated 60-second survivals with a blind LSTM, but yaw
  tracking MAE is 1.2618 rad/s and is conditioned on survival. It requires
  recurrent ONNX state and starts already supported on the ball. It neither
  climbs onto the ball nor recovers from the floor. This is evidence for a
  scoped memory experiment, not proof that our walking needs recurrence.
- [Running](https://github.com/Vottivott/microduck-playground/blob/e7c82578852683978783e751ecf1e8e909d32a5b/experiments/running/README.md)
  reports 1.651 m/s nominal and 1.612 m/s under backlash/disturbance stress in
  short simulation batteries, with substantial heading/lateral drift remaining.
  Its gradual robustness curriculum and complete checkpoints are useful; its
  speed/survival scores are not interchangeable with our composite acceptance.

## Ordered recommendation

1. **Refresh the reference and check the runtime boundary before training.**
   Compare the newly pinned VelStand model, active contact pairs, actuator and
   delay behavior against our preserved model. Inspect the real-daemon simulator
   for local compatibility without launching it by default. Specify a later
   rehearsal using our exact retained actors, command writes and continuous
   walk–turn–stop sequence. Success means an explicit difference table and
   reproducible tests, not a blanket claim that the two stacks are equivalent.
   Preserve all source freezes and avoid wholesale upstream replacement.

2. **Complete one bounded posture comparison, then diagnose the remaining gap.**
   First check that the intended standing face pose can physically settle under
   the active downhill conditions. Freeze the planned matched standing-only
   objective ablation from V54 shared. Require all four downhill sessions,
   retained flat/composition/surface gates and actual long-episode coverage in
   all 24 training conditions before advancing. No threshold relaxation or
   checkpoint cherry-picking. If it fails, use per-mode advantage, contact,
   action and experience diagnostics to select one next change. A privileged
   critic is a lower-interface-cost comparison than adding actor memory. Do not
   precommit to an endless sequence of penalty increases. Replicate an accepted
   recipe with two further training seeds before broader claims.

3. **Turn the flat course into a sensor-driven task.**
   Reuse V21/V15/V30 within its demonstrated flat operating envelope. Replace
   privileged target coordinates with a rendered-camera bearing estimate, and
   use the supported depth stream for nearby obstacles. Start with a visible
   target and simple obstacle layout, then freeze unfamiliar layouts, lighting,
   target occlusion, delayed/dropped observations and target-loss stopping tests.
   Verify camera geometry rather than assuming the named optical axis is the
   physical forward direction. Compare perception outputs against hidden ground
   truth only in evaluation. This is the highest-leverage next *capability*
   addition: following, approaching and navigating can share one motor skill.

4. **Add recovery and intentional skill handoffs.**
   Study the new upstream recovery recipe, then develop or admit each artifact
   through our gates. Test walking → stop → sit/recover → stand → walking from
   continuous physical states. Each skill needs entry conditions, allowed
   contacts, impact/load limits, completion/failure signals and a defined exit.
   Recovery legitimately allows some non-foot support, so it needs its own
   preregistered contact rules; walking's rejection rules remain unchanged.
   Kicking and object interaction follow reliable recovery and target sensing.

5. **Expand one walking capability across terrain families.**
   Start with bounded slopes and secured low-pile-like numerical conditions;
   progressively add friction, cushioning, surface transitions and edges. Keep
   surface families and combinations held out, measure parameter application,
   and retain flat/endurance performance. Add history/adaptation only after a
   controlled test shows hidden dynamics are limiting a competent baseline;
   add predictive terrain sensing when geometry requires action before contact.
   Do not require the user to select a separate carpet policy for each room.

Steps 3–4 can be scoped to flat-floor development while broader terrain admission
is still open. They do not promote V55 or turn the existing course into an
accepted general capability. `TRAINING_ACTUALIZATION.md` remains the single
execution queue; this note does not authorize paid compute or hardware.

## What accurate physics can mean without owner measurements

Use public CAD, actuator identification and available raw measurements as
bounded priors, with source identities and uncertainty. The
[BAM paper](https://arxiv.org/abs/2410.08650v4) identifies and validates friction
models using physical test benches; it does not identify our assembled robot
or foot–carpet contact. Cross-engine replay, passive tests and timestep/solver
checks can expose numerical errors but cannot supply those missing measurements.

Continue simulation development without asking the owner for data. If a public
dataset matches a calibration question, admit only that scope with separate
fit and validation trials. Physical carpet readiness still requires applicable
physical evidence; a synthetic locomotion dataset or a successful video cannot
close it. The newly found [locomotion dataset](https://huggingface.co/datasets/devorah-ai-2016/microduck-locomotion-dataset-v1)
describes itself as synthetic, so it is not a physical calibration source.

## Source revisions and verification scope

Retrieved September 15 via public GitHub API and immutable raw-file URLs:

| Repository | Revision | Commit date (UTC) |
|---|---|---|
| `pollen-robotics/microduck_rl` | `cb70b792312d559a4da09064d92009079671815f` | September 14 |
| `pollen-robotics/microduck` | `fead66bb21195971fcbb2858a19b1e290a9f2031` | September 15 |
| `Macmachi/microduck-rl-genesis` | `9d1f213879650f2623e3bbd7bf06fe63dbf71a10` | September 3 |
| `Vottivott/microduck-playground` | `e7c82578852683978783e751ecf1e8e909d32a5b` | September 14 |
| `kabilankb/isaaclab-microduck` | `4310fe050b7a1b01e7b2f4bada103dea81d71fb2` | August 30 |

Local source copies and SHA-256 records are in ignored
`.workspace/community-research-20260915/`; the immutable links above preserve
retrieval independently of that cache. Source inspection was not execution or
reproduction of the authors' benchmarks. No training, paid compute, policy
activation, hardware operation or external posting was performed for this review.
