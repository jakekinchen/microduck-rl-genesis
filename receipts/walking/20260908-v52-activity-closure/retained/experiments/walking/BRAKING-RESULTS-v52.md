# V51 recovery revalidation and V52 braking correction: complete, rejected

V52 survives both successive downhill stops in each 36-second session. It still fails downhill absolute yaw and regresses previously successful flat, endurance and surface cases. The bounded activity is complete; the behavior is not accepted. Keep the original V21/V15 actors with V30 controller retained. V50 and V52 remain development candidates only.

## Measured acceptance

| Exposed evaluation | V50 | V52 | Decision |
|---|---:|---:|---|
| Flat timing bank | 21/21 | 13/21 | Eight regressions |
| Repeated flat windows | 42/42 | 25/42 | Seventeen regressions, including unrun windows |
| Downhill whole sessions | 0/2 | 0/2 | Stops now survive; yaw still fails |
| Continuous 180-second compositions | 2/2 | 0/2 | Falls at 15.10 and 158.58 seconds |
| Whole surface sessions | 5/14 | 3/14 | Two original passes lost |
| Surface windows | 13/28 | 8/28 | Five fewer complete passes |

Both downhill sessions finish 36 seconds with no resets. All four downhill windows fail only the absolute-yaw gate and its tracking-bucket counterpart: first/second windows are .202639/.205836 rad/s for start 1 and .202257/.207138 for start 2, against .20. Stopping, final head posture, gait, contact geometry, internal loading and the other required checks pass in those four windows; whole-session heading also passes. This is measured exposed stopping improvement, not full walking acceptance.

Surface passes retained: `rigid-control-start-2`, `soft-low-traction-start-2`, `unseen-low-medium-start-1`. Lost passes: `rigid-control-start-1` (fall at 15.76 s) and `soft-low-traction-start-1` (second-window fall, session time 32.38 s). Historical `unseen-*` names refer to already exposed development cases, not a fresh validation bank. Four surface failures occur before any braking intervention and exactly match V50 prefixes.

## V51 prerequisites and V52 training

V51 revalidated three V49 first-stop witnesses on V50 incoming physical states. Two witnesses were reusable with original V15 steady standing; one state required the preregistered 384-candidate retargeting search. All three first-stop demonstrations became eligible. Eligibility excludes only the already-failed pre-stop yaw checks; it is not whole-session acceptance. The retargeted branch still fell at the second stop (31.84 s).

V51 verified 1,391 original source controls, 150 reset controls, 9,698 exactly repeated comparison controls and all 83,053 search controls. All twelve comparison branches and selected search branches preserve full physical state and physics-rate internal-load evidence. No original evaluator or historical score was edited.

V52 performed one supervised demonstration-distillation run, not PPO: 2,000 Adam updates, 512,000 sample draws, seed 26090852, FINAL only, zero new RL transitions. Training used 375 demonstrated recovery rows plus 11,625 zero-residual retention rows from previously passing stops. The 61D normalized residual actor adds 14D raw servo deltas for 125 controls (2.5 seconds) after requested movement becomes zero; movement cancels the correction. V50 walking and V15 steady-standing weights remain fixed. The late 13.14-second demonstration differs from the evaluated 13-second trigger; the frozen protocol declares this distribution difference. No action clipping, physics change or policy activation occurred.

Final training RMSE: .006832 rad on demonstrations and .008877 rad on retention rows. Maximum ONNX/Torch export error across all training inputs and 1,000 random inputs: 1.430512e-6 rad. Low demonstration error did not preserve closed-loop behavior.

## First regression and next best step

The focused flat case is `nominal-20-20ms--forward-08`. Its first 650 controls (through 13.00 s) match V50 action and observation float32 bytes and qpos/qvel float64 bytes. At 13.02 s, the braking observation exactly matches a zero-residual training example, yet the model adds a maximum .019819-rad correction. This is already a retention-fitting error, before any unseen-state extrapolation. The correction reaches .431395 rad at 13.80 s and 1.102263 rad at the 14.42-second fall. The nearest normalized replay distance grows from zero to 67.146. These are measured facts; they support compounding closed-loop error, not a proven unique causal mechanism.

Next freeze a retention-constrained braking experiment: first inspect and reduce the worst zero-label errors on the exact successful-stop states, then collect verified corrective targets on states visited by the learned braker as it begins to diverge. A zero residual is a justified label on retained successful trajectories, not automatically on newly visited off-trajectory states; revalidate recovery there. Keep successful downhill demonstrations, original V15 steady standing, the unchanged .20 yaw gate, and all 63 flat, both endurance and five original surface retention gates. Preregister the changed loss/data rule and one bounded final-only run. Do not extend V52, select an intermediate checkpoint, add terrain-specific switches, or open fresh/protected banks. Close the remaining walking yaw margin separately after stopping retention holds.

