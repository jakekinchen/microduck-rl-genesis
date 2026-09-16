# Expanding Ducky's walking to carpet and other surfaces

Status: development strategy with public-data experiments, September 6, 2026.
Numerical surface-stress training is distinct from calibrated carpet training
and physical trials; neither physical claim has been established.
The current ordered work remains in `TRAINING_ACTUALIZATION.md`.

## Capability and controller choice

Keep one user-facing walking capability: commanded forward/lateral/yaw motion,
standing, stopping and continuous transitions within a documented envelope.
Aim for a general locomotion controller trained over multiple surface families.
Give carpet its own curriculum stage and acceptance matrix. Do not create one
manually selected behavior per carpet or assume that a terrain label is needed
by the deployed actor.

The current implementation uses V21 walking and V15 standing actors. Both actors
and their switching/controller logic must be tested together on every supported
surface. Training the walking actor alone cannot repair an untrained standing
transition. Joint training, transition-state training or a unified actor are
candidate interventions; choose through a frozen comparison rather than assuming
one architecture is already the solution.

Keep specialist policies as a later option when experiments demonstrate a real
tradeoff, such as a distinct stair-climbing or very soft-ground regime. Any
automatic selector then adds observability, hysteresis, transition and failure
tests. A specialist does not remove the obligation to validate surface crossings.

## Starting evidence

V21's inherited training is nominal rigid-ground training with timing variation;
V22 physical variations and V23 terrain cases were evaluations of fixed weights.
They did not expand the training distribution. V23 passed four sustained
180-second walks, but new terrain passed only 2/12 sessions, and both long
compositions failed whole-session heading. No existing result demonstrates real
carpet walking. See `experiments/walking/V23-RESULTS.md`.

V30 subsequently passes all 63 original flat gates and both three-minute
compositions, reducing heading endpoints to 6.24/8.95 degrees. Public surface
refinements do not add a fully passing surface bucket; final surface acceptance
is 5/14. The full comparison, physics gaps and retained failures are in
`experiments/walking/PUBLIC-SURFACES-RESULTS.md`.

## Public data without owner-collected measurements

The owner requested an online-data route. Public collection, source checks,
contact-model diagnostics and local policy experiments can proceed without
asking the owner to acquire measurements. The evidence catalog is
`experiments/walking/public-surfaces-v1/evidence.json`; source-specific decisions
are in `experiments/walking/public-surfaces-v1/RESEARCH-NOTES.md`.

Published carpet construction, static compression and contact-pair friction
provide scoped priors. ISRD provides surface-related sensor features from a
different robot; its 30,709 rows were inspected but excluded from Ducky policy
training and material fitting. None of these sources identifies a matched
Ducky-foot carpet response at gait loads and rates. Do not convert missing
measurements into synthetic physical evidence.

V25/V27 therefore test explicitly exploratory soft-contact settings. Passive
settling, timestep sensitivity and cross-engine checks verify their numerical
implementation. Agreement does not establish a carpet constitutive model:
the normalized contact model's indentation barely changes across probe masses.
Loose rugs, pile snagging, underlay hysteresis and physical battery/thermal
endurance remain outside these experiments.

Keep local simulation development executable while physical admission remains
open. Public matched measurements could eventually close particular calibration
gates; a general-purpose dataset or a successful unrelated robot cannot. The
stages below describe the evidence needed for supported physical operation,
not an instruction for the owner to perform data collection.

## Development stages

| Stage | Work | Evidence required to advance |
|---|---|---|
| 0. Fix the existing composition | Isolate STOP heading drift and standing handoffs, including downhill initial states. | Preserve original regression tests; require heading across the entire session, start/stop safety, no bracing/interference, and successful standing transitions. Do not average separate windows into a composition pass. |
| 1. Measure representative surfaces | Start with secured low-pile carpet, then a different pile/backing and cushioned carpet. Record the actual floor/underlay/anchoring configuration. | Identified physical samples and robot assembly; calibrated force/displacement/drag measurements with uncertainty and separate validation acquisitions. |
| 2. Build and verify effective contact models | Model measured friction, compression/recovery, height and edges. Keep robot geometry/inertia/actuator calibration separate. | Held-out loading/unloading and drag/landing responses match preregistered tolerances. Verify engine parameters, contact pairs, timestep/solver sensitivity and appropriate cross-engine diagnostics. |
| 3. Train progressively | Begin with measured easy carpet conditions at conservative speed, then expand softness, direction, transitions and combinations. | Actual runtime coverage, no reset accumulation or cross-environment leakage; controlled comparisons against the frozen base across multiple training seeds. |
| 4. Test unfamiliar materials and layouts | Hold out actual carpet specimens/products, underlays and crossing layouts; evaluate new combinations. | Every required surface/command/transition bucket passes independently, with complete failure denominators and uncertainty. New seeds of a familiar specimen do not establish material generalization. |
| 5. Establish physical support | Supervised physical starts, turns, STOP, repeated crossings and endurance on the named surfaces. | Same gates using external ground truth where needed, retained telemetry and videos, repeat sessions and declared speed/load/battery bounds. Physical admission stays separate from simulation admission. |

