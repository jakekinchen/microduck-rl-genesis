# Can we expand Ducky's capabilities credibly?

Research and repository comparison, September 8, 2026. This is a decision note,
not an experiment preregistration or a new behavior acceptance result.

**September 15 reassessment:** [Direct X and current-source review](COMMUNITY_RESEARCH_20260915.md)
finds new upstream full-collision walking/recovery configuration and a documented
real-daemon simulation path. Refresh those comparisons before the planned
standing-posture experiment. The highest-leverage capability extension is
sensor-driven tasks around retained locomotion, followed by recovery/handoffs
and staged terrain expansion. The September 8 source findings below remain
historical; current VelStand now selects the full-collision model. Neither new
source code nor community demonstrations change our acceptance results.

**September 12 follow-through:** V55's matched yaw comparison is complete.
The yaw6 arm broadens stopping survival to four downhill headings, but yaw,
final face posture, one whole-composition heading gate and two long-training
conditions still fail. No accepted improvement or terrain advancement.
The next proposed experiment isolates standing face-posture objective alignment;
see [V55 results/reassessment](../../experiments/walking/YAW-RESULTS-v55.md) and
[the additional primary-source review](../../experiments/walking/YAW-RESEARCH-v55.md).

**September 9 follow-through:** the bounded V54 comparison and all evaluations
are complete. The shared controller preserves the 63 flat cases, both full
compositions and five surface passes, and survives both complete downhill
sessions. Yaw oscillation, one final head-posture check and training-coverage
gaps still block advancement. The next recommendation is a focused yaw
refinement from that shared development baseline, followed by unchanged
acceptance gates and replication before wider terrain. See the complete
[results and reassessment](../../experiments/walking/RECIPE-RESULTS-v54.md).
The original research rationale below is retained as the pre-experiment record.

**Recommendation: continue, with a staged locomotion program and a bounded
comparison of training recipes before another braking patch.** A useful walking
envelope across household surfaces is a credible research target. Reliable
operation on arbitrary carpet, loose rugs, stairs and outdoor terrain is not a
single demonstrated capability we can inherit from a paper or checkpoint.

The existing [terrain strategy](TERRAIN_GENERALIZATION.md) already makes the
right distinction: one user-facing walking capability, several training and
test families, and separate physical admission. This review supports that
direction. It changes the immediate emphasis from another residual-loss tweak
to checking the learning recipe, experience distribution and transition design.

## What other teams actually demonstrate

These are primary publications or the authors' repositories. Reported hardware
results belong to those robots and test conditions. A repository task listing
is implementation evidence, not an independently reproduced success rate.

