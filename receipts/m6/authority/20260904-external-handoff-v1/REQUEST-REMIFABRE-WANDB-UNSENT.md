# UNSENT request - RemiFabre community rough-walk artifact

Status: **draft only; not transmitted**

Subject: Immutable provenance inputs for `microduck-rough-walk-e/policy.onnx`

Hello RemiFabre / W&B project owner,

We are validating `policy.onnx` at immutable Hugging Face revision
`fa7b27eeb5610d3b351362f4bd71691ee8be3d7d`, SHA-256
`5aa423bd693e431b19e2ead77f99cbae6184e40a529eb2f7c1b4f85bb7f57040`.
The model card/source name W&B run `yr25mna4` checkpoint `model_9999` and a
later hostile-environment finetune, but no public immutable checkpoint artifact
is currently bound to the ONNX. Could you publish or identify:

1. The exact source checkpoint bytes, SHA-256, W&B artifact version/commit, and
   training-run identity that produced this ONNX, including any resume chain.
2. Separately attributable normalizer statistics/source, observation ordering,
   digest, and immutable checkpoint/ONNX association, even if inference
   currently bakes Sub/Div tensors into the ONNX.
3. The exact artifact-specific exporter invocation, exporter source revision/
   path/digest, runtime versions, input checkpoint digest, and output digest.
4. The immutable evaluator implementation revision/path/digest used for the
   reported evaluation battery.
5. Digest-bound raw evaluation receipts naming policy/evaluator/model/BAM/task,
   cases/seeds, per-case outputs, and evidence-file digests.
6. An immutable license file/revision/digest explicitly covering the ONNX,
   checkpoint, normalizer/export record, evaluator, and evidence.

Public immutable W&B artifact versions and Hugging Face/Git commit hashes are
acceptable when every referenced file also has a SHA-256. Model-card prose,
preview media, mutable aliases, or aggregate metrics alone cannot close the
gate.

No action is requested from this draft until the project owner explicitly
authorizes third-party contact.
