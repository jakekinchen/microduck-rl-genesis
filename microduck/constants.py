"""Constantes du Microduck — portage Genesis de pollen-robotics/microduck_rl.

Tout ce qui est un INVARIANT de la recette sim2real amont est ici, en un seul
endroit, pour qu'une divergence saute aux yeux :

  - l'ordre des 14 servos (le contrat de déploiement) ;
  - la pose HOME (keyframe STAND2 : tronc avancé de ~5 mm au-dessus des pieds) ;
  - la découpe de l'observation acteur 61-D ;
  - les paramètres de l'actionneur BAM M6 (XL330).

Référence amont : src/mjlab_microduck/robot/microduck_constants.py et
`AGENTS.md` du dépôt amont ("Invariants — do not break these").
"""

from __future__ import annotations

import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_HERE, "assets")
ROBOT_DIR = os.path.join(ASSETS_DIR, "microduck")

# Modèle « walk » : contacts tronc/tête retirés (tomber coûte peu). C'est le
# modèle de la tâche Velocity, la seule portée ici.
MICRODUCK_WALK_XML = os.path.join(ROBOT_DIR, "robot_walk.xml")
# Même modèle, avec ±1° de jeu d'engrenage en série sur chaque servo (2° de jeu
# total). L'encodeur du vrai servo étant du côté SORTIE du jeu, la boucle
# firmware et les observations lisent à travers (cf. `velocity_env`, `backlash=`).
MICRODUCK_WALK_BACKLASH_XML = os.path.join(ROBOT_DIR, "robot_walk_backlash.xml")
# Modèle collisions complètes, pour les tâches standup/sitstand (non portées).
MICRODUCK_ALLCOLLISIONS_XML = os.path.join(ROBOT_DIR, "robot_allcollisions.xml")

BAM_XL330_M6_JSON = os.path.join(ASSETS_DIR, "xl330_m6.json")

# ---------------------------------------------------------------------------
# Articulations
# ---------------------------------------------------------------------------

# INVARIANT (AGENTS.md du dépôt amont) : 14 servos, indices 0-4 jambe gauche, 5-8 nuque/tête,
# 9-13 jambe droite. C'est l'ordre dans lequel Genesis liste les joints du MJCF
# ET l'ordre attendu par le runtime embarqué — ne pas réordonner.
JOINT_NAMES: tuple[str, ...] = (
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee",
    "left_ankle",
    "neck_pitch",
    "head_pitch",
    "head_yaw",
    "head_roll",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee",
    "right_ankle",
)
NUM_ACTIONS = len(JOINT_NAMES)

# Les 4 DOF nuque/tête, dans l'ordre de la commande head_pose.
HEAD_JOINT_NAMES: tuple[str, ...] = ("neck_pitch", "head_pitch", "head_yaw", "head_roll")
HEAD_JOINT_IDS: tuple[int, ...] = tuple(JOINT_NAMES.index(n) for n in HEAD_JOINT_NAMES)
# Les 10 DOF jambes : seule cible de la reward « pose » (la tête est pilotée par
# head_pose_tracking ; la mettre aussi dans « pose » ferait deux objectifs
# contradictoires et le policy finit par ignorer la commande).
LEG_JOINT_IDS: tuple[int, ...] = tuple(
    i for i, n in enumerate(JOINT_NAMES) if "neck" not in n and "head" not in n
)

# Pose HOME (keyframe STAND2). Le tronc est avancé de ~5 mm pour que le CoM
# tombe sur l'axe de cheville : à l'ancien HOME il était ~5 mm derrière, ce qui
# biaisait le robot vers l'arrière.
HOME_JOINT_POS: dict[str, float] = {
    "left_hip_yaw": 0.0,
    "right_hip_yaw": 0.0,
    "left_hip_roll": -0.0873,
    "right_hip_roll": 0.0873,
    "left_hip_pitch": -0.4579,
    "right_hip_pitch": 0.4579,
    "left_knee": -0.0049,
    "right_knee": 0.0049,
    "left_ankle": 0.4530,
    "right_ankle": -0.4530,
    "neck_pitch": 0.3491,
    "head_pitch": 0.3491,
    "head_yaw": 0.0,
    "head_roll": 0.0,
}
DEFAULT_JOINT_POS: tuple[float, ...] = tuple(HOME_JOINT_POS[n] for n in JOINT_NAMES)