This next-data strategy is motivated by the primary DAgger paper, which addresses imitation-learning distribution changes caused by the learner’s own actions: [Ross, Gordon and Bagnell, 2011](https://proceedings.mlr.press/v15/ross11a.html). Its theory motivates the experiment; it does not certify this robot or guarantee recovery from every visited state.

## Verification and provenance

Offline verification reconstructs all 12,000 replay rows and positive residual labels byte-for-byte, checks all 2,000 finite losses and normalized model tensors, verifies frozen source and retained manifests, and rechecks every evaluated action against the retained V50/V15 ONNX plus the V52 correction. All 73,242 evaluated controls match exactly (zero action discrepancy); 292,968 physics-rate load samples are present. All 36,952 available first-window prefix controls match V50 actions, observations, qpos and qvel exactly. Controller activation age and the 125-control bound verify on every row. Missing windows remain failures.

Workspace tooling: 140 tests pass. Four focused V51/V52 tests pass. These validate tooling and event routing, not physical behavior. All original motor, posture, gait, geometric interference, internal-load, endurance and heading gates remain unchanged. No fresh/protected bank, measurement-based physical calibration, carpet transfer or general terrain acceptance is claimed.

Artifacts:
- Frozen plans: `experiments/walking/BRAKING-FEASIBILITY-v51.md`, `experiments/walking/BRAKING-DISTILLATION-v52.md`.
- V51 receipts: `receipts/walking/20260908-v51-recovery-{capture,comparisons,search}`.
- V52 run: `logs/braking-distill-20260908-v52`.
- V52 evaluations: `receipts/walking/20260908-v52-braking-{flat,repeated,endurance,surfaces}`.
- Full case failures, manifests, audit source and figure: `outputs/walking-braking-v52/`.
- Recorded-pose downhill video: `outputs/walking-braking-v52/downhill-start-1.mp4`. The full-session FAIL label includes the remaining yaw failure; this visualization adds no new simulation or repaired motion.
- Final closure: `receipts/walking/20260908-v52-activity-closure/`.

Braking ONNX SHA-256: `2dea5e82c66690ea06d2cf3b56a76968f360de567d3cb6c1ed0491ace389421b`.
Braking checkpoint SHA-256: `daa24588eb08d24e9ac6dc342db1859a7105a88a8ca22652727233a42ea05110`.
V50 base walking ONNX SHA-256: `1f8e87d7370a1aeb7b57f272c96abb6df49e3039b8d1332bfce24c1a81de5b4f`. The braking digest is additional to this base-policy identity; a V50 base digest alone does not identify the composite V52 controller.

## Every failed evaluated case

Case time below is relative to its 18-second scoring window. Full compositions retain uninterrupted session time. Unrun windows after a fall are counted as failures.

### flat

| Case | First fall (s) | Failures |
|---|---:|---|
| `nominal-20-20ms--forward-08` | 14.42 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_contact:self_penetration_over_1mm; self_load:incomplete_duration |
| `nominal-20-20ms--forward-12` | 15.200000000000001 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; self_contact:incomplete_duration; self_load:incomplete_duration |
| `zero-lag--forward-12` | 16.0 | actual_joint_margin_below_minimum; fall; incomplete_duration; nonfoot_support; stop_max_speed_m_s; stop_max_tilt_deg; stop_max_yaw_rate_rad_s; self_contact:incomplete_duration; self_load:incomplete_duration |
| `zero-lag--forward-20` | 15.22 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; self_contact:incomplete_duration; self_load:incomplete_duration |
| `zero-lag--arc-left` | 14.84 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; self_contact:incomplete_duration; self_load:incomplete_duration |
| `long-30-20ms--forward-08` | 15.6 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `long-30-20ms--forward-12` | 15.68 | fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; self_contact:incomplete_duration; self_load:incomplete_duration |
| `long-30-20ms--arc-right` | 15.96 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; self_contact:incomplete_duration; self_load:incomplete_duration |

### repeated

| Case | First fall (s) | Failures |
|---|---:|---|
| `motor-10ms-sensor-20ms--forward-158--repeat-1` | 16.04 | actual_joint_margin_below_minimum; fall; incomplete_duration; nonfoot_support; stop_max_speed_m_s; stop_max_tilt_deg; stop_max_yaw_rate_rad_s; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-10ms-sensor-20ms--turn-left-738--repeat-2` | 15.98 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-10ms-sensor-20ms--arc-left-117-448--repeat-2` | 14.92 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-10ms-sensor-20ms--arc-right-184-383--repeat-1` | 16.26 | actual_joint_margin_below_minimum; fall; incomplete_duration; nonfoot_support; stop_max_speed_m_s; stop_max_tilt_deg; stop_max_yaw_rate_rad_s; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-15ms-sensor-0ms--forward-158--repeat-2` | 16.48 | actual_joint_margin_below_minimum; fall; incomplete_duration; nonfoot_support; stop_max_speed_m_s; stop_max_tilt_deg; stop_max_yaw_rate_rad_s; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-15ms-sensor-0ms--turn-right-380--repeat-1` | 15.48 | actual_joint_margin_below_minimum; backward_pursuit; fall; incomplete_duration; missing_tracking_or_stop_evidence; no_useful_translation; nonfoot_support; unsustained_bilateral_stepping; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-15ms-sensor-0ms--arc-right-184-383--repeat-1` | 14.88 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-25ms-sensor-20ms--forward-211--repeat-1` | 14.84 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-25ms-sensor-20ms--forward-201--repeat-1` | 14.86 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-25ms-sensor-20ms--turn-left-738--repeat-1` | 14.24 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration |
| `motor-10ms-sensor-20ms--forward-158--repeat-2` | — | not_run_after_terminal_fall |
| `motor-10ms-sensor-20ms--arc-right-184-383--repeat-2` | — | not_run_after_terminal_fall |
| `motor-15ms-sensor-0ms--turn-right-380--repeat-2` | — | not_run_after_terminal_fall |
| `motor-15ms-sensor-0ms--arc-right-184-383--repeat-2` | — | not_run_after_terminal_fall |
| `motor-25ms-sensor-20ms--forward-211--repeat-2` | — | not_run_after_terminal_fall |
| `motor-25ms-sensor-20ms--forward-201--repeat-2` | — | not_run_after_terminal_fall |
| `motor-25ms-sensor-20ms--turn-left-738--repeat-2` | — | not_run_after_terminal_fall |

### endurance

| Case | First fall (s) | Failures |
|---|---:|---|
| `downhill-3deg-start-1--window-1` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s |
| `downhill-3deg-start-1--window-2` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s |
| `downhill-3deg-start-2--window-1` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s |
| `downhill-3deg-start-2--window-2` | — | mean_abs_yaw_error_rad_s; endurance:tracking_bucket_2:mean_abs_yaw_error_rad_s |
| `continuous-composition-start-1--window-1` | 15.1 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `continuous-composition-start-2--window-9` | 14.58 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `continuous-composition-start-1--window-2` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-3` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-4` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-5` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-6` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-7` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-8` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-9` | — | not_run_after_terminal_fall |
| `continuous-composition-start-1--window-10` | — | not_run_after_terminal_fall |
| `continuous-composition-start-2--window-10` | — | not_run_after_terminal_fall |

### surfaces

| Case | First fall (s) | Failures |
|---|---:|---|
| `rigid-control-start-1--window-1` | 15.76 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-low-traction-start-1--window-2` | 14.38 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-middle-start-1--window-1` | 8.76 | fall; incomplete_duration; missing_tracking_or_stop_evidence; persistent_loaded_foot_slip; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-middle-start-2--window-1` | 1.84 | fall; incomplete_duration; insufficient_active_evidence; missing_bilateral_steps; missing_tracking_or_stop_evidence; no_useful_translation; unsustained_bilateral_stepping; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-high-traction-start-1--window-1` | 0.22 | missing_or_invalid_case_evidence:no posture evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `soft-high-traction-start-2--window-1` | 0.22 | missing_or_invalid_case_evidence:no posture evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-low-medium-start-2--window-2` | 16.1 | fall; incomplete_duration; nonfoot_support; persistent_loaded_foot_slip; stop_max_speed_m_s; stop_max_tilt_deg; stop_max_yaw_rate_rad_s; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-high-mild-start-1--window-1` | 14.14 | fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-high-mild-start-2--window-1` | 13.88 | actual_joint_margin_below_minimum; fall; incomplete_duration; missing_tracking_or_stop_evidence; self_contact:incomplete_duration; self_load:incomplete_duration; self_load:continuous_body_bracing; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-low-soft-start-1--window-1` | 14.620000000000001 | fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; persistent_loaded_foot_slip; self_contact:incomplete_duration; self_contact:self_penetration_over_1mm; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `unseen-low-soft-start-2--window-1` | 14.34 | fall; incomplete_duration; missing_tracking_or_stop_evidence; nonfoot_support; persistent_loaded_foot_slip; self_contact:incomplete_duration; self_contact:self_penetration_over_1mm; self_load:incomplete_duration; endurance:incomplete_endurance_evidence; endurance:missing_final_standing_posture |
| `rigid-control-start-1--window-2` | — | not_run_after_terminal_fall |
| `soft-middle-start-1--window-2` | — | not_run_after_terminal_fall |
| `soft-middle-start-2--window-2` | — | not_run_after_terminal_fall |
| `soft-high-traction-start-1--window-2` | — | not_run_after_terminal_fall |
| `soft-high-traction-start-2--window-2` | — | not_run_after_terminal_fall |
| `unseen-high-mild-start-1--window-2` | — | not_run_after_terminal_fall |
| `unseen-high-mild-start-2--window-2` | — | not_run_after_terminal_fall |
| `unseen-low-soft-start-1--window-2` | — | not_run_after_terminal_fall |
| `unseen-low-soft-start-2--window-2` | — | not_run_after_terminal_fall |

