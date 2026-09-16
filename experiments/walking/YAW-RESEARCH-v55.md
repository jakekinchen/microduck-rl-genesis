# Research checked during the V55 comparison

September 12, 2026. Read-only research for the post-result decision. None of
these methods changes the already frozen V55 protocol or its acceptance gates.

The [pinned official MicroDuck velocity configuration](https://github.com/pollen-robotics/microduck_rl/blob/2b581c641406a48346e696212930ea881c222c52/src/mjlab_microduck/tasks/microduck_velocity_env_cfg.py)
uses staged standing allocation and gives its critic simulated base velocity.
Those are useful platform-specific comparisons, but V55 retains the existing
curriculum and 61D critic to isolate one yaw-objective change. Its model and
actuator differences remain documented in `UPSTREAM-RECIPE-AUDIT-v54.md`.

[Rudin et al., Learning to Walk in Minutes](https://proceedings.mlr.press/v164/rudin22a.html)
demonstrate curriculum-based training and hardware validation on ANYmal.
This supports measuring staged terrain learning; it does not predict a
MicroDuck success rate, training budget or calibrated carpet response.

[CAPS, Mysore et al., ICRA 2021](https://ai.bu.edu/caps/), regularizes differences
between policy outputs at successive and neighboring states. Its demonstrated
physical example is a quadrotor. This suggests an action-spectrum and local
sensitivity diagnostic if oscillation persists. A roughly 3.27-Hz **body yaw**
peak does not establish high-frequency **action** jitter: periodic stepping
itself is expected. An action-regularization ablation would need a separately
frozen test and retention gates. No deployment filter is justified by this paper.

The current [official TorchRL MicroDuck tutorial](https://docs.pytorch.org/rl/main/tutorials/microduck.html)
describes task-indexed recurrent PPO, per-task advantage standardization and
a separately identified closed-form gait demonstration. It explains how
pooled normalization can change the relative learning signal of mixed tasks.
This suggests recording actual per-mode/per-terrain advantages before selecting
an optimization change. Reward variance alone cannot prove such an imbalance.
The tutorial's controller/observation/actuator compatibility and behavior under
our complete-contact gates have not been verified. It is not a drop-in policy,
a reproduced benchmark, or evidence that recurrence is required here.

Decide the next experiment from the complete V55 outcomes. Priority remains
whole-session walking and stopping, retained flat/surface/composition results,
verified long-episode exposure and replication. Physical calibration and
unseen-terrain acceptance stay separate. Keep exposed heading-interpolation
failures even if the familiar two starts look stable.
