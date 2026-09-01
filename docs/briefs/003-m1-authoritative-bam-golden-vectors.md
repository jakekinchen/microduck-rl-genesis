# Slice Brief 003 - M1 authoritative BAM golden vectors

**Date:** 2026-09-01

## Objective

Pin the exact BAM implementation used by the official Microduck RL stack and
generate deterministic open-loop plus reset/internal-state fixtures that both
the Genesis port and later official mjlab adapter can consume without importing
the authority at runtime.

## Authority Boundary

- `/Users/kelly/Developer/microduck-rl/uv.lock` records Rhoban/BAM commit
  `62bd8ce12154340be97e06f7f41a0ca8f116d967` for the official stack.
- The live `mjlab_frictionloss` branch currently resolves to
  `57d13ead53206a6bf0db3d66f86506ae8c2ce01a`.
- Retrieve and verify the locked commit. Do not use the moving branch head as a
  silent replacement. If the locked commit is unavailable, record a
  `missing_input` blocker instead of inventing vectors.
- The existing repo-local BAM parameter JSON remains byte-bound by its current
  lock; report any mismatch with the authority before generating fixtures.

## Acceptance Criteria

- Record repository URL, exact commit, branch context, source-file digests, BAM
  parameter digest, license, generation command, schema, dtype, and tolerances.
- Define deterministic edge and seeded cases covering firmware control voltage,
  current/back-EMF torque, friction terms, clipping/saturation, zero velocity,
  sign changes, reset state, and any state carried between calls.
- Generate expected values by executing the pinned authoritative BAM code, not
  by calling the Genesis port.
- Add a pure-data fixture under
  `microduck_contract/actuator/fixtures/` and bind it from
  `bam-m6-xl330-v1.lock.json` through `scripts/freeze_contract.py`.
- Add deterministic tests that feed the same inputs through the Genesis BAM
  implementation and compare every declared output/state field within a
  preregistered tolerance.
- Run the existing 2,000-case formula comparison and the short
  MuJoCo+BAM-versus-Genesis loop against the exact pinned checkout; record the
  current documented mjlab quadratic-gate divergence separately.
- Do not claim official mjlab cross-backend conformance yet. This slice creates
  the shared authority fixture and validates Genesis consumption only.

## Expected Files

- `microduck_contract/actuator/fixtures/bam-m6-xl330-v1-open-loop.json`
- `microduck_contract/actuator/bam-m6-xl330-v1.lock.json`
- `scripts/freeze_contract.py`
- a focused fixture-generation script under `scripts/`
- focused deterministic tests under `tests/`
- `docs/session-logs/003-executor-m1-authoritative-bam-golden-vectors.md`

## Validation

```bash
.venv-apple/bin/python scripts/freeze_contract.py --check
BAM_REPO=<pinned-checkout> .venv-apple/bin/python tests/test_bam_formulas.py
BAM_REPO=<pinned-checkout> GS_ENABLE_ZEROCOPY=1 \
  .venv-apple/bin/python tests/test_bam_vs_mujoco.py
.venv-apple/bin/python <focused-golden-vector-test>
GS_ENABLE_ZEROCOPY=1 .venv-apple/bin/python tests/run_all.py
```

## Evidence Boundary

Matching authoritative vectors validates the declared BAM functions and state
cases only. It does not prove full official-mjlab adapter parity, complete model
conformance, task success, transfer, or physical authority.

## Out Of Scope

- Altering the 61D observation, 14D action order, 50 Hz loop, action filter, or
  model variants.
- Updating to moving BAM branch head without a versioned divergence decision.
- Official mjlab adapter changes beyond reading the shared fixture.
- Training, Brev, publication, policy activation, or physical testing.

## Stop Conditions

- The locked BAM commit or its license/source provenance cannot be retrieved.
- The authority and official Microduck lock disagree about the behavior used.
- Fixture generation requires changing BAM or Genesis semantics rather than
  exposing a documented divergence.
