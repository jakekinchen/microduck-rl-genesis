# V53 retention correction: completed, not promoted

V53 restores all 63 flat cases and exactly the original five passing surface sessions. Both 180-second compositions finish without falling, but one fails whole-session heading. Downhill recovery regresses from V52. The bounded experiment is complete; the candidate is rejected. Keep the original V21/V15 actors with V30 retained.

| Complete all-gate evaluation | V50 | V52 | V53 |
|---|---:|---:|---:|
| Original flat timing bank | 21/21 | 13/21 | **21/21** |
| Repeated flat windows | 42/42 | 25/42 | **42/42** |
| Downhill whole sessions | 0/2 | 0/2 | **0/2** |
| 180-second compositions | 2/2 | 0/2 | **1/2** |
| Whole surface sessions | 5/14 | 3/14 | **5/14** |
| Surface windows | 13/28 | 8/28 | **13/28** |

All 20 short windows within the two 180-second compositions pass. Start 1 nevertheless fails the separate full-session heading gate: maximum error **21.414506 degrees**, above **20**; its endpoint error is 5.760180 degrees. Start 2 passes, including maximum/endpoint heading errors 18.100903/10.175197 degrees. Neither composition resets or falls. Do not reduce the denominator to short-window success.

Downhill start 1 falls at **14.24 s**, with actual joint-margin, body-interference and sustained/continuous internal-load failures. The second window is unrun and remains failed. Start 2 survives both stops through 36 s, but its windows have mean absolute yaw errors .202257/.215905 rad/s versus .20, and final mean absolute face pitch 30.108382/31.392713 degrees versus 30. Its whole-session endpoint heading is 16.879942 degrees versus 15. V52 survived both starts with stop checks passing; that gain is not fully retained.

The five surface passes are exactly `rigid-control-start-1`, `rigid-control-start-2`, `soft-low-traction-start-1`, `soft-low-traction-start-2`, and `unseen-low-medium-start-1`. Historical `unseen-*` case names are now exposed development cases. No unfamiliar specimen or protected bank was evaluated.

## Verified data collection and one training run

The frozen collection selected nominal forward-08, nominal forward-12 and zero-lag arc-left, each at controls 655, 670 and 690. All **2,223 original V52 controls** reproduce original float32 actions/observations, qpos/qvel and braking age/active state. Full physics/BAM, sensor/motor histories, command-ramp, heading and braking-event states are retained.

For all nine states, the original V50/V15 actors recover and pass every complete 18-second flat gate. Each original-actor and unchanged V52 branch repeats exactly, including physics-rate load telemetry: **5,358 repeated continuation controls** total. No reset occurs inside a continuation. The unchanged branches retain their original failures; the collector does not assign zero labels to arbitrary unvalidated states.

The dataset contains **13,055 rows**: 11,625 prior successful-stop zero labels, **930 new verified recovery rows**, and **500 actual V52 downhill braking examples** from the four previously successful stop events. Those four source windows retain their yaw failures. The mixed V51 time-knot examples are replaced rather than relabeled. Every replay observation and target reconstructs byte-for-byte from its bound source.

One seed-26090853 supervised run completed all **8,000 updates**, using 3,072,000 sample presentations. It starts from V52 FINAL and keeps its 61-64-64-14 architecture, normalization tensors, 125-control event router, V50/V15 base weights, V30 controller and complete-contact-v11 physics fixed. The changed loss penalizes average and worst-joint zero-label errors, with 128 positive, 128 random zero and 128 hard zero examples per update; hard pools refresh every 50 updates. All 160 pools and 8,000 finite losses are retained. There are zero new PPO/RL transitions. FINAL only; no extension, clipping, terrain switch, policy activation, paid compute or hardware operation.

