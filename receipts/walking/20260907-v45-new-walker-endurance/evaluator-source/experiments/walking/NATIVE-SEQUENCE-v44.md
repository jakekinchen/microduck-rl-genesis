# V44: joint native full-sequence refinement

Preregister before either smoke or learning. One smoke (8 environments x 5 x
24 transitions) and one full run (64 x 500 x 24 = 768,000 transitions), seed
26090744; FINAL499 only. Failed gates terminate promotion, not erase the run.
No hyperparameter/checkpoint search or automatic extension.

Start from the exact retained V21 walker and V15 stander, preserving both means
and frozen observation normalizers. Route two independently trainable MLPs by
exact zero of the unnormalized three-axis actor command. The original V16 ramp
and V30 heading controller remain fixed. Exploration starts at one quarter of
each parent's standard deviation (no deterministic action modification), with
std bounded [.005, .15]. PPO: fixed learning rate 3e-5, entropy 0, gamma .999,
otherwise original five-epoch/four-minibatch PPO. Cold critic and optimizer;
critic sees the same 61 observations. No phase, terrain or simulator privilege
enters actor/critic observations. Reward uses simulation velocity, posture,
actual joint positions, 200-Hz applied internal loads and torque occupancy.

The intervention is sequence training of both actors, including its conservative
native exploration/learning settings. This bundled experiment does not identify
separate causal effects of each setting. Independent acceptance uses the old
reward-independent evaluator, not the reward or episode survival.

Each episode is 54 seconds with three continuous 18-second windows: stand 0-1 s,
move 1-13 s, brake and stand through 18 s. Advance through forward, both turns,
and both arcs on flat; alternate .10/.12 m/s straight commands on +/-3-degree
slopes. Command order advances with each completed/fallen episode. Equal fixed
environment allocation to two flat orders, downhill and uphill. No intermediate
state resets or teacher actions. Falls reset to complete HOME state including
BAM, motor/sensor FIFO and heading/ramp state. Training coverage must report
actual phase counts, both actor switches, complete episodes and falls per
bucket. Retain every actual 61D observation and 14D sampled action as float32
bytes with streaming digests, plus every switch's actuator/sensor history.
The latter JSON is diagnostic state coverage, not a full MjData snapshot.

Physics stays native MuJoCo 3.12.0, contact-v11 original CAD coverage, pinned BAM,
200-Hz integration and 50-Hz unfiltered normalized 61-to-14 policy interface.
Motor delay six physics ticks, sensor delay one control tick. Balanced template
allocation is limited materialized terrain coverage, not broad randomization.
Before training, compare all original closed-loop actor inputs/actions/physical
states with the sequence adapter and repeat full HOME resets byte-exactly.

Frozen acceptance order: all 21 original and 42 exposed repeated flat gates;
all four original diagnostic sessions (two downhill, two 180-s compositions);
all 14 exposed surface sessions. Preserve each previously passed surface session
and improve both downhill sessions; require all task, bilateral stepping, loaded
slip, joint-stop, torque, posture, body geometry, internal-load and heading gates.
No missing component or unrun window can pass. Never change frozen thresholds.

Only if those prerequisites pass, open the separately frozen V44 fresh sequence
bank: four new flat order/timing/heading compositions and two slope sequences.
Every session must pass; these are new combinations of already exposed terrain
families, not unseen carpet specimens or protected physical acceptance. The bank
is not read by training and is not used for checkpoint selection.

Reject on any prerequisite regression; retain the V30 pair, summarize the first
failure and actual training coverage, and select the next bounded diagnosis.
Fresh terrain/protected final banks remain closed. Real Ducky calibration,
cross-engine numerical agreement on softer contacts and physical transfer remain
unmet. No hardware, paid compute, publication or policy activation.