The next executable experiment must freeze its numerical limits, sampling
distribution, curriculum schedule, training budget, seeds, repeats and decision
rule before launch. This strategy document is not that preregistration.

## What a carpet model must represent

Changing a rigid floor's friction coefficient does not validate carpet physics.
Measure force versus indentation, recovery and hysteresis under loads relevant
to Ducky's feet; static breakaway and steady sliding in different directions;
loaded carpet height, backing and underlay; and rug-edge geometry and movement.
Pile may impede a swinging foot even when the support surface has high traction.
Begin with secured specimens. Loose rugs, deep pile and fiber snagging remain
outside support until represented and independently tested.

An effective contact model may be sufficient; simulating every fiber is not a
prerequisite. It must reproduce the physical responses that affect the gait.
Fit only on the declared calibration split. Parameter values copied from another
robot or visually plausible penetration do not establish that match. Soft foot
contact must not disable body-to-body collision or internal-load gates.

The existing passive calibration intake covers mass, planar COM and kinetic sled
friction. It does not yet measure compression, hysteresis, snagging or landing
dynamics. Those require a separately specified collection and analysis stage.

## Manage training and validation separately

In RL, broadening the training set means changing the environments and situations
that produce rollouts, not merely collecting more checkpoints or evaluation
videos. Preserve the current nominal model as a baseline. Each training version
records the exact terrain families, realistic parameter correlations, frequency
of sampling, command speeds, starts and perturbations. Retain a nonzero mixture
of prior easy surfaces and regression gates to catch forgetting.

Introduce one uncertainty family at a time for diagnosis, then combine them.
Sample valid physical configurations: backing, softness, friction and rug motion
are not automatically independent uniform variables. Advance difficulty using
development performance within each bucket. Do not widen every range at once,
use reward alone as the curriculum signal, or move terrain under a loaded foot
as an undocumented source of assistance. Exposure to hard cases must not starve
learning of successful stepping examples.

Maintain separate training, visible development, protected final, physical
calibration and physical validation populations. Use development failures for
learning; a final result becomes exposed when inspected. Keep complete sessions
and physical specimens together when splitting. Freeze each candidate before
final evaluation, report per-family outcomes and confidence bounds appropriate
to independent trial units, and retain a fallback/unsupported designation for
conditions outside the tested envelope. Never claim all terrains from a finite
test matrix.

Every supported surface needs straight travel, both turns/arcs, stopping, restart,
surface entry/exit, one foot on each surface, different approach angles and long
continuous operation. Include slip, sole clearance relative to support, contact
loads, joint/torque limits, body collisions, heading, non-foot support, falls and
physical battery/temperature limits. Video and reward cannot replace these gates.

## Adaptation and sensing

Start with the existing deployable sensor interface. If a well-designed mixed
curriculum plateaus because instantaneous observations cannot distinguish surface
response, compare a short observation/action history or an adaptation estimator
under an explicitly versioned interface and latency budget. The deployment side
must infer conditions from available sensors; privileged simulator friction or
terrain labels may help a training critic/teacher but must not leak into the
deployed actor. No online weight updates on hardware are assumed.

Use perception when anticipating a terrain feature becomes necessary; reactive
proprioception cannot guarantee suitable foot placement before an unseen edge.
Any extra sensor or specialist selector creates its own validation requirements.

## Research informing the recommendation

- Singh et al., [Robust Humanoid Walking on Compliant and Uneven Terrain](https://arxiv.org/html/2504.13619v1): a shared policy, staged terrain exposure and compliance modeling on another biped. Their numerical ranges and robot-specific assumptions are not Ducky calibration.
- Kumar et al., [Rapid Motor Adaptation](https://ashish-kmr.github.io/rma-legged-robots/): a base policy plus an adaptation module across changing conditions on a quadruped.
- Kumar et al., [Adapting Rapid Motor Adaptation for Bipedal Robots](https://arxiv.org/abs/2205.15299): evidence that adaptation can also help bipedal locomotion. This supports an architecture experiment if needed, not a promise about Ducky.
