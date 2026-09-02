# Slice Brief 013 - M2 official walking policy authority

**Date:** 2026-09-02

## Objective

Resolve the exact designated official-mjlab walking ONNX required for M2
repeatability proof. Establish policy, checkpoint, exporter, observation
normalizer, source commit, task, and license provenance before the evaluator
opens or executes the artifact.

## Acceptance Criteria

- Search the pinned official checkout, its git object tree, existing local
  receipts/artifacts, and public project-owned distribution surfaces for a
  61D-to-14D normalized walking ONNX.
- Record candidate paths/digests and reject Genesis-trained, unnormalized,
  unrelated-task, unlicensed, mutable-latest-only, or provenance-incomplete
  artifacts.
- If one authoritative artifact is available, validate it without repository
  code execution, bind its provenance, and run only the visible development
  suite twice. Keep task success `not_evaluated`.
- If none exists, emit a durable terminal `official_policy_authority_missing`
  result naming the exact missing inputs and acceptable resolution paths. Do
  not use stored credentials, private W&B/Hugging Face state, train a
  substitute, or relabel a Genesis policy.
- Add an Executor log, scoped commit, and separate Reviewer decision; keep M2
  open unless the exact authority and repeatability gate both close.

## Validation

```bash
git -C <official-checkout> ls-tree -r --name-only <pinned-commit>
<artifact-inspector> --no-execute <candidate.onnx>
BAM_REPO=<clean-pinned-bam> .venv-apple/bin/python <focused-authority-test>
scripts/check_branch_hygiene.sh origin/main
git diff --check
```

## Evidence Boundary

Finding or validating an official policy artifact is provenance and evaluator
plumbing evidence only. It does not establish task success, backend superiority,
transfer, or physical authority.

## Stop Conditions

- The artifact requires credentials, private storage access, payment, or
  untrusted repository code execution.
- No exact normalized official walking policy with sufficient provenance is
  available after bounded local and public checks.
- The next action would inspect a final Genesis candidate, publish, push, train,
  activate a policy, or operate hardware.
