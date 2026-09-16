# V48: retain walking and correct downhill standing recovery

V47 reproduces failed downhill and passing matched-flat sessions with complete
handoff histories. Downhill arrives faster, but passing cases also have large
first-standing action jumps. Train standing from original V15 with original
V21 walking deterministic and byte-frozen; retain V30 command control and all
native MuJoCo/contact-v11/BAM physics. No action filtering or blending.

One 24-environment, five-iteration smoke (2,880 learning transitions), followed
by one 48-environment, 500-iteration run (576,000), seed 26090848. FINAL499 only;
no checkpoint selection, extension or second candidate. Fixed .00003 learning
rate, gamma .999, five epochs/four minibatches, original clipped PPO objective,
entropy coefficient zero. Original normalizers and the V15 teacher remain
frozen. Standing exploration starts at half its parent std, limited to
[.005,.25] rad; walking has no exploration and no actor-objective gradient.

Twenty-four cells cross the two flat command orders, downhill and uphill with
the three existing timing profiles and yaw starts 0/.12 rad. Each has HOME and
complete pre-brake (13.00-s) reset states. Initial assignments and subsequent
resets alternate origins. Every pre-brake prefix is executed with the original
pair, and its actual 650 policy outputs are retained; 15,600 prefix controls per
setup are distinct from learning transitions. Episodes continue without handoff
resets to the original 54-s sequence endpoint or a fall. A pre-brake start runs
at most 41 s, and its completions are counted separately from full HOME cycles.
Subsequent windows expose standing-induced restart states to the frozen walker.

Before learning, materialize all 24 cells and compare both reset origins twice
against the original controller for 900 controls or its earlier fall. Require
exact action/observation bytes and physical continuation after non-accumulating
resets. Full histories include MjData, BAM, motor FIFO, sensor history, command
ramp and heading state. Missing/failed original controls remain negative cases.

Reward is exactly V46's tracking, posture, stopping, applied internal-load,
effort, action-change and normalized joint-margin cost. The actor loss adds
online V15 imitation on *flat standing samples only*, plus .2-weight rehearsal
against original stored standing action/observation pairs from all 63 flat
windows and both passing 180-s compositions. Both losses use squared deviations
normalized by .05 rad, with 512 uniformly sampled replay rows per minibatch.
The flat-domain label is optimizer-only metadata; the deployed actor and critic
still consume only 61 observation values. Do not imitate unsafe downhill
standing online. This combined correction is not a factorial ablation.

Evaluate all four exposed banks even after an earlier gate fails. Acceptance
requires all 63 flat windows, both complete 180-s compositions, both original
downhill sessions, and no loss of the five passing V30 surface sessions. Keep
every task, gait, posture, torque, actual joint, heading, body geometry and
200-Hz internal-load gate. All missing windows remain failures. Open the already
separate fresh sequence bank only after every prerequisite passes; protected
terrain banks remain closed. On failure, keep V30 and stop this bounded activity.
Physical calibration, carpet transfer, hardware and policy activation remain unmet.
