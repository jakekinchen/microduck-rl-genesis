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
