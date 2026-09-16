# Research decisions, September 6, 2026

## What was collected

- [ISRD, Kertesz](https://zenodo.org/records/45874): verified the publisher's
  archive MD5, counted 30,709 rows and 49 columns. The surface classes include
  short carpet, soft/shag carpet and carpeted floor. These are engineered
  Sony ERS-7 sensor features, not Ducky motor demonstrations or a constitutive
  material dataset. No training/adaptation accuracy is claimed from this archive.
- [Yaz and Fidan, 2025](https://doi.org/10.7216/teksmuh.1750698): Table1 gives
  5-mm pile and 7-mm overall thickness for polyester sisal-look, loop-pile
  and cut-pile samples. Their different compression/recovery behavior motivates
  retaining construction identity instead of treating every carpet as friction.
- [Gupta, Majumdar and Goswami, 2017](https://nopr.niscpr.res.in/bitstream/123456789/43250/1/IJFTR%2042%284%29%20399-406.pdf): extracted four Table4 rows with
  thickness, compression and recovery means, preserving the 2/200-kPa loads and
  30-second dwell. Figure2 is a schematic. No points were fabricated from it.
  These endpoints cannot identify Ducky-load transient damping or hysteresis.
- [Bertocci et al., 2003](https://jamanetwork.com/journals/jamapediatrics/fullarticle/481328): Table1 reports carpet/shoe dynamic friction .51 and
  static friction .58; carpet/dummy values differ. This is evidence that the
  counterface matters, not that Ducky's sole has either coefficient.
- [Bunterngchit et al., 2000](https://pmc.ncbi.nlm.nih.gov/articles/PMC2895255/):
  methods report a 4.54-kg rubber-sole pull slipmeter, quarter-inch olefin outdoor
  carpet and dynamic coefficient1.8. Different contact/load conditions prevent
  interpreting this and .51 as a measured Ducky friction distribution.

## Training design supported by the literature

[Singh et al.](https://arxiv.org/html/2504.13619v1) trained a shared biped policy
with staged exposure to compliant and uneven surfaces. Their compliance ranges
were selected for another robot, so V25 does not call those values calibration.
V25 uses a narrower exploratory soft-contact bank and fixed geometry. It does
not move the supporting terrain during an episode.

[Kumar et al.'s biped adaptation work](https://arxiv.org/abs/2205.15299) motivates
a history/adaptation experiment if explicit mixed training has an observability
limit. It does not justify copying an incompatible quadruped feature dataset
into Ducky's observation channels or adding privileged surface labels to an
actor that will not receive them in deployment.

The [MuJoCo contact documentation](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters)
describes parameter mixing. V25 verifies the assembled contact's friction and
solver timing in both runtime code paths, as well as fixed ground geometry.
Matching numerical parameters is distinct from matching material force response.

## What online data did not close

No retrieved dataset provides a matched Ducky sole, representative carpet/underlay
samples, low-pressure loading/unloading curves at gait rates, independent trials
and enough metadata to establish calibrated contact dynamics. Static endpoint
means, carpet appearance, surface-class features and another robot's successful
video do not supply those quantities. They remain explicit model uncertainty.

Thus public inputs support a reproducible prior-informed simulation experiment;
they do not license a physical carpet-ready label. No user measurement request
is necessary to execute the local development plan, and no substitute entries
were inserted into the separately gated physical-calibration intake.

## Catalog identifier correction

The frozen catalog entry `kim_lockhart_2000` uses a mistaken author mnemonic.
Its URL, apparatus and 1.8 friction value point to Bunterngchit, Lockhart,
Woldstad and Smith (2000), *Age related effects of transitional floor surfaces
and obstruction of view on gait characteristics related to slips and falls*.
[PubMed's bibliographic record](https://pubmed.ncbi.nlm.nih.gov/20607122/)
confirms DOI 10.1016/S0169-8141(99)00012-8. Preserve the frozen identifier and
source hashes; this correction changes attribution, no model or training value.

The same catalog entry's `pile_height_m` field interprets the source's
quarter-inch product description too specifically. The retrieved methods do
not separate pile height from total carpet thickness. Treat .00635 m as a
nominal carpet dimension, not a verified pile-only measurement. This geometric
field is not used in the flat-panel training model; its friction value and
all executed simulations remain unchanged.
