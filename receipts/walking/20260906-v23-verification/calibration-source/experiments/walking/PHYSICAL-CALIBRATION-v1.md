# Ducky-specific physics calibration

Current status: no Ducky-specific raw measurement corpus found in the inspected
Genesis workspace, real-runtime repository, official RL repository or pinned
BAM source checkout. The pinned `xl330_m6.json` is an inherited actuator model;
it does not identify this robot, its battery, feet, assembly or test surface.
All existing policies and physics parameters remain unchanged.

## First executable stage: passive measurements

Use `scripts/calibrate_walking_physics.py`; it performs offline analysis only.
`receipts/walking/20260906-physical-calibration-intake/measurements.json` is an
unfilled collection manifest. Empty slots fail; there are no synthetic readings.
Record robot serial, assembly revision, battery, actual sole material, surface
and instrument identity. Photograph/survey the setup and retain original sensor
exports or readings. Record UTC acquisition time, operator, instrument calibration
reference and expanded 95% uncertainty including setup/survey/tare uncertainty.
Bind every original record by SHA256. A metadata declaration is not independent
verification of measurement authenticity.

Four quantities have executable reductions and fixed gates:

| Quantity | Physical collection and raw JSON fields | Held-out tolerance |
|---|---|---|
| Total mass | Installed battery and complete assembly; stable calibrated scale; `scale_gross_kg`, `scale_tare_kg`. | 0.015 kg |
| HOME COM X/Y | Tared rigid platform on at least three noncollinear surveyed load cells. Robot in measured HOME; survey support coordinates in `trunk_HOME_xy_m`, using external reference marks. `tare_corrected_supports`: `x_m`, `y_m`, `normal_force_n`; `pose`: `measured_HOME`; `coordinate_frame`: `trunk_HOME_xy_m`. COM is the support-load weighted coordinate. Foot centers are not load-cell support coordinates. | 0.003 m per axis |
| Kinetic friction | Separate weighted sled carrying the actual sole material on the named horizontal surface. Steady 0.02–0.15 m/s, absolute acceleration <=0.02 m/s². `test`: `constant_speed_horizontal_sled_with_actual_sole_material`; >=50 `steady_samples` over >=1 s with `time_s`, `speed_m_s`, `acceleration_m_s2`, `tangential_force_n`, `normal_force_n`. Mean tangential/normal force ratio. Breakaway tilt measures static friction and cannot substitute. | 0.15 dimensionless |

Every raw JSON includes `source: physical_measurement`, the manifest's exact
`identity` object, `captured_at_utc`, `operator`, `setup_evidence`,
`instrument_calibration_reference`, `unit` and `expanded_uncertainty_95`.
Units are kg, m and dimensionless respectively. Per-record expanded uncertainty
must be positive and <= one third of the corresponding tolerance. These gates
are provisional engineering targets, not claims about available instruments.
The intake rejects values outside its declared range; investigate rather than
silently clipping or changing a gate after seeing data.

For each quantity preassign five fit records and three validation records, with
at least two acquisition sessions in each split. Fit and validation sessions,
raw hashes and trial identities must be disjoint. Re-seat/re-tare between trials;
collect validation in later sessions without using its outcomes to alter the fit.
Hash and freeze the manifest before analysis. Estimate from the fit mean only.
Retain systematic uncertainty without dividing it by sqrt(n), plus a t-based
repeatability term. Every held-out absolute residual plus measurement and fit
uncertainty must satisfy its tolerance. Never average away a bad held-out record.
Analysis exposes this validation set; a revised fit needs a newly preregistered set.

Commands, after real collection and hash assignment:

```sh
.venv-apple/bin/python scripts/calibrate_walking_physics.py freeze --bundle receipts/walking/20260906-physical-calibration-intake
.venv-apple/bin/python scripts/calibrate_walking_physics.py analyze --bundle receipts/walking/20260906-physical-calibration-intake --output receipts/walking/20260906-physical-calibration-intake/first-measured-result.json
```

## Remaining measured physics stages

The passive-stage result always keeps overall physical calibration incomplete.
Total mass and planar COM cannot identify the individual link masses, 3D COMs or
full inertias. Measure those with weighed components, surveyed geometry and an
appropriate pendulum/inertia fixture; check positive-definite physically feasible
inertia and independent passive-response residuals before model replacement.

For all 14 actual servos, record actuator identity/firmware/gains, independent
angle and torque references, known test load and moment arm, timestamps, applied
targets, measured angle/velocity, supply voltage/current and temperature. Bench
trials require the correctly identified restrained hardware, human supervision
and a reviewed collection adapter. Do not launch BAM's bulk recorder directly:
it actively drives hardware and its available implementations have fixed device
assumptions. Fit only training trials; hold out separate loads, directions,
voltages and acquisition sessions. Freeze torque/angle/timing residual gates with
the actual sensor resolution before collection. Preserve the old XL330 model.

Separately measure joint zeros/axes/stops/backlash, IMU extrinsics/noise/bias and
clock/latency, battery voltage sag, sole impact/compliance and contact slip. Finally
use externally tracked, synchronized held-out physical motion and byte-identical
simulator action replay; compare dynamics without refitting the same episode.
No current calibration tool can auto-admit these missing stages.

BAM's primary acquisition and fitting guidance:
https://bam.readthedocs.io/en/latest/identification/acquisition.html and
https://bam.readthedocs.io/en/latest/identification/fitting.html . Local authority
is `.workspace/bam` at `62bd8ce12154340be97e06f7f41a0ca8f116d967`.
