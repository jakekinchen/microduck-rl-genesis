# Runtime rehearsal v1 — frozen September 15, 2026

This is a compatibility diagnostic, not a behavior acceptance bank. No hardware,
device driver, paid compute, policy deployment, protected test bank, or published
artifact is involved. All TCP endpoints bind explicitly to `127.0.0.1`; all
daemons and sockets belong to the isolated `.workspace/runtime-rehearsal-v1` tree.

Sources: runtime `fead66bb21195971fcbb2858a19b1e290a9f2031`, RL/body server
`cb70b792312d559a4da09064d92009079671815f`. Do not patch upstream source.
Load exact retained V21 and V15 ONNX files from the V30 regression receipt.
Verify both file hashes before loading. Disable policy output filters, voltage
adaptation and standing gain reduction in an isolated params file; set both
action scales to one. Disable unrelated policy slots and chorale acceptance.

The upstream executable differs from the retained controller: standing selects
at command magnitude <=0.05 instead of exact zero, command scheduling is its
own, and V30 heading control is absent. Its default `scene.xml` includes
`robot_groundcontact.xml`; its position-actuator XML is not the local dynamic
BAM controller. It has no local motor/sensor-delay queues. The upstream claim of
"same BAM" therefore does not establish conformance. Preserve this raw upstream
diagnostic separately. A TerrainWorld socket adapter requires a separate timing
and command-routing conformance experiment before any equivalence claim.

First verify all 3,300 already recorded nominal course actions through the
unmodified Rust policy-rehearsal example. This checks raw 61D/14D ONNX inference,
not observation construction, actor selection, daemon timing or physics.

Then run **one** headless, localhost, one-body episode from the official HOME
placement: stand 2 seconds; walk forward at 0.12 m/s for 4 seconds; turn at
0.4 rad/s for 2 seconds; zero-command stand for 4 seconds. Commands refresh at
10 Hz, body telemetry at nominal 50 Hz. The official body is held during startup
until enabled; this setup assistance must be excluded from behavior evidence.
Maximum startup 10 seconds and whole subprocess lifetime 45 seconds. Do not
automatically retry or tune after observing the result.

Terminate the sequence on base height <0.07 m, tilt >70 degrees, nonfinite
telemetry, daemon exit, or failed IPC. Missing phases are failures. Track real
time factor, health responses, command acknowledgements, body height, position,
gyro and gravity. Require all four phases and no fall for the bounded sequence;
report timing separately (target >=45 Hz daemon, 0.95–1.05 simulated seconds per
wall second). No bilateral gait, contact load, joint-stop, posture or full
physical acceptance is inferred from this diagnostic's telemetry.

Always terminate and wait for only the child processes created by the diagnostic.
Check that its TCP listener is gone; preserve failure logs and original params.
Do not call upstream `duck-sim up/down`: it downloads its own policies, enables
them and manages its own process state. Launch the required binaries directly.
