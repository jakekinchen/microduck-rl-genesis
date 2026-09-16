# Gait diagnosis evidence

Current authoritative diagnosis: `experiments/laser/GAIT_DIAGNOSIS.md`.
Both the earlier dynamic pursuit policy and the new gait-v4 checkpoint are
**rejected walking**, not transfer-ready candidates.

- `comparison.json`: final same-evaluator comparison. Old target 4/4, gait 0/4;
  v4 target 1/4, gait 0/4. Actual stop occupancy 100% to 0%, no new valid gait.
- `20260905-v4-evaluation/`: completed 600-iteration / 14,745,600-transition
  candidate, source/checkpoint/export, four full measured traces and actual
  close-up videos. Zero qualified swings in every case; reserved bank closed.
- `20260905-v4-smoke/`: completed 64×5 software smoke, not gait acceptance.
- `20260905-turn-composite-baseline/`: authoritative four-case baseline for
  the final v4 comparison, using the exact same frozen composite evaluator.
- `20260905-turn-gait-final-baseline/`: earlier single-circle physical-head-frame
  audit and sustained-stepping rejection, not the four-case final comparison.
- `20260905-turn-physical-face-audit-v3/`: corroborated +X physical head/mouth
  frame. No backward traversal; actual joint-stop, swing and slip failures.
- `20260905-genesis-exact-action-replay/`: original float32 action bytes replayed
  in Genesis, not a feedback evaluation. Both hip-yaw joints remain at stops;
  the later fixed-action path falls. No cross-engine gait/transfer pass.
- `20260905-genesis-feedback-diagnostic/`: separate fresh-feedback Genesis run;
  no root-below-7-cm event in 8 seconds, but both hip-yaw stops occupied throughout
  post-startup. Not byte-identical-action replay or calibrated transfer evidence.
- `20260905-camera-alignment-v2-r2/`: old camera looks into the head; camera-v2
  sees an 85 cm ground target with upright pixels. No physical calibration.
- `20260905-camera-alignment-v2/`: retained negative near-FOV test at 65 cm.
- `20260905-v3-quarantined-final/`: **do not resume/select**. The wrong-axis
  premise was disproven. Terminal source/checkpoint/log snapshot after verified
  process exit137; 1,695,744 logged completed transitions, partial count unknown.
- `20260905-v3-quarantined/`: earlier retention snapshot before the process
  actually exited; superseded by the terminal snapshot above.
- `20260905-smoke-failed/`: initial software smoke failed on float/bool masking.
  The bug was fixed and covered by regression tests.
- `20260905-smoke-evaluation/`: wrong-axis v3 smoke, not a usable candidate.
- All `*-audit-v1`, `*-audit-v2`, and `*-face-command-ablation-v2` receipts:
  retain as rejected diagnostic history. Their backward-facing labels used
  the faulty CAMERA axis, not the physical SITE, and must not support a claim.

No historical receipt is rewritten to hide that incorrect inference. Final
comparison, tests and root checksums bind the completed diagnosis. The full
repository suite passed before the last two additional focused regression tests;
all 14 focused tests subsequently passed. Target-only scores and synthetic
classifier positives never establish physical transfer. The next task is basic
locomotion, not another automatic laser reward cycle.
