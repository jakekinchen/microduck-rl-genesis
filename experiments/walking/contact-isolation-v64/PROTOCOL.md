# V64 contact and numerical isolation

Freeze this visible diagnostic before execution. Preserve all V63 and V62
receipts and action bytes. No protected terrain bank, training, daemon, policy
activation, paid compute or hardware is involved.

The question is whether the detailed model's negative replay is sensitive to
physical-export differences, the added foot-shell/floor contacts, or integration
resolution. None of the diagnostic variants is automatically an accepted model.

## Ordered bank

1. Copy V63 poses at the 0.045, 1.475, 1.630 and 2.505 second observations.
   Compare original STL and compiled mesh plane-support extrema for both soles
   and foot shells. Require agreement within 50 nm; read the recorded V63 forces
   separately. No new integration or force estimate is needed for this audit.
2. Run eight controls: V11 and V62, replay and passive, two independent repeats
   each, at the original 5 ms integration step. Every dynamics array must match
   its V63 counterpart byte for byte. Both V11 replays must also satisfy the
   existing original-source conformance rule. Stop the sequence on a mismatch.
3. Run four V62 replay counterfactuals, two repeats each: body/inertial/joint XML
   copied from V11 with all candidate geoms retained; or only the two foot-shell
   floor pairs masked. These are separate interventions, never combined. The
   first must match all 27 declared compiled physical/actuator arrays to V11;
   the second must change exactly two undirected mask-compatibility predicates.
   Other filters, explicit pairs and exclusions remain unchanged. A masked model
   is ineligible for admission even if its replay survives.
4. Run sixteen convergence diagnostics: both models, replay and passive, both
   2.5 ms and 1.25 ms integration, two independent repeats each. Retain 50 Hz
   commands, 200 Hz BAM/friction updates and the physical 20 ms target delay.
   Torque, friction and damping are held between BAM updates. Only integration
   subdivision changes; contact parameters and integrator type are unchanged.

Each case starts from a fresh model, data, BAM controller and HOME-filled FIFO,
with the V63 pose, yaw and duration. Replay requests the original 900 by 14
float32 actions over 18 seconds. Passive requests five seconds at exactly zero
electrical torque, retaining BAM mechanical friction and rotor inertia.
Each child has one attempt and a 240-second process-group deadline. A setup
exception blocks its phase; a measured behavior failure is retained normally.

## Measurements and decisions

Use all V63 physical thresholds, including the exposed 3 mm floor limit, without
relaxation. Sample loads, penetration, state, actual joint limits and warnings
after every integration step. Preserve incomplete prefixes and terminate at
the same fall/hard-stop rules. Read contact solref, solimp, friction, dimension
and margin from actual solver contacts, alongside applied forces. Recompute
load occupancy and continuous duration using the actual integration period.

Verify every recorded action against the original tensor bytes and independently
reconstruct the 200 Hz FIFO timeline. Check identical targets, motor torque,
friction and damping throughout each finer integration group. Deterministic
repeat equality excludes wall-clock timing; it does not establish start diversity.

For the shell mask, divergence before the first original shell/floor contact
must remain below 1e-10 in state and torque. A later change is materially visible
if root displacement exceeds 1 mm, a joint exceeds 1 degree, terminal status
changes or terminal time shifts by more than 20 ms. This local counterfactual
tests the pair's contribution; it does not establish a physically correct model.

For the two finest integration settings, report the whole common observed
prefix on the coarser grid. The preregistered agreement screen requires root
difference at most 1 mm, joint difference at most 1 degree, peak ground-depth
difference at most 0.5 mm, internal-depth difference at most 0.25 mm, the same
terminal category and terminal-time difference at most 20 ms. Missing duration
cannot pass the underlying behavior gates. This screen is a numerical diagnostic,
not a mathematical convergence proof or measured calibration.

Only reconsider a standing-policy startup handoff after an unmasked full model
has resolved these contact/numerical questions. Otherwise retain the negative
and identify the next bounded physical-model investigation. No training follows
an unresolved physics diagnostic.

MuJoCo's mask predicate permits isolating a pair while preserving other mask
decisions; explicit pairs and parent/weld filters require separate checks.
[Official collision selection](https://mujoco.readthedocs.io/en/stable/computation/index.html#selection).
Its contact parameters couple softness and numerical response; smaller steps
alone cannot establish physical fidelity.
[Official solver guidance](https://mujoco.readthedocs.io/en/stable/modeling.html#solver-parameters).
