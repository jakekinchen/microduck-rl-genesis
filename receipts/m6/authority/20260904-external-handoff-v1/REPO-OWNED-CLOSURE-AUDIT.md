# Repo-owned M6 closure audit

Result: **no honest repo-owned artifact closes a remaining official or
community manifest role without changing origin category or claim boundary.**

- `artifact_contract/fixtures/{official,community}` contains explicit synthetic
  marker fixtures. They prove schema/validator behavior only and cannot become
  real official or community provenance.
- `evaluator/` is a repo-owned development evaluator. It is not the evaluator
  used to produce either upstream candidate's claims, and no authorized run of
  either candidate produced digest-bound raw evidence with it.
- `export_onnx.py` is repo-owned current tooling, not the historical exporter
  invocation that produced either candidate digest.
- Apple-baseline `model_0.pt`/`model_4.pt` files are five-iteration local smoke
  checkpoints with different lineage and task scope. They are not source
  checkpoints for either candidate.
- The accepted 65-file bundle provides locally attributable model assets and a
  BAM parameter file. It does not prove that the official policy used those
  exact inputs; only an immutable upstream binding can close those roles. The
  community candidate's model/BAM/task/exporter roles are already bound.
- Extracting tensors from a baked-normalizer ONNX would require policy parsing,
  would not recover checkpoint-statistics provenance, and is not authorized.
- Running a candidate locally would create new repo-owned evaluation evidence,
  not the missing upstream raw evidence, and policy execution is not authorized.

Therefore the next honest M6 progress requires immutable upstream inputs and/or
explicit human authority for contact or public release. Further local searching
or relabeling would not close a role.
