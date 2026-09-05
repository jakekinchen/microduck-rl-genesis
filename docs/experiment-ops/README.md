# Offline experiment diagnostics

Use these tools alongside Duck Lab while training continues. They use Python's
standard library and read existing traces or process metadata. They do not
import Genesis, Torch, MuJoCo or ONNX; start training; change environments;
signal processes; or modify checkpoints and receipts.

## Inspect work already running

```sh
./scripts/duck-ops activity
./scripts/duck-ops guard
```

`guard` returns 3 when a known local Python training entrypoint is running,
2 when inventory fails, and 0 when no known entrypoint is found. The JSON
distinguishes repository-owned, other-directory and unknown-owner processes.
Other checkouts can still compete for the same Mac, so they remain visible.
Full command arguments and environment variables are never returned.

This is an advisory check before a **future** launch, not an atomic lease,
training admission, or proof that the host is idle. Unknown launchers, remote
jobs, child interpreters with different names and process races are outside
coverage. Existing scripts are deliberately not wrapped while they are active.
There is no kill, stop, cleanup, automatic restart or training endpoint.

## Find the first divergent sample

```sh
./scripts/duck-ops compare \
  receipts/laser-follow/20260904-v1-trained/trajectory.jsonl \
  receipts/laser-follow/20260904-v1-genesis/trajectory.jsonl \
  --output .workspace/diagnostics/laser-v1-NEW
open .workspace/diagnostics/laser-v1-NEW/index.html
```

The output directory must be new. It contains a portable `index.html` and
`comparison.json`. The HTML works offline, with no service or network calls.
Choose a case, scrub time, or jump to the first observed difference. Sources
are identified by full path and SHA-256, and first differences include original
line numbers. Original receipt bytes are never rewritten.

The retained v1 baseline versus its repeat provides a useful control:

```sh
./scripts/duck-ops compare \
  receipts/laser-follow/20260904-v1-baseline/trajectory.jsonl \
  receipts/laser-follow/20260904-v1-baseline-repeat/trajectory.jsonl \
  --output .workspace/diagnostics/baseline-repeat-NEW
```

Both contain 3,100 samples across six cases. Recorded action, command, target,
position and event values agree. Wall-clock inference latency is intentionally
excluded from this semantic comparison. The baseline still failed pursuit;
repeatability does not establish a useful behavior.

The trained v1 Genesis versus C MuJoCo comparison also has 3,100 aligned samples.
For the forward case the first recorded position difference is at 0.020 s
(maximum component difference about 0.120 mm), then commands and actions first
differ at 0.040 s. This prioritizes reset, first-step actuator/force and contact
inspection; it does **not** identify which of them caused the difference.
These are feedback rollouts. All six cases eventually use different actions.

## Interpret the result

| Classification | Meaning |
|---|---|
| `fixed_recorded_actions` | Every recorded action value matches on the complete observed time alignment. |
| `different_recorded_actions` | At least one recorded action differs. Do not attribute the whole rollout difference to physics alone. |
| `incomplete_or_misaligned` | A case or timestamp is missing on one side. A matching prefix cannot hide truncation. |
| `action_telemetry_missing` | Aligned traces lack one or more action records. Equality stays unknown. |

JSON does not preserve original tensor bytes/dtype. The comparison packs parsed
numeric values as binary64 with no rounding, tolerance, clipping or signed-zero
erasure. Its value hashes are **not** tensor-byte hashes. Position uses a
diagnostic maximum-component tolerance of 1e-6 m by default, adjustable with
`--position-tolerance-m`. Raw deltas remain visible. This tolerance never changes
actions or any task acceptance threshold.

Missing contacts remain unknown. Contact lists, if supplied, must use canonical
pair-name strings and are compared independent of order. Missing samples on
both sides cannot be discovered without an expected schedule; equal observed
times alone do not prove the 50 Hz contract or full episode coverage. The
existing evaluator owns those checks. No interpolation, best-fit time offset,
trajectory warp or automatic reclassification is performed.

Input is bounded to 16 MiB, 20,000 rows and 256 cases per file. Empty input,
duplicate keys/times, nonfinite values, malformed vectors and a file changing
during the read are rejected. Retain a terminal copy before comparing an active
trace. Limits are deliberate to keep inspection cheap alongside training.

## Sister-repository boundary

See [INTEROPERABILITY.md](INTEROPERABILITY.md) for the diagnostic contract and
the conceptual mapping to sim2claw's operations layer. We share source identity,
case/time units and proof distinctions; robot contracts and execution authority
remain project-specific. No sim2claw implementation or control plane was copied.

See [PHYSICS_AND_OPERATIONS.md](PHYSICS_AND_OPERATIONS.md) for the history-driven
probe order and how to use these tools for a new behavior.

## Validate software only

```sh
python3 -m unittest discover -s tests -p test_experiment_ops.py -v
node --check experiment_ops/report.js
```

Node is needed only for the optional JavaScript syntax check. Neither command
requires a simulator or a training environment. This is separate from the
simulation, learned-behavior and physical acceptance gates.
