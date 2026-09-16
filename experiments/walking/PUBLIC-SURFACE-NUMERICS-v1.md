# Additional public surface numerical audit

Frozen in script before execution: passive 0.4-kg, 40x20x10-mm rigid cuboid,
initial center height25mm, four V25 contact profiles, 2s settling at .005 and
.0025s. Compare mean indentation over final .5s with native MuJoCo. Per-profile
agreement limit is max(.1mm,20% of native indentation), with raw discrepancies
retained. This is a numerical diagnostic; no material model or controller is
selected by whether Ducky succeeds. No real-carpet claim follows agreement.

The V25 surface adapter lowers the sole friction so each floor sets the maximum
pair coefficient. It also lowers sole-to-sole friction if those two geoms touch;
all other robot collider coefficients remain unchanged. This exception must not
be described as all internal friction unchanged. Existing internal contact and
bracing rejection remains in every native locomotion evaluation.
