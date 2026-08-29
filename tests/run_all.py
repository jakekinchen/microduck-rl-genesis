"""Lance toute la suite de validation du portage, chacun dans son processus.

Chaque test initialise Genesis, qui ne supporte pas plusieurs `gs.init()` dans
un même processus — d'où les sous-processus.

    python tests/run_all.py
    BAM_REPO=/chemin/vers/bam python tests/run_all.py   # active les comparaisons BAM
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = [
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
    r = subprocess.run([sys.executable, os.path.join(HERE, argv[0]), *argv[1:]])
    if r.returncode != 0:
        fails.append(label)

print(f"\n{'=' * 70}")
if fails:
    print("ÉCHECS :", ", ".join(fails))
    sys.exit(1)
print("tous les tests passent")
