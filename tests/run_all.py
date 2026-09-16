"""Lance toute la suite de validation du portage, chacun dans son processus.

Chaque test initialise Genesis, qui ne supporte pas plusieurs `gs.init()` dans
un même processus — d'où les sous-processus.

    python tests/run_all.py
    BAM_REPO=/chemin/vers/bam python tests/run_all.py   # active les comparaisons BAM
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_ops.activity import require_idle

# Refuse before any child imports Genesis, MuJoCo or a GUI toolkit.
require_idle(ROOT)

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = [
    ("workspace tooling (no simulator)", "../scripts/verify_workspace.py"),
    ("complete contact geometry, body-interference rejection, heading servo and persistent delays", "test_walking_contact_corrections.py"),
    ("command-only standing switch and sustained internal load rejection", "test_walking_standing_runner.py"),
    ("standing-only commands and posture-gated internal-force objective", "test_standing_reward.py"),
    ("command ramp preserves raw user scoring and exact zero", "test_command_ramp.py"),
    ("load-aware walking objective preserves command/action contract", "test_walking_unbraced.py"),
    ("effective inherited command distribution and metadata", "test_walking_effective_contract.py"),
    ("filtered course correction preserves feedforward, caps and exact stop", "test_filtered_heading.py"),
    ("instantaneous yaw refinement preserves turns, stopping and inherited physics", "test_walking_yaw_refinement.py"),
    ("physical development factors apply without accumulation or cross-model leakage", "test_walking_physical_domain.py"),
    ("compiled terrain geometry, conservative sole clearance and isolated layouts", "test_walking_terrain_v23.py"),
    ("full-horizon endurance rejects drift, missing data and local tracking failures", "test_walking_endurance_v23.py"),
    ("passive calibration intake rejects missing measurements and split leakage", "test_walking_calibration.py"),
    ("whole-session heading drift cannot reset away between windows", "test_v23_session_heading.py"),
    ("posture-conditioned positive return and persistent yaw cost", "test_walking_viability.py"),
    ("additive cumulative heading fidelity", "test_walking_heading.py"),
    ("isolated non-saturating trunk balance reward", "test_walking_balance.py"),
    ("current IMU sampling without changing physical integration", "test_walking_sensor_phase.py"),
    ("native contact timing default and isolated model change", "test_walking_contact.py"),
    ("non-saturating walking command response", "test_walking_tracking.py"),
    ("full-body clearance and command diagnostic boundaries", "test_walking_diagnostics.py"),
    ("native floor masks and unchanged scene structure", "test_walking_ground.py"),
    ("neutral head command is additive walking acceptance", "test_walking_posture.py"),
    ("controlled walking effort and landing incentives", "test_walking_controlled.py"),
    ("walking sole, timing and command/stop acceptance", "test_walking.py"),
    ("physical gait rejection and camera alignment", "test_laser_gait.py"),
    ("dynamic laser and live controls", "test_laser_dynamic.py"),
    ("laser steering and perception", "test_laser_task.py"),
    ("inventaire provenance fichiers M6", "test_file_provenance.py"),
    ("contrats artefact et attestations M6", "test_artifact_contract.py"),
    ("résolution artefacts réels M6", "test_m6_real_artifact_resolution.py"),
    ("recherche autorité communautaire M6", "test_m6_community_authority_search.py"),
    ("archéologie provenance locale M6", "test_m6_local_provenance_archaeology.py"),
    ("distribution locale provenance-gated M6", "test_m6_distribution_bundle.py"),
    ("handoff autorité externe M6", "test_m6_authority_handoff.py"),
    ("admission développement first-party", "test_first_party_development.py"),
    ("contrat immuable expérience M5", "test_m5_experiment_contract.py"),
    ("proposition M5 quatrième pilote non autorisée", "test_m5_fourth_pilot_proposal.py"),
    ("proposition M5 cinquième pilote non autorisée", "test_m5_fifth_pilot_proposal.py"),
    ("proposition M5 sixième pilote non autorisée", "test_m5_sixth_pilot_proposal.py"),
    ("proposition M5 septième pilote non autorisée", "test_m5_seventh_pilot_proposal.py"),
    ("schéma benchmark Apple", "test_apple_scaling.py"),
    ("matérialisation BAM épinglée", "test_materialize_bam_authority.py"),
    ("vecteurs BAM dorés épinglés", "test_bam_golden_vectors.py"),
    ("trajectoire BAM 14 servos épinglée", "test_bam_closed_loop_fixture.py"),
    ("réconciliation des modèles épinglée", "test_model_reconciliation.py"),
    ("déterminisme d'évidence multiplateforme", "test_cross_platform_determinism.py"),
    ("sémantique de marche épinglée", "test_walking_semantics.py"),
    ("sémantique de backflip épinglée", "test_backflip_semantics.py"),
    ("décision de divergence versionnée", "test_divergence_decision.py"),
    ("coeur évaluateur C MuJoCo", "test_evaluator_core.py"),
    ("matrice de cas évaluateur", "test_evaluator_case_matrix.py"),
    ("protocole held-out aveugle", "test_heldout_protocol.py"),
    ("classifieurs de réussite", "test_success_classifiers.py"),
    ("bundle évaluateur de développement", "test_evaluator_bundle.py"),
    ("autorité ONNX marche officielle", "test_official_walking_policy_authority.py"),
    ("formules BAM vs référence Rhoban", "test_bam_formulas.py"),
    ("couple externe vs MuJoCo", "test_external_torque.py"),
    ("boucle actionneur vs MuJoCo+BAM", "test_bam_vs_mujoco.py"),
    ("randomisation de domaine", "test_dr.py"),
    ("contrat d'observation 61-D", "test_obs_contract.py"),
    ("variante à jeu d'engrenage", "test_backlash.py"),
    # Chaîne de déploiement complète : l'ONNX qui partira sur le robot rejoue
    # bien la politique sur les observations réelles de l'environnement. Se
    # déclare non applicable tant qu'aucun checkpoint n'existe.
    ("ONNX de déploiement vs politique", "test_onnx_deploy.py"),
    ("env sol plat", "smoke_env.py"),
    ("env terrain accidenté", "smoke_env.py --rough"),
]

# Contrôles facultatifs : outillage gardé hors du dépôt publié. On les lance
# s'ils sont là, on les saute sans bruit sinon — un dépôt fraîchement cloné doit
# voir sa suite passer sans dépendre de fichiers qui n'y sont pas.
OPTIONNELS = [("rien de sensible dans le dépôt", "../tools/sanity_check.py")]
EXTRA = [
    (label, cmd) for label, cmd in OPTIONNELS
    if os.path.exists(os.path.join(HERE, cmd.split()[0]))
]

fails = []
for label, cmd in TESTS + EXTRA:
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}", flush=True)
    argv = cmd.split()
    r = subprocess.run([sys.executable, os.path.join(HERE, argv[0]), *argv[1:]],
                       cwd=os.path.dirname(HERE))
    if r.returncode != 0:
        fails.append(label)

print(f"\n{'=' * 70}")
if fails:
    print("ÉCHECS :", ", ".join(fails))
    sys.exit(1)
print("tous les tests passent")