On the identical original 11,625 zero-label inputs, RMSE decreases from .008877 to **.002735 rad**, the worst action error from .209567 to **.028361 rad**, and the 95th percentile of per-row maximum errors from .040455 to **.011027 rad**. The focused nominal first braking correction shrinks from .019819 to **.009238 rad**; its formerly failed rollout now passes all gates through 18 s. Fitting improves, but it is not exact zero preservation.

## Why the next task is joint fitting feasibility

V53 still has **.015697-rad RMSE** and **.206272-rad maximum error** against the downhill demonstrations. More revealingly, the four first braking actions have maximum errors **.141180, .077870, .206272 and .133775 rad** on their exact training inputs. A small average fitting error therefore hides large corrections at the transition onset.

The positive and weighted zero-label losses have locally opposing gradient directions (cosine -.242560 at FINAL; norms 6.47152 and 51.61537). This is a local optimization diagnostic, not proof that the 61D input is ambiguous, that the network lacks capacity, or that any particular optimizer will solve the robot. Physics was unchanged, and these same-input errors precede any closed-loop distribution shift.

**Next best step:** freeze an offline joint-fit feasibility experiment with independent maximum-error gates for successful-stop retention and downhill recovery, explicitly covering every stop onset. Do not trade one group away through an aggregate mean loss. Require both fitting gates before another full rollout battery. If a bounded fit cannot meet them, inspect conflicting labels/representation and test one preregistered capacity change; do not assume missing observability. A passing fit still requires all 63 flat, both full endurance, five surface retention, successive downhill-stop, posture, contact, load and yaw gates. Keep the .20 yaw and 20-degree whole-session heading limits unchanged.

## Verification and retained evidence

All **94,660 evaluated actions** exactly match the frozen base ONNX plus the new ONNX correction, with zero action discrepancy. All **36,952 available first-window prefix controls** through braking onset exactly match V50 action/observation bytes and qpos/qvel. **378,640 physics-rate load samples** are present. Event ages and activation windows verify on every recorded row; failures and missing windows remain failures. All replay labels, model/run hashes, normalizers, source freezes and receipt manifests verify.

Maximum recorded Torch/ONNX export error across the training set and 1,000 random inputs is **2.384186e-6 rad**, below 1e-4. All **140 workspace tests** and **two focused V53 tests** pass. Tests cover process recognition, receipt handling, the changed loss and event lifetime; they do not establish physical behavior. No thresholds or historical scores changed. Fresh/protected banks remain closed; measurement-based calibration, general terrain acceptance and carpet transfer remain unmet.

Artifacts:

- Frozen protocol: `experiments/walking/BRAKING-RETENTION-v53.md`.
- Collection: `receipts/walking/20260908-v53-retention-collection/`.
- Dataset: `experiments/walking/braking-replay-v53/`.
- Run: `logs/braking-retention-20260908-v53/`.
- Evaluations: `receipts/walking/20260908-v53-braking-{flat,repeated,endurance,surfaces}/`.
- Audit, fitting diagnostic, figure and recorded-pose video: `outputs/walking-braking-v53/`.
- Activity closure and source-bound references: `receipts/walking/20260908-v53-activity-closure/`.

V53 braking ONNX: `d0c2e4accc07364cd588a93713ef7f65acc92f7bf39283fb2889b058e45d98fa`.
V53 checkpoint: `0244483f11156d76f0f08f5cd2ced021e8e227978c707fdda9d1ee6388d8150c`.
Training freeze: `7f9f9b9cba64fa9bcd31798d0a99eead6e908b1e9262466334fcf56781166291`.
The V50 base walker ONNX remains `1f8e87d7370a1aeb7b57f272c96abb6df49e3039b8d1332bfce24c1a81de5b4f`; the additional V53 braking digest is required to identify the composite controller. The active packet uses a passing V53 flat reference only. The video shows the actual rejected downhill start-1 receipt; it re-renders recorded poses without integrating physics or repairing motion.

## Every failed window and session

Window times are relative to each 18-second scoring interval. Complete-session failures are listed independently.

### flat

