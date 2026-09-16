# V54: routed versus shared locomotion recipe

September 9, 2026. Authorized continuation of the capability research sequence.
This first comparison is local simulated development, not physical admission.
Keep V21/V15 with V30 until every prerequisite passes. The V53 residual is not
an initializer. No historical source, score, threshold or hidden bank changes.

## Question and fixed conditions

Can one shared command-conditioned MLP improve complete walk–brake–stand–restart
behavior relative to jointly trained routed V21/V15 MLPs, with explicit short-to-
long transition practice and rehearsal of all previously passing conditions?
This is a recipe comparison: initialization, parameter sharing and parameter
count differ. It is not a clean causal claim about architecture alone.

Both arms use native MuJoCo 3.12, original complete-contact-v11 geometry, pinned
BAM, V16 command ramp, V30 heading controller, 200-Hz physics and raw 50-Hz
61D-to-14D actions. No action filtering, terrain/mode privilege or observation
history is added. Critic observations remain the same 61 actor inputs. A
privileged-critic ablation is deferred. All actual internal loads are recorded
at four physics samples per control, as in V50; complete evaluator gates remain.

The upstream source audit uses commit 2b581c641406a48346e696212930ea881c222c52.
Its current-observation actor, explicit standing/turning allocation and staged
training motivate the comparison. Its stripped walking collisions, independent
sensor-delay/noise recipe, privileged critic, reward weights and later command
extensions are not silently imported. Equal vector dimensions do not establish
runtime equivalence. See `UPSTREAM-RECIPE-AUDIT-v54.md`.

## Initialization and learning budget

The routed arm starts from exact original V21/V15 means and their separately
frozen normalizers. The shared arm is one 512–256–128 ELU MLP initialized from
V21, using its frozen normalizer. Fit that shared initializer for exactly 20,000
Adam updates at 1e-4 using 256 moving and 256 zero-command rows per batch, with
balanced mode MSE on the original retained actors' stored action tensors. This
is supervised initialization, not new RL experience; preserve errors for every
case and both roles. No best-checkpoint selection or extension. Initializer
error is diagnostic, not a behavior pass or a reason to conceal a bad start.

Each arm then receives one 24x5x24 smoke and one 48x1500x24 PPO run: 2,880 smoke
and 1,728,000 main transitions per arm. Seed 26090954, final iteration 1499 only.
Both actors in the routed arm learn, including standing. Shared and routed use
the same fixed 3e-5 PPO rate, gamma .999, five epochs/four batches, clipped
surrogate/value loss, zero entropy bonus and original parent exploration scaled
by .25 with [.005,.15] learned standard-deviation limits. Critic/optimizer start
cold. Preserve parent normalizers throughout.

Use the unchanged V50 reward, including downhill absolute yaw cost, actual
joint margin, posture, torque and internal-load costs. Add mode-balanced replay
retention on 256 moving and 256 standing original labels per PPO minibatch;
scaled squared action error uses .03 rad, weight one. Add weight-one online
teacher retention on flat cells only, for both modes. Teachers stay frozen.
The rehearsal set includes every action from all passing V30 flat windows,
both complete 180-second compositions and exactly five passing surface sessions.
Failed windows and failed whole sessions cannot supply imitation targets.

## Materialized experience and curriculum

Reuse V50's 24 fixed exposed cells: two flat command orders, uphill/downhill
3 degrees, three timing profiles and initial yaw 0/.12. Two worlds per cell.
This is limited geometry/timing coverage, not broad domain randomization.

Each environment progresses independently through three episode layouts:

| Level | Repeated window | Move interval | Episode length |
|---|---:|---:|---:|
| 0 | 6 s | 1–3 s | 18 s (three windows) |
| 1 | 12 s | 1–8 s | 36 s (three windows) |
| 2 | 18 s | 1–13 s | 180 s (ten windows) |

An environment advances by one level only at its next complete HOME reset,
after at least six successes in its last eight episodes at its current level.
Success here means completion without a fall, not independent behavior acceptance.
Level 1 cannot start before 6,000 per-environment controls (iteration 250), and
level 2 before 18,000 (iteration 750). No intra-sequence resets, forced teacher
actions or terrain movements. The common curriculum rule may produce different
exposure in each arm; retain that difference instead of claiming equal data.

Record every input/action, reward component, episode outcome, curriculum level,
actual mode switch, phase count and materialized parameter. Before learning,
check both full-state HOME resets and original-policy/action-insertion replay
for each cell and each layout. Record full comparisons to terminal fall or the
entire layout; stopping early on the actual fall is not successful completion.

## Frozen comparison and decisions

Freeze evaluator source bindings before initializer fitting or candidate rollout.
For each full final, run all 63 exposed flat cases, both original downhill
sessions, both complete 180-second compositions and all 14 exposed surface
sessions, even after an earlier bank fails. Preserve exact normalized ONNX
export and actual-observation parity; the shared arm supplies the identical
policy to both legacy world slots. Those slot labels do not imply two actors.

An arm advances only with 63/63 flat, 2/2 complete 180-second compositions,
both complete downhill sessions and retention of all five original surface
passes, with every unchanged component gate. Require all 24 cells to record
both switch directions and at least one complete level-2 episode per cell for
the training-coverage claim. A coverage failure cannot become generalization.
If neither arm meets prerequisites, retain V30, diagnose the first failure and
reassess the next experiment; do not open fresh/protected terrain banks.

If an arm passes, preregister two additional seeds before claiming reproducible
improvement, then advance to the bounded terrain stage. If both pass, prefer
the shared arm only if it preserves all passing surface sessions of the routed
arm; otherwise report no unambiguous winner. Broader history/perception and new
behavior work remain conditional on the actual need and required foundations.

Use the second external drive for new data; verify mounted-volume identity and
>=20 GB external and >=3 GB internal free space before each main run. Stop owned
compute on nonfinite evidence or I/O error, retaining a failed/interrupted receipt.
Do not silently continue in an unmounted `/Volumes` directory. Guard and launch
must be one conditional operation. No paid compute or hardware is authorized
by this protocol. Physical calibration and carpet transfer remain unmet.
