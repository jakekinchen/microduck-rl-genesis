# Laser-following development experiment

Current priority: [systemic gait diagnosis and correction](GAIT_DIAGNOSIS.md).
The earlier pursuit scores do not establish credible walking. Actual hip-stop
parking, low-clearance shuffling and slipping reject the turn-v2 policy.

For the September 5 dynamic extension, live drag/keyboard controls, moving
routes, domain-randomization training and measured comparisons, see
[Dynamic pursuit build](DYNAMIC_BUILD.md). The selected experimental policy
passes 11/12 reserved randomized development trials versus 2/12 previously;
one trial still falls. These scores are target-only, not gait acceptance.

User-directed work on 2026-09-04. This is a new local first-party task, not a
workaround for third-party provenance or physical-operation requirements.

## Architecture and claim boundary

The actor still takes 61 observations and emits 14 unfiltered joint deltas at
50 Hz. A separate deterministic steering function converts a visible ground
target into ordinary `vx, vy, wz` commands. PPO learns the joint actions in
Genesis with BAM; the steering layer is not learned. No IK or joint-action
assistance is added. Existing M5-bound source files remain unchanged.

The current controller receives **simulated ground-truth spot coordinates**.
It is not an end-to-end camera policy. `detect_red_spot` is a conservative RGB
detector, tested on images and evaluated on rendered video, but its pixels do
not drive this experiment. Real camera following still needs calibrated
camera/ground geometry, camera-frame conventions, latency/dropout validation,
and a separately authorized hardware test.

Camera audit: the locked model's `head_camera` at HOME has world position
approximately `(0.0643, -0.00009, 0.2531)` m, optical forward `(-1, 0, 0)`,
and vertical FOV 45 degrees. Positive walking X is therefore behind that
camera. MuJoCo's [camera convention](https://mujoco.readthedocs.io/en/latest/modeling.html#cameras)
is optical negative Z, image right positive X, image up positive Y. Resolve
this in a versioned camera adapter/model before claiming onboard visibility;
do not silently rotate a frozen model or feed oracle coordinates as detections.
Reproducible audit and head-camera image:
`receipts/laser-follow/20260904-camera-audit/`.
The later camera-v2 adapter fixes optical forward and image-up using the CAD
site/mouth frame, without changing physics or actions. The physical robot faces
+X; the inward-looking legacy camera was the bug, not the walking convention.
See `receipts/laser-gait/20260905-camera-alignment-v2-r2/`. Close ground targets
can still leave the FOV at HOME; there is no camera-driven policy yet.

## Research