| Source | Evidence and useful lesson | Limit for Ducky |
|---|---|---|
| [Official MicroDuck training repository](https://github.com/pollen-robotics/microduck_rl/blob/2b581c641406a48346e696212930ea881c222c52/README.md) | The same platform has walking, combined walking/recovery, sit–stand and other task implementations, plus normalized policy export and a deployment runtime. Reuse its platform knowledge before designing a wholly new stack. | Its velocity task uses `robot_walk.xml`, with trunk/head contacts stripped. Recovery tasks use a curated ground-contact model; the true full-collision model is listed as unused by tasks. This is not equivalent to our complete-contact acceptance model. |
| [Open Duck Mini sim-to-real](https://github.com/apirrone/Open_Duck_Mini/blob/v2/docs/sim2real.md) and [training code](https://github.com/apirrone/Open_Duck_Playground) | An adjacent small biped provides a public route from actuator identification and reference-guided learning to physical walking. This is more relevant than a purely animated character. | Different mechanics, observations and inference processing; neither its weights nor its action filtering can be silently substituted into our frozen controller. |
| [A-RMA, Cassie, 2022](https://arxiv.org/html/2205.15299v2) | A reference-assisted base controller learns adaptation from observation/action history. The authors then refine the controller with RL using the imperfect learned adaptation estimates, and demonstrate physical walking across varied conditions. | Cassie is a different biped. History helped this method; it does not establish that our current failures require memory. Their bounded simulation survival tests do not replace our full 180-second compositions. |
| [Compliant-terrain HRP-5P, 2025](https://arxiv.org/html/2504.13619v1) | Train standing, turning in place and forward walking on rigid ground, then refine on varied compliance and unevenness. One policy crosses several physical surfaces. Indoor terrain trials succeed in **6/9** cases; standing on slopes remains a reported failure. | Transitions are phase-gated. Soft-contact ranges were chosen empirically, and moving simulated terrain can inject artificial support impulses. The adaptive-clock extension has simulation evidence only. Useful curriculum evidence, not a calibrated carpet model to copy. |
| [Learning to Walk in Minutes, ANYmal](https://proceedings.mlr.press/v164/rudin22a.html) | Large parallel simulation and an adaptive difficulty curriculum make locomotion learning practical; the authors also demonstrate physical transfer. | Published minute-scale training uses their GPU setup and task. It is not a forecast for our native Mac pipeline or our acceptance battery. |
| [Walk These Ways, 2023](https://proceedings.mlr.press/v205/margolis23a.html) | One policy represents different gait, posture and foot-swing strategies. Selecting among them can help on new conditions without retraining for every surface. | A quadruped result. Choosing the right strategy remains part of the system; it does not prove automatic terrain recognition or universal robustness. |
| [Disney's bipedal character, 2024](https://la.disneyresearch.com/publication/design-and-control-of-a-bipedal-robotic-character/) | Command-conditioned RL connects expressive motion references to physical locomotion and composed performances. Motion references can supply a useful starting structure for richer behaviors. | Custom hardware and a different control stack. Character quality and a successful performance are not our safety, endurance or unseen-terrain acceptance tests. |
| [Perceptive locomotion, ANYmal, 2022](https://leggedrobotics.github.io/rl-perceptiveloco/) | A privileged teacher and recurrent student combine proprioception with uncertain terrain perception; the team reports long physical outdoor and underground traversals. | This supports adding anticipation when terrain demands it, after the basic controller works. It does not make a camera or a large recurrent model the first fix for our stopping failures. |
| [Extended servo friction models / BAM](https://arxiv.org/abs/2410.08650v4) | Pendulum identification and validation on four servo types support richer friction models than idealized motor control. Public actuator research is useful physical prior information. | A published actuator fit does not identify this assembled Ducky's inertia, latency, battery behavior or foot–carpet response. Preserve our pinned BAM dependency while comparing models. |

The common pattern is **learn a stable base, allocate real training experience
to the new behavior, retain the old operating conditions, and test physical
transitions**. There is no evidence here that endlessly widening every random
parameter at once is the best route. Nor does this literature establish one
controller architecture as universally superior.

## What the current MicroDuck recipe adds to that picture

The inspected upstream revision is
[`2b581c641406a48346e696212930ea881c222c52`](https://github.com/pollen-robotics/microduck_rl/commit/2b581c641406a48346e696212930ea881c222c52),
dated September 8, 2026, 14:54:49 UTC. The links here pin source behavior rather
than relying on a moving branch or old search excerpts.

Its [velocity configuration](https://github.com/pollen-robotics/microduck_rl/blob/2b581c641406a48346e696212930ea881c222c52/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py)
explicitly reserves 15% of commands for turning in place and progressively
increases zero-command standing from 2% to 25%. The actor uses current
observations; the critic additionally receives simulated base velocity. Command
ranges remain modest while other curricula progress. These are concrete
comparison candidates, not settings already validated under our model.

Its [walking/recovery configuration](https://github.com/pollen-robotics/microduck_rl/blob/2b581c641406a48346e696212930ea881c222c52/src/mjlab_microduck/tasks/microduck_velstand_env_cfg.py)
records its own regressions: recovery experience displaced walking, rewards
interfered across modes, and an improved crouch recovery coincided with failed
prone recovery. The authors changed state sampling, reward activation and
curriculum timing. That development history is unusually relevant to our
retention problem; its causal explanations remain the authors' diagnoses.

More active collision pairs do not, by themselves, establish that our simulator
is more accurate. Geometry, collision exclusions and contact response still need
validation. Conversely, removing a collision to match an upstream demonstration
cannot qualify a candidate under our unchanged acceptance model. Compare model
variants explicitly and retain their separate results.

## What our experiments establish—and what they have not tested

The local source of truth remains the completed reports and receipts:

| Local activity | Observed result | Consequence for the next decision |
|---|---|---|
| [V44 joint sequence training](../../experiments/walking/SEQUENCE-RESULTS-v44.md) | 768,000 transitions; both routed actors trained. Flat, endurance and surface gates regress. **Zero complete downhill training episodes**, despite 527 stochastic downhill falls. | We already tried joint training. Repeating its label is not a new method. Improve the actual learning exposure and retention design; a configured sequence is not a learned sequence. |
| [V50 walking correction](../../experiments/walking/RETENTION-RESULTS-v50.md) | 864,000 transitions across 24 fixed exposed cells. Flat 63/63 and both 180-second compositions retained; downhill yaw improves but stops fail. | This is a useful constrained improvement, not broad randomized terrain training. Its critic sees the same policy observations, unlike the upstream privileged critic. |
| [V52 braking](../../experiments/walking/BRAKING-RESULTS-v52.md) | Both downhill sessions survive their two stops, but yaw still fails; flat retention falls to 38/63 and endurance to 0/2. | Successful stopping trajectories exist in those tested simulated states. The correction does not preserve the broader controller. |
| [V53 retention fitting](../../experiments/walking/BRAKING-RESULTS-v53.md) | Flat returns to 63/63, surfaces to the original 5/14, endurance to 1/2; one downhill session falls again. The fit uses 13,055 stored rows and no new PPO transitions. | More repetitions of the same supervised data are not more environment coverage. Large errors on known downhill onset inputs remain a fitting problem before they can diagnose observability. |

My inference is that **experience coverage, competing objectives and coupled
walk/stop behavior are currently better-supported bottlenecks than a demonstrated
physical impossibility**. This is not proof that the unchanged architecture can
solve every case. Neither a finite failed search nor a negative training run
establishes impossibility.

The original V21 walker / V15 stander with V30 stays retained. The surface
denominator includes rigid controls and exploratory numerical contact settings;
5/14 does not mean five physically validated carpet types. Historical case names
containing `unseen` now belong to exposed development, not protected evidence.

V53's verified learner-state labels are directionally consistent with
[DAgger's distribution-shift motivation](https://proceedings.mlr.press/v15/ross11a.html):
the learner visits states absent from expert demonstrations. One collection of
nine states is not convergence evidence. Fitting targets accurately must still
be followed by closed-loop testing on candidate-generated trajectories.

## How to manage capability growth

Keep one walking capability at the product level: walk, turn, brake, stand and
restart inside a declared envelope. Whether that uses one actor or several is
an engineering choice to test. Do not require a person to select “carpet mode”
for each room. Reserve specialists for a measured need, and test the selector
and every supported handoff as part of the behavior.

| Stage | Scope to develop | Evidence required before broadening |
|---|---|---|
| Stable core | Moderate-speed flat walking, turns, zero-command standing, stops and repeated restarts under existing timing profiles; repair the exposed downhill transition. | Retain 63/63 flat, both whole 180-second compositions and the original five surface passes; pass both complete downhill sessions and all contact, heading and posture gates. |
| Robust numerical envelope | Progressively vary actuator/sensor uncertainty, small slopes, friction and effective compliance, starting from parameters supported by public priors. | Actual applied-parameter coverage, valid resets and enough completed transitions in each training bucket. Preserve old performance. This remains simulation evidence. |
| Carpet and mixed surfaces | Secured low-pile cases first, then explicitly bounded cushioning, edges and surface crossings. Keep compression, friction and swing-foot clearance distinct. | New material/geometry families and combinations held out from tuning; whole-route transitions and endurance. Matched material evidence is needed for calibrated carpet claims. |
| Adaptation or perception | Add observation history if controlled diagnostics expose hidden-state ambiguity. Add terrain perception when safe placement requires seeing an obstacle before contact. | Compare with a simpler controller; verify sensor realism, latency, recurrent-state resets and degraded-input behavior. Version any change to the deployed observation/state contract. |
| Other behaviors | Sit–stand, recovery, head/pose gestures and then task-specific interaction. | Separate entry/exit conditions, failure recovery and continuous handoffs to locomotion, plus the full behavior validation standard. A list of tricks is not a validated library. |

For each stage, retain a frozen reference, a visible development set and protected
final families. Report per-bucket outcomes and whole sessions rather than one
average reward or success rate. Freeze checkpoint selection and failure rules
before training. Replicate a promising recipe across at least three training
seeds before claiming reproducible improvement; test repeats and statistical
acceptance thresholds must be preregistered for the eventual claim. Three seeds
alone are not a reliability guarantee. Never train on the protected final bank.

Our [validation standard](BEHAVIOR_VALIDATION.md) already supplies these evidence
boundaries. This review does not waive thresholds, reclassify failed candidates,
or imply that the maximum requested terrain envelope is mechanically feasible.

## Recommended next activity

**Freeze a controlled locomotion-recipe comparison before spending on a larger
run.** The first question is whether we can improve complete command transitions
without losing the retained controller's performance. Carpet expansion follows
that prerequisite.

1. Map the pinned upstream recipe to our current inputs, commands, motor model,
   collision pairs, reward terms and termination rules. The differences above
   are the starting audit, not evidence of runtime equivalence. Do not silently
   import a different model, command convention or action filter.
2. Specify a common native MuJoCo/BAM comparison harness with unchanged evaluation
   physics and gates. Compare the existing routed walking/standing design with
   a shared command-conditioned actor as a candidate, using explicit standing,
   turning and full-transition training allocation. Declare initialization and
   retention constraints; if recipes change several ingredients, call the
   result a recipe comparison rather than attributing it to architecture alone.
3. Keep the first pilot bounded. Verify baseline replay, policy export, applied
   parameters and transition exposure before a learning run. A privileged critic
   is a useful separate low-interface-cost ablation; actor history and broad
   terrain changes should not be bundled into the same intervention. The exact
   budget, seeds, state curriculum and numeric decision rules remain to be frozen.
4. Require retention plus successful complete downhill sequences before broader
   unseen-surface evaluation. If a pilot still cannot produce meaningful complete
   transition experience, diagnose that failure before increasing its budget.
   A larger dataset or model is not automatically the next remedy.

The pending joint-fit feasibility test can remain a small diagnostic: separate
maximum errors for zero-correction retention and downhill stopping, including
every onset. It should not be the default indefinite development strategy or
stand in for on-policy sequence learning. The current fitting errors do not
justify declaring the 61D actor insufficient.

Reference-guided learning is also worth keeping available if exploration fails:
use verified feasible Ducky motions to shape training, then allow correction.
Do not retarget unrelated robot actions without validating mechanics, and do not
add hidden action assistance to an unchanged policy's evaluation.

## Practical feasibility and physical limits

**A good research bet:** improving the simulated walk/stop envelope, preserving
old skills while introducing bounded terrain variation, and developing additional
simple command-conditioned behaviors. We have working tools and meaningful
negative evidence, plus closely related implementations to compare against.

**Still uncertain:** how broad a physical household-floor envelope this Ducky
assembly can support. Small feet, servo torque/speed, head motion, battery state,
clearance and contact dynamics constrain the answer. Deep pile, unsecured rugs,
snagging and large steps need their own feasibility assessment.

**Not supported:** a promise of all-terrain walking, physically accurate carpet
response from a friction setting alone, or a delivery date inferred from another
lab's demonstration.

The retained V50 run records about **1,004 seconds for 864,000 transitions**
(roughly 861 transitions/s for that run). V53's **8,000 supervised updates took
about 5.4 seconds**; these are entirely different compute units. Neither duration
includes the complete research, evaluation and evidence workflow. See the local
[V50 run](../../logs/retention-native-20260908-v50/run.json) and
[V53 run](../../logs/braking-retention-20260908-v53/run.json). Measure throughput
and evidence bytes per transition for the chosen pilot before projecting a
larger budget or provisioning paid compute. Plan verified external storage for
large receipts without changing old evidence or deleting ambiguous data.

Work can proceed using online sources without asking the owner to collect
measurements. Public motor data, CAD and material tests support priors and scoped
model checks. They do not automatically match the assembled robot and surface.
Successful transfer does not require a perfect fiber-level carpet simulation;
it does require physical evidence for the claimed operating envelope. If matching
public measurements cannot close a calibration gate, keep it explicitly open
while simulation development continues.

## Review scope and provenance

Reviewed current local status, the terrain/behavior standards, V44/V50/V52/V53
reports, current native trainer configuration, the pinned upstream recipe and
the primary sources linked above. The Disney and ANYmal project/publication
pages provide author-reported summaries; this is not an independent replication
of their experiments or an exhaustive survey of all locomotion research.

Small upstream source snapshots are retained locally under ignored
`.workspace/capability-research-20260908/`; immutable public links above carry
the reproducible source identity. Existing source freezes and experiment
receipts are unchanged. No simulator, training, paid resource, hardware action
or policy activation was started for this review.
