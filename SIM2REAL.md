# Deployment contract — what the robot must receive

**English** · [Français](SIM2REAL.fr.md)

This document describes **exactly** what a policy exported by `export_onnx.py`
expects. It is the counterpart of the embedded runtime of
[pollen-robotics/microduck](https://github.com/pollen-robotics/microduck): a
policy trained here honours the same contract as those trained upstream, so it
plugs in without modification.

Everything below is verifiable in the code: `microduck/constants.py` for the
layout, `microduck/velocity_env.py::_compute_observations` for how it is built.

## 1. Rate

| | |
|---|---|
| Control frequency | **50 Hz** (20 ms period) |
| Physics step in simulation | 5 ms, decimation 4 |
| Action filtering | **none** |

⚠️ **The policy is not filtered.** No low-pass is applied to the action during
training. Adding one on the runtime side — or removing one — breaks transfer in
both directions.

## 2. Input: the 61-D observation vector

**Strict** order. All quantities are SI, in the trunk ("body") frame unless
stated otherwise.

| Indices | Name | Dim | Content |
|---|---|---|---|
| `[0:3]` | `base_ang_vel` | 3 | trunk angular velocity, body frame, rad/s (IMU gyroscope) |
| `[3:6]` | `projected_gravity` | 3 | **unit** gravity vector projected into the body frame |
| `[6:20]` | `joint_pos` | 14 | joint position **relative to HOME**, rad |
| `[20:34]` | `joint_vel` | 14 | joint velocity, rad/s |
| `[34:48]` | `actions` | 14 | **previous** action, raw (before scaling) |
| `[48:51]` | `twist` | 3 | command `[vx, vy, ωz]` in m/s, m/s, rad/s |
| `[51:55]` | `head_pose` | 4 | head-pose command, deltas from HOME, rad |
| `[55:61]` | `body_pose` | 6 | trunk-pose command `[x, y, z, roll, pitch, yaw]` |

The first 48 dimensions are proprioception, the last 13 are commands. **An
unused command slot is set to zero, it is never removed**: that is what lets the
runtime hot-swap policies behind a single observation buffer.

### Details that matter

- **`projected_gravity`** is the world `(0, 0, −1)` vector expressed in the body
  frame. Standing level, it equals `(0, 0, −1)`.
- **`joint_pos` is relative to HOME**, not absolute. Subtract
  `constants.DEFAULT_JOINT_POS` from the encoder reading.
- **`actions`** is the **raw** action returned by the network at the previous
  step, not the joint setpoint derived from it.
- No per-term scaling is applied to the input: normalisation is **baked into the
  ONNX** (empirical mean and standard deviation learned during training). Never
  convert a checkpoint by hand.

## 3. Output: 14 actions

The ONNX returns a vector of 14 values, in the canonical servo order:

```
0  left_hip_yaw     5  neck_pitch     9  right_hip_yaw
1  left_hip_roll    6  head_pitch    10  right_hip_roll
2  left_hip_pitch   7  head_yaw      11  right_hip_pitch
3  left_knee        8  head_roll     12  right_knee
4  left_ankle                        13  right_ankle
```

The setpoint sent to the servos is:

```
q_target[i] = HOME[i] + action[i] * ACTION_SCALE      # ACTION_SCALE = 1.0
```

`HOME` is `constants.HOME_JOINT_POS` (the STAND2 pose: trunk moved ~5 mm forward
so the centre of mass falls on the ankle axis).

This is a **position** setpoint, sent to the servo's position controller. The
simulation models that controller (the XL330 firmware voltage law, gain
`kp = 200`), it does not replace it.

## 4. What the simulation modelled of the real robot

If any of these does not match the target robot, transfer degrades:

| Item | Simulated value |
|---|---|
| Servos | Dynamixel XL330, BAM M6 model bench-fitted |
| Firmware gain | `kp = 200` (stiffness kept from the Microduck) |
| Supply voltage | drawn per robot in **6.5 – 8.2 V** |
| Voltage drop under load | `V = V₀ − R·I`, `R ∈ [0, 0.2] Ω`, floor 6.0 V |
| Firmware current limit | 1.75 A |
| Command delay (bus) | 3 to 6 physics steps = **15 to 30 ms** |
| IMU delay | 0 to 1 control step = 0 to 20 ms |
| `joint_vel` delay | exactly 1 control step (firmware moving average) |
| Encoder bias | ±0.015 rad (±0.86°), constant per robot |
| Gear backlash | ±1° per servo, encoder read through it (with `--backlash`) |
| IMU misalignment | random axis rotation, ≤ 6° |
| Sole friction | ratio drawn in 0.7 – 1.3 |
| Trunk mass / inertia | ±5 % |
| Trunk / head centre of mass | ±15 mm / ±10 mm (ramped by curriculum) |
| Pushes | ±0.3 m/s every 3 to 6 s |

## 5. Known limits

1. **No real-robot trial has been made from this repository.** The contract is
   honoured and the physics is numerically validated against MuJoCo (see the
   README, §7), but that does not replace a deployment.
2. **The contact engine is Genesis, not MuJoCo.** The difference measured over
   one second of walking is small, but not zero.
3. **Gear backlash is modelled, but you have to enable it.** `--backlash` trains
   on the model where each servo carries ±1° of play in series, with the
   firmware loop AND the observations read *through* the play (the real servo's
   encoder is on the output side). Without that flag, the simulation is more
   optimistic than the real robot about position accuracy. Observation and
   action dimensions are identical, so the runtime sees no difference.
4. **No exteroception.** Proprioception only: the policy cannot avoid an
   obstacle it cannot see.

## 6. Verifying an export

```bash
python export_onnx.py -e microduck-velocity -o walk.onnx
```

The script prints the observation layout and compares the ONNX output against
the PyTorch module on a batch of random observations (the difference must stay
below 1e-4 rad, i.e. 0.006° — a hundred times finer than anything meaningful on
an XL330). It fails if the normaliser was not properly folded into the graph,
and warns if the policy returns the same action regardless of the observation —
which happens with a checkpoint taken too early.

**That check validates the conversion, not the wiring.** Before putting anything
on the robot, also run:

```bash
python tests/test_onnx_deploy.py microduck-velocity
```

That one rolls out a real episode and compares, at every step, the action of the
trained policy against the one onnxruntime returns when fed **the same
observation the environment just assembled**. It is the only check that would
catch:

- a permutation of the 14 servos between training order and export order;
- a normaliser left adaptive instead of frozen;
- the wrong observation group read from the `TensorDict` (the actor reads only
  `policy`, never `privileged`).

None of these three raises an exception. They only show up when the robot falls.

Measured on the walking policy: **4.8·10⁻⁷ rad** maximum difference over 60 steps.
