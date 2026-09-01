# Microduck contract snapshots

This directory freezes the backend-independent facts currently encoded by this
repository: the 61D observation, 14D action order, 50 Hz loop, model/asset
bundle, and BAM profile inputs.

These files are **candidate repo-local contracts**, not unilateral upstream
authority. They become cross-backend evidence only after the official mjlab
adapter and the independent C MuJoCo evaluator pass the same fixtures.

Generate or verify them with:

```bash
python scripts/freeze_contract.py
python scripts/freeze_contract.py --check
```

Do not hand-edit generated lock files. The missing `golden_vectors` and pending
cross-backend BAM status are intentional blockers tracked in
[`../TRAINING_ACTUALIZATION.md`](../TRAINING_ACTUALIZATION.md).