| Case | First fall (s) | Failures |
|---|---:|---|
| All cases pass | — | None |

### repeated

| Case | First fall (s) | Failures |
|---|---:|---|
| All cases pass | — | None |

### endurance

| Case | First fall (s) | Failures |
|---|---:|---|
| `downhill-3deg-start-1--window-1` | 14.24 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_contact:self_penetration_over_1mm; self_load:incomplete_duration; self_load:sustained_self_load_occupancy; self_load:continuous_body_bracing; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `downhill-3deg-start-2--window-1` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s; endurance:final_standing_mean_absolute_face_pitch_deg |
| `downhill-3deg-start-2--window-2` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s; endurance:final_standing_mean_absolute_face_pitch_deg |
| `downhill-3deg-start-1--window-2` | — | not_run_after_terminal_fall |

| Session | Duration (s) | Failures |
|---|---:|---|
| `downhill-3deg-start-1` | 14.24 | session_heading_failure; window_failure; incomplete_duration; sustained_self_load_occupancy; continuous_body_bracing |
| `downhill-3deg-start-2` | 36.00 | session_heading_failure; window_failure |
| `continuous-composition-start-1` | 180.00 | session_heading_failure |

### surfaces

| Case | First fall (s) | Failures |
|---|---:|---|
| `soft-middle-start-1--window-1` | 8.76 | fall; incomplete_duration; missing_tracking_or_stop_evidence; persistent_loaded_foot_slip; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-middle-start-2--window-1` | 1.84 | fall; incomplete_duration; insufficient_active_evidence; missing_bilateral_steps; missing_tracking_or_stop_evidence; no_useful_translation; unsustained_bilateral_stepping; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-high-traction-start-1--window-1` | 0.22 | missing_or_invalid_case_evidence:no posture evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-high-traction-start-2--window-1` | 0.22 | missing_or_invalid_case_evidence:no posture evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-low-medium-start-2--window-2` | — | persistent_loaded_foot_slip |
| `unseen-high-mild-start-2--window-1` | 13.92 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_contact:self_penetration_over_1mm; self_load:incomplete_duration; self_load:continuous_body_bracing; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-low-soft-start-1--window-1` | — | persistent_loaded_foot_slip |
| `unseen-low-soft-start-1--window-2` | — | persistent_loaded_foot_slip |
| `unseen-low-soft-start-2--window-1` | — | persistent_loaded_foot_slip |
| `unseen-low-soft-start-2--window-2` | — | mean_abs_yaw_error_rad_s; persistent_loaded_foot_slip; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s |
| `soft-middle-start-1--window-2` | — | not_run_after_terminal_fall |
| `soft-middle-start-2--window-2` | — | not_run_after_terminal_fall |
| `soft-high-traction-start-1--window-2` | — | not_run_after_terminal_fall |
| `soft-high-traction-start-2--window-2` | — | not_run_after_terminal_fall |
| `unseen-high-mild-start-2--window-2` | — | not_run_after_terminal_fall |

| Session | Duration (s) | Failures |
|---|---:|---|
| `soft-middle-start-1` | 8.76 | session_heading_failure; window_failure; incomplete_duration |
| `soft-middle-start-2` | 1.84 | session_heading_failure; window_failure; incomplete_duration |
| `soft-high-traction-start-1` | 0.22 | session_heading_failure; window_failure; incomplete_duration |
| `soft-high-traction-start-2` | 0.22 | session_heading_failure; window_failure; incomplete_duration |
| `unseen-low-medium-start-2` | 36.00 | window_failure |
| `unseen-high-mild-start-1` | 36.00 | session_heading_failure |
| `unseen-high-mild-start-2` | 13.92 | session_heading_failure; window_failure; incomplete_duration; continuous_body_bracing |
| `unseen-low-soft-start-1` | 36.00 | window_failure |
| `unseen-low-soft-start-2` | 36.00 | window_failure |

