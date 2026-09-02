# Independent evaluator core

This directory contains the CPU-only reference path that is independent of the
Genesis and mjlab training loops. `core.py` loads the frozen task, interface,
model, and BAM locks; validates a 61D-to-14D ONNX policy; steps official MuJoCo
at 5 ms; updates the policy target every four steps; and calls the pinned BAM
`MujocoController` at every physics step.

The current slice is deliberately infrastructure-only. Its retained fixture is
a deterministic zero-output ONNX policy held at HOME for 40 physics steps. Two
runs must produce the same report bytes and trajectory digest. That proves the
reset/inference/control/physics/report path is wired, but it is not a walking or
backflip success result.

Run the bounded smoke with a clean BAM checkout at the pinned commit:

```bash
BAM_REPO=/path/to/pinned/bam \
  .venv-apple/bin/python tests/test_evaluator_core.py
```

Or emit a report explicitly:

```bash
.venv-apple/bin/python evaluator/run.py \
  --policy tests/fixtures/evaluator/zero-policy.onnx \
  --bam-repo /path/to/pinned/bam \
  --output /tmp/evaluation-core-smoke.json
```

The report intentionally says `task_success: not_evaluated` and
`proof_class: infrastructure_only`. Later M2/M3 slices must add the complete
evidence bundle and frozen classifiers before any candidate can be promoted.
