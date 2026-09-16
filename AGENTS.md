# Repository agent instructions

Work directly in the current Codex task as a single agent.

- Do not create Executor, Reviewer, Planner, Manager, Guardian, or critic cycles.
- Do not spawn, fork, delegate to, or message other Codex tasks unless the user
  explicitly asks for multi-agent work in their current request.
- Do not recreate or run an autonomous goal loop, pair-cycle runner, stop
  sentinel, or role-based workflow.
- Use `TRAINING_ACTUALIZATION.md` as the ordered task list and `GOAL.md` as
  the concise current-status record.
- Implement, test, review, and report work in the same task. Ordinary code
  review does not require a separate agent or role.
- Treat `docs/briefs/`, `docs/session-logs/`,
  `docs/reviewer-messages/`, and `docs/manager-log/` as historical evidence.
  Do not append new role-cycle records there.
- Preserve receipts and evidence boundaries. A plausible rollout, partial
  artifact, or local checkpoint is not task success or physical authority.
- Do not start paid compute, publish artifacts, contact third parties, activate
  a policy, or operate hardware without the required user authority.

## Physical behavior acceptance

- Every behavior and composition must satisfy
  `docs/workspace/BEHAVIOR_VALIDATION.md` before the corresponding library
  capability claim: reward-independent tests, effective domain randomization,
  unseen-environment evaluation, continuous-state transitions and evidence-bound
  physics validation. This includes deterministic controllers and perception.
- Define the operating envelope and preregister per-bucket thresholds, repeats,
  splits and decision rules. Missing/failed cases are not passes; randomization
  configuration alone is not coverage. Test actual parameter application and
  non-accumulating resets. Preserve exposed and protected final banks separately.
- Cross-engine agreement does not establish calibrated physical accuracy.
  Missing measurement-based calibration remains an explicit claim blocker;
  continue scoped local development without asserting generalization or transfer.
- For locomotion, target/velocity success is necessary but not sufficient:
  independently inspect sustained bilateral stepping, loaded contact slip,
  actual joint-stop occupancy, falls and non-foot support. Missing telemetry
  is unknown, not a pass. Keep calibrated physical acceptance separate.
- Audit body-to-body collision coverage as well as floor contact. Visual meshes
  and a "full" model name do not prove active contact pairs: verify mesh
  identities, masks and engine filters. Reject recorded body interference;
  floor clearance cannot substitute for this check. Preserve original scores
  and label changed-model/controller results separately.
- Reject sustained internal body loading as well as penetration. A policy can
  brace its legs against the battery while keeping overlap below a geometric
  tolerance. Read actual applied contact loads at physics rate without changing
  dynamics; missing or partial stop evidence cannot pass. Do not equate force
  sums across different engines' contact-manifold representations.
- Check visual/camera frames against physical feature geometry and CAD sites.
  A named camera can point inward; do not reverse a task from its optical axis
  alone. The laser diagnosis and rejected v3 attempt are documented in
  `experiments/laser/GAIT_DIAGNOSIS.md`.
- Freeze the composite evaluator before inspecting a candidate. Preserve
  historical target-only scores, but do not present them as walking quality.
  No new reviewer/executor cycles are required for these checks.
- Evaluator exit code zero means the evaluation completed, not that the
  behavior passed. Read every required component/case result and its failures;
  a successful export, manifest check or test process cannot replace that.

## Workspace entry points

- Use `./scripts/duck status` for a small current-state projection and
  `./scripts/duck doctor` when checking local runtime/evaluator readiness.
- Use `./scripts/duck verify` after workspace tooling changes. It runs the
  same fast suite as workspace CI without starting a simulator; see
  `docs/workspace/VERIFICATION.md` for worktree use and proof boundaries.
- Use `./scripts/duck studio` to compare retained development videos and
  trajectories. It reads receipts; it cannot start training or operate hardware.
- For a new behavior, consult `.agents/skills/microduck-experiments/SKILL.md`
  and `docs/workspace/BEHAVIOR_WORKFLOW.md`. Reuse an existing experiment when
  appropriate; `duck new` creates only a draft, not an executable training task.
- Consult `docs/workspace/RETROSPECTIVE.md` for history lessons instead of
  loading every historical role log. Keep private history extracts and local
  dependency checkouts under ignored `.workspace/`.
- For current laser work, run `./scripts/duck prepare` and follow
  `docs/workspace/ACTIVE_EXPERIMENT.md` before another intervention. Inspect
  the first failure, test one active property group at a time, freeze a fresh
  test bank, and rerun the advisory `./scripts/duck-ops guard` before launch.

## Local compute and macOS Dock behavior

- Treat training and the full simulation suite as competing compute jobs.
  `./scripts/duck-ops guard` recognizes both, including known standalone
  simulator tests. Recheck immediately before launch and honor its exit code:
  use `./scripts/duck-ops guard && <training command>`, or an equivalent
  conditional. Do not run guard and launch as independent tool calls or ignore
  a nonzero result. It is an advisory snapshot, not a reservation or lock.
- `tests/run_all.py` now refuses launch when another recognized compute job is
  present or process inspection fails. Use `./scripts/duck verify` for tooling
  changes; do not start a full simulation regression during active training.
- Two Python Dock entries can be a trainer and a simulation test, not two
  agents. Genesis imports hidden Tk/Pyglet GUI infrastructure on macOS even
  with `show_viewer=False`; shadow-window settings alone do not suppress it.
  Do not patch global Python, AppKit or rendering backends just to hide icons.
  See `docs/workspace/MACOS_COMPUTE.md` for the verified diagnosis and limits.
