# CI setup correction — September 16, 2026

The first candidate workflow (run 35137800692, head 6367f1e) completed 42 tests:
41 passed and one errored during import, with no skips. In particular, the real
retained detector/follower interface test passed. The PPO update-equivalence
test could not reach its assertions because importing the `microduck` package
runs its unchanged initializer, which eagerly imports Genesis.

A second setup defect was found in the package log: installing unconstrained
RSL dependencies selected a newer torchvision and replaced CPU PyTorch 2.9.1
with CUDA PyTorch 2.14.0. The first workflow therefore was not a validation of
the intended Torch version. Its failure/logs remain preserved.

This correction modifies only the new test and CI setup, not runtime/learning
implementations or frozen historical code:

- Install the official CPU Torch 2.9.1 / torchvision 0.24.1 pair; constrain both
  exact CPU distributions during subsequent resolution. Run `pip check` and
  assert both versions and `torch.version.cuda is None` before testing.
- Load the actual PPO recipe child modules through an isolated package path,
  bypassing only the simulator-importing initializer for this synthetic update
  test. Restore previously loaded module identities afterwards. Neither PPO
  implementation, RSL dependency, nor tested actor update is replaced or mocked.
  Native package-entrypoint integration is still untested by this check.

The original local-validation.json is a historical record for the initial
source snapshot; its test_ppo.py blob is not the corrected test. All candidate
implementation files remain unchanged. The corrected workflow needs a separate
result; this note does not predeclare success.

Version pairing reference: https://pytorch.org/get-started/previous-versions/#v291
Existing workspace-tools and contract-drift workflows passed on the first head.
Native experiments, full Rust transport, training and physical acceptance remain
pending regardless of portable CI results.
