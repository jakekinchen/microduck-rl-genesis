# V34 authored collision-hull isolation

V33 measured actual collision support differences at the same HOME pose over
2,054 frozen directions: sole maxima 0.354/0.289 mm; all-body maximum 0.654 mm.
V32 contact-patch detection did not resolve the replay discrepancy. Return to
original V25 MPR/settings and change only robot collision mesh decimation to
False. Convexification remains enabled, matching MuJoCo's convex-mesh scope;
visuals, source CAD, authored inertias, contact masks and motor dynamics stay.

Before rollout, audit all imported colliders against native hull support at a
copied pose; maximum sampled support difference must be below 1 micrometre and
all runtime body masses must match authored values within import tolerances.
Reuse all five V31 prefixes, unchanged actions and 2-mm/5-degree numerical gates.
This is a geometry-conformance change, not an assumption that the full CAD hull
is physically calibrated. Preserve original-model V30 behavior scores separately.
