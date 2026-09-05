# Shared arm and duck workcell direction

Owner request, 2026-09-05: grow Sim2Claw and MicroDuck together toward a shared
simulated environment and eventually arm-assisted duck battery replacement.
The owner chose the existing battery hardware; a redesigned battery mount is
not the target. This is a future integration lane, not a replacement for the
active MicroDuck training queue.

The adjacent `arm_duck_workcell.v1.json` is an exact mirror of
`configs/operations/arm_duck_workcell.v1.json` in Sim2Claw. Accepted SHA-256:
`0ec9b9e0bee51bd78680d132ba65b8cd1edc113cd21fa0d82c28a1f5865f9a31`.
It binds ten direct native sources and proposes separate action buffers on a
200 Hz physics clock: six absolute-radian arm values at 20 Hz and fourteen
home-relative duck values at 50 Hz. No values are created or dispatched by the
inspection tools. Full transitive MJCF/mesh closure remains a later gate.

## Inspect without starting a simulator

```sh
.venv-apple/bin/python docs/workspace/coordination/check_plan.py
.venv-apple/bin/python docs/workspace/coordination/check_plan.py --sim2claw-root /path/to/sim2claw
```

The local checker only verifies the accepted plan bytes and an optional exact
peer mirror. Run the substantive native source/declaration check from
Sim2Claw's separate runtime:

```sh
uv run --locked sim2claw ops workcell --peer-root /path/to/microduck-rl-genesis
```

That command belongs in the Sim2Claw checkout. It does not import that package
into the MicroDuck runtime or execute capability strings from an envelope.
Without an explicit peer root its MicroDuck source checks remain unchecked.

## Ownership and ordered gates

Sim2Claw owns the shared recipe and the arm/manipulation/workcell adapter.
MicroDuck owns its model variants, home pose, observations, gait/docking/posture
training and native evaluator. Keep `TRAINING_ACTUALIZATION.md` as this repo's
ordered queue and retain its current single-task work mode.

The stages are source-bound declarations; static assembly of one arm, one duck
and a fixture; separate controller/contact checks; measured existing battery
mechanics; a frozen service evaluator; bounded local skill training; independent
cooperative validation. The declaration gate does not close the seven later
simulation/mechanical/training gates. The full responsibility map and exact
acceptance criteria live in Sim2Claw `docs/operations/SHARED_WORKCELL.md`.

The native `np_f970` battery geometry is currently rigid inside the trunk.
Before modeling removal, measure the actual part/mount/latch/connector and
reconcile aggregate trunk inertia. Collision pairs must be tested per backend;
MuJoCo masks cannot silently define Genesis cross-entity contacts. A five-axis
arm plus gripper needs explicit grasp/orientation and extraction feasibility.
Metadata validity or geometric insertion does not establish mechanical,
electrical, battery-service or physical success.

## Compute and Git policy

Use local Mac compute first: the existing pinned Genesis/Metal and PyTorch/MPS
lane is the first GPU candidate, with an independently owned CPU MuJoCo
reference evaluator. Isolate the shared world from active VelocityEnv/training
construction and benchmark scene/batch size before selecting a backend.
NVIDIA/Brev is a last-resort inference/validation lane for an explicitly named
local gap, with exact inputs, cases, time/cost bounds, receipt and stop/delete
condition. This document starts no compute job and grants no hardware authority.

Keep the repositories and runtime locks separate. Commit reviewed source,
contracts and native evidence through scoped paths. Existing receipt snapshots
and source hashes retain their current locations; do not relocate them just
because equivalent blobs appear more than once. Git already deduplicates exact
blobs. Ignored `.workspace/` contains local dependency/private-history state,
while tracked or staged receipts remain evidence.

Before future data-heavy commits, Sim2Claw's read-only operations CLI can inspect
this repo via `ops --root /path/to/microduck-rl-genesis git-health`. Its optional
`--check` is a prospective staging-review signal, not a deletion instruction or
an acceptance verdict. The training owner's active index must remain intact.

Both owners must review changes to this shared plan and update the accepted
mirror digest/checks together. Native workspace-exchange v1 has its own frozen
schema/fixture digests and bilateral conformance gate; this plan does not change
that contract. No simulator, artifact or native implementation is copied here.