- [Thomas Wolf's Microduck laser-following post on X](https://x.com/Thom_Wolf/status/2092959363992326236)
  was located through an [indexed reproduction](https://zamantika.com/tl/Thom_Wolf/status/2092959363992326236).
  It describes an image-detector integration. X itself was not retrievable,
  and the demonstration does not establish that its laser-specific steering
  was trained with RL.
- The primary [Microduck runtime design](https://github.com/pollen-robotics/microduck/blob/main/docs/design/robotd-design.md)
  documents legacy laser tracking sign flags and places ball/laser detection
  in the media service. Its linked legacy `apirrone/microduck_runtime` repo
  returned 404 during this research; no unretrieved code is claimed as reused.
- The [official training repository](https://github.com/pollen-robotics/microduck_rl)
  describes PPO-trained, 50 Hz ONNX locomotion. We reuse our local equivalent,
  not an unverified downloaded policy.

## Reward and curriculum v1

Keep the existing velocity task's BAM, joint, posture, foot, and action-rate
terms. Increase velocity tracking to 5, upright to 3, and reduce pose to 0.5;
head commands stay zero. Add:

- 4 × forward progress rate toward the current target, normalized by 0.25 m/s,
  clipped to [-1, 1], gated by uprightness and target availability.
- 1 × settled stopping reward when the target is within 0.18 m or unavailable.
- -5 per fall event; terminate below 0.07 m or beyond 70 degrees tilt.

Progress uses the **robot's velocity**, not target distance differences: target
motion and target respawning cannot manufacture progress reward. Rate rewards
are multiplied by the 20 ms control period; the terminal penalty is an event.

Targets initially spawn 0.3–0.9 m away, within ±45 degrees. At iteration 300,
the angle expands to ±110 degrees; at 400, targets move at up to 0.04 m/s per
axis. Every five seconds, 10% are unavailable, generating a zero-motion
command. Startup and episode randomization remain enabled; velocity pushes
are disabled for this first pursuit curriculum. Training episodes retain
stochastic exploration; deterministic evaluation has no automatic fall reset.

## Reproduce

Use unique run/output names. The tools reject existing output directories.

```sh
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python scripts/train_laser.py \
  --run-id laser-smoke-NEW --num-envs 64 --iterations 5

GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python scripts/train_laser.py \
  --run-id laser-follow-NEW --num-envs 1024 --iterations 500 \
  --warm-start-own-baseline

.venv-apple/bin/python scripts/evaluate_laser.py \
  --run-id laser-follow-NEW \
  --bam-repo /path/to/exact/pinned/bam \
  --output receipts/laser-follow/NEW --video
```

Warm-start loads only the digest-checked local first-party seed-26090401
checkpoint (100 prior iterations / 2,457,600 transitions). The new curriculum
counter starts at zero; actor, critic, normalizer, and optimizer are retained.
Without the flag, training starts from scratch. The 500-iteration run adds
12,288,000 transitions; the 64×5 smoke adds 7,680 independent transitions.

The training receipt saves effective config, seed, source/package hashes,
parent checkpoint digest, final checkpoint digest, and measured duration.
Export requires the completed local receipt and matching sources/checkpoint;
the canonical normalizer-plus-MLP exporter is reused with fixed-batch ONNX.

## Independent evaluation

`suite-v1.json` freezes six **visible-development** cases and thresholds before
the training outcome: forward, left, right, already-near stop, target loss,
and a moving target. C MuJoCo + pinned BAM runs the exact ONNX at 50 Hz, with
measured inference latency, full control-step records, and explicit fall
termination. Videos show a red, non-colliding marker at the actual target.
The marker is rendering-only, not a physical assistance object.

Stopping/loss cases can pass for a policy that never walks. Therefore a
2/6 aggregate is not evidence of pursuit. Report acquisition cases and moving
tracking separately; never turn increased reward into accepted task success.

The baseline receipt is `receipts/laser-follow/20260904-v1-baseline/`: 2/6
checks pass (near-stop and target-loss), but 0/3 distant targets are acquired,
and the moving-target case fails. Forward displacement is about 1.45 cm in
12 seconds. No falls occurred in this baseline battery.
The repeat receipt `20260904-v1-baseline-repeat` matches all 3,100 control-step
states, actions, and targets exactly, excluding measured wall-clock latency.

For a trained policy that fails C MuJoCo, run
`scripts/evaluate_laser_genesis.py --evaluation RECEIPT --output NEW_DIRECTORY`
to test those same cases in Genesis CPU. This is a diagnostic to localize the
remaining work, not an independent or held-out acceptance shortcut.

## Queue

- [x] Find online precedent and distinguish perception from learned locomotion.
- [x] Implement versioned target steering, PPO reward, curriculum, and loss stop.
- [x] Pass 64×5 local smoke and steering/perception tests.
- [x] Freeze independent cases and measure the pretraining baseline.
- [x] Complete 1024×500 fine-tuning and retain checkpoint/run provenance.
- [x] Export, verify randomized/real-observation parity, evaluate all six cases.
- [x] Inspect videos and report actual approach/stop/moving-target behavior.
- [x] Preserve the failed v1 result and refine the command adapter without
  changing the checkpoint or acceptance thresholds; v2 passes 6/6 C MuJoCo cases.
- [ ] Connect pixels through calibrated ground geometry; test false positives,
  ambiguity, occlusion, stale frames, lighting changes, and target reacquisition.
- [ ] Hardware integration and safe physical testing under separate authority.

## Completed result (2026-09-04)

The bounded run completed 500 PPO iterations / **12,288,000 new transitions**
in 1,282.7 seconds including simulator startup (21.4 minutes). It warm-started
our 2,457,600-transition first-party checkpoint; no external weights or paid
cloud resources were used. The final checkpoint is
`d5c6592881d061cd47c0c66b220cdebc9c9f43fe2a3d9f9fcff4d58703e827f6`.

The v1 trained controller moved 39.5 cm forward but settled 25.1–25.6 cm from
the three distant dots, just outside the frozen 24 cm threshold. It passed
2/6 C MuJoCo tests, versus 5/6 in Genesis (moving tracking failed there too).
That negative result remains at `20260904-v1-trained`; it was not relabeled.

The versioned **deployment-only** `laser-steering-approach-v2` adapter raises
the distance-to-forward-velocity gain from 1.5/s to 3/s, keeping the 0.25 m/s
speed cap, target-loss stop, 0.18 m command stop radius, and angular controller.
This compensates for weak motion under small velocity commands; it is not
additional RL training or a change to joint actions. The policy is byte-identical:
ONNX SHA-256 `8c5fd28e4f65125d469f6946c51fdd9561a3c35b5bbabb71e6af2515270208ad`.
Run it with the evaluation command above plus `--approach-gain 3.0`.

V2 passes **6/6 visible-development C MuJoCo/BAM cases**, with zero falls and
zero measured inference deadline misses in the primary run:

| Case | Result |
|---|---|
| Forward / left / right | Acquired; final stand-off 20.9 / 21.2 / 21.4 cm |
| Near stop | Remained settled; passed |
| Target loss | Stopped; max speed after grace period 0.010 m/s |
| Moving dot | Within 28 cm for 100% of samples after 4 s; final gap 22.0 cm |

V2 also passes 6/6 in Genesis CPU (`20260904-v2-genesis`). A second C MuJoCo
run (`20260904-v2-repeat`) reproduces all 3,100 control-step states/actions/
targets exactly, excluding measured latency. As an ablation, the old policy
with this same stronger steering still passes only 2/6 (`20260904-v2-baseline`):
the learned locomotion, not the gain change alone, is necessary for pursuit.

Primary receipt: `receipts/laser-follow/20260904-v2-steering/`. The original
training receipt includes complete stdout, learning curve, checkpoint,
normalizer, exact source snapshots, and hashes. Randomized Torch/ONNX parity
is 3.34e-6 rad; real MuJoCo-observation parity is below 2e-6 rad.

This establishes a working **simulated target-following prototype**, tuned on
visible cases. It does not establish camera-driven laser detection/control,
blind held-out robustness, canonical walking acceptance, or physical success.
