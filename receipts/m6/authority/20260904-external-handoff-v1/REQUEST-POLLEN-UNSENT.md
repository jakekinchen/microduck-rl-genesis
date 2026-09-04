# UNSENT request - Pollen Robotics official alpha walking artifact

Status: **draft only; not transmitted**

Subject: Immutable provenance inputs for `alpha_walking.onnx`

Hello Pollen Robotics maintainers,

We are validating the official `alpha_walking.onnx` file at immutable Hugging
Face revision `088524a64e2557dc453256b6071dbb9d23888802`, SHA-256
`e36332d383997d51401897734cd3e79cf5038406feddb18b4d57ecfb141daa6c`.
Could you publish or identify immutable, publicly retrievable evidence linking
that exact ONNX digest to the following?

1. Source checkpoint bytes, SHA-256, training-run identity, and immutable
   artifact/revision containing them.
2. Normalizer statistics/source, shape and observation ordering, SHA-256, and
   an immutable link to that checkpoint and ONNX.
3. Exact exporter source repository/revision/path/digest, invocation, runtime
   versions, input checkpoint digest, and output ONNX digest.
4. Exact root MJCF repository/revision/path/digest used for training/export.
5. Exact BAM implementation and parameter repository/revision/path/digests.
6. Exact task identifier plus repository/revision/path/digest for its config.
7. Immutable evaluator implementation repository/revision/path/digest.
8. Digest-bound raw evaluation receipts naming evaluator, policy, model, BAM,
   task, cases/seeds, and output evidence digests.
9. An immutable license file/revision/digest explicitly covering the policy,
   checkpoint, normalizer, exporter, model/task inputs, and published evidence.

A signed manifest or immutable repository/model revision containing these
records is ideal. Narrative claims, mutable latest links, screenshots, videos,
or aggregate metrics without digest-bound raw evidence cannot close the gate.

No action is requested from this draft until the project owner explicitly
authorizes third-party contact.