# ---------------------------------------------------------------------------
# Corps / repères
# ---------------------------------------------------------------------------

TRUNK_BODY = "trunk_base"
FOOT_LINKS: tuple[str, ...] = ("ankle_left", "ankle_right")  # gauche puis droite

# Genesis n'expose pas les <site> MJCF. On recalcule la pose des repères de pied
# à partir du repère du link cheville + l'offset local lu dans robot_walk.xml
# (<site name="left_foot" pos="-0 -0.0238146 -0.0140852" .../>).
FOOT_SITE_OFFSETS: tuple[tuple[float, float, float], ...] = (
    (0.0, -0.0238146, -0.0140852),  # left_foot,  local à ankle_left
    (0.0, -0.0238146, -0.0140852),  # right_foot, local à ankle_right
)

# Bodies de l'ensemble tête, cible de la DR de CoM tête. `bearing_roll` n'est PAS
# un body de tête (c'est le link hip-yaw droit) mais il est listé à l'identique
# de l'amont pour préserver le comportement de DR existant.
HEAD_BODY_NAMES: tuple[str, ...] = (
    "neck",
    "neck_pitch",
    "yaw_roll_motion",
    "bottom_head_shell",
    "jaw_soft",
    "bearing_roll",
)

# ---------------------------------------------------------------------------
# Observation — CONTRAT DE DÉPLOIEMENT
# ---------------------------------------------------------------------------
# 61-D acteur = 48 proprioception + 13 commandes, exactement dans cet ordre.
# Un env qui n'utilise pas un slot de commande le met à zéro, il ne le supprime
# jamais : c'est ce qui permet au runtime de permuter les politiques à chaud.
OBS_LAYOUT: tuple[tuple[str, int], ...] = (
    ("base_ang_vel", 3),
    ("projected_gravity", 3),
    ("joint_pos", 14),
    ("joint_vel", 14),
    ("actions", 14),
    ("twist_command", 3),
    ("head_pose_command", 4),
    ("body_pose_command", 6),
)
NUM_OBS = sum(d for _, d in OBS_LAYOUT)
assert NUM_OBS == 61, NUM_OBS

# ---------------------------------------------------------------------------
# Actionneur BAM M6 (Dynamixel XL330)
# ---------------------------------------------------------------------------
# Constantes firmware du XL330 (bam/dynamixel/actuator.py). error_gain convertit
# kp_fw * Δq en rapport cyclique PWM ; il dépend de la résolution encodeur et du
# diviseur de gain interne, tous deux mesurés à l'oscilloscope par Rhoban.
XL330_ENCODER_COUNTS_PER_REV = 4096
XL330_KP_DIVISOR = 256  # observé empiriquement (le manuel annonce 128)
XL330_PWM_LIMIT = 885
XL330_ERROR_GAIN = (XL330_ENCODER_COUNTS_PER_REV / (2.0 * math.pi)) / (
    XL330_KP_DIVISOR * XL330_PWM_LIMIT
)
XL330_MAX_PWM = 1.0
XL330_MAX_CURRENT = 1.75  # limite de courant firmware [A]

# Raideur firmware conservée du microduck (microban utilise 125).
BAM_KP_FW = 200.0
# DR tension batterie : tirage par env au démarrage, constant sur tout le run.
BAM_VIN_RANGE = (6.5, 8.2)
# Chute de tension sous charge : V_drop = R * I, I estimé par Σ|τ| / kt.
# (Amont : `vin_drop_gain_range` ; même sémantique, R en ohms.)
BAM_VIN_DROP_RESISTANCE_RANGE = (0.0, 0.2)
BAM_VIN_MIN = 6.0
# Retard de commande bus/firmware, en PAS PHYSIQUES (200 Hz) → 15 à 30 ms.
BAM_DELAY_MIN_LAG = 3
BAM_DELAY_MAX_LAG = 6
