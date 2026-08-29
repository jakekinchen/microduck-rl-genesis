"""Recette de la tâche Velocity (marche) — portage de microduck_velocity_env_cfg.py.

Les valeurs ET leurs justifications sont reprises telles quelles de l'amont :
chacune est le résultat d'un run raté. Les changer sans lire le commentaire
attaché, c'est refaire l'erreur.

Tâche principale : suivi de commande de vitesse + commande de pose de tête.
"""

from __future__ import annotations

import math

# Pas de contrôle : 24 pas par env et par itération PPO (cadence amont).
NUM_STEPS_PER_ENV = 24

# Fraction d'envs commandés à tourner sur place (lin=0, |ang| ∈ [0,4·max, max]).
# Un tirage uniforme indépendant ne produit « lin≈0, |ang| grand » que ~2 % du
# temps : le demi-tour sur place était de fait non entraîné (audit 2026-07).
TURN_IN_PLACE_FRACTION = 0.15

# --- Interrupteurs de randomisation de domaine -----------------------------
ENABLE_COM_RANDOMIZATION = True
ENABLE_HEAD_COM_RANDOMIZATION = True
ENABLE_KP_RANDOMIZATION = False  # était True
ENABLE_KD_RANDOMIZATION = False  # était True
ENABLE_MASS_INERTIA_RANDOMIZATION = True
ENABLE_JOINT_FRICTION_RANDOMIZATION = True  # via BamActuator.friction_scale
ENABLE_ARMATURE_RANDOMIZATION = True  # inertie rotorique ramenée à l'arbre
ENABLE_VELOCITY_PUSHES = True
ENABLE_IMU_ORIENTATION_RANDOMIZATION = True  # erreurs de montage
ENABLE_ENCODER_BIAS = True  # offset de calibration encodeur, constant par env
ENABLE_FOOT_FRICTION_RANDOMIZATION = True
ENABLE_SELF_COLLISION_PENALTY = True

# Rééchantillonnage des commandes de pose.
HEAD_POSE_CMD_RESAMPLE_S = (2.0, 5.0)
BODY_POSE_CMD_RESAMPLE_S = (2.0, 5.0)
TWIST_CMD_RESAMPLE_S = (3.0, 8.0)

# --- Plages de DR ----------------------------------------------------------
# DR du CoM (corps et ensemble tête) : plages par paliers, voir COM_RANGE_STAGES
# et HEAD_COM_RANGE_STAGES plus bas.
MASS_INERTIA_RANDOMIZATION_RANGE = (0.95, 1.05)  # ±5 % sur masse ET inertie
KP_RANDOMIZATION_RANGE = (0.85, 1.15)  # ±15 % (désactivé, cf. ENABLE_KP_RANDOMIZATION)
KD_RANDOMIZATION_RANGE = (0.9, 1.1)  # ±10 % (désactivé)
JOINT_FRICTION_RANDOMIZATION_RANGE = (0.9, 1.1)
ARMATURE_RANDOMIZATION_RANGE = (0.9, 1.1)
FOOT_FRICTION_RANDOMIZATION_RANGE = (0.7, 1.3)  # semelle accrocheuse, resserré depuis (0.3, 1.2)
VELOCITY_PUSH_INTERVAL_S = (3.0, 6.0)
# ±0,3 m/s et pas ±0,5 : une poussée ADDITIVE plus grande que la vitesse de
# marche max (0,4) toutes les 3-6 s entraîne une démarche nerveuse en permanence
# (audit 2026-07). ±0,3 garde la robustesse sans rendre optimale la nervosité.
VELOCITY_PUSH_RANGE = (-0.3, 0.3)
# Erreur de montage IMU jusqu'à 6°, d'AXE ALÉATOIRE — donc centrée sur zéro :
# ça entraîne la tolérance à l'AMPLITUDE d'un désalignement, pas à un biais de
# tangage. Le décalage systématique de ~5° de la vraie carte est corrigé à la
# source dans le runtime, pas ici.
IMU_ORIENTATION_RANDOMIZATION_ANGLE = 6.0
ENCODER_BIAS_RANGE = (-0.015, 0.015)  # ±0,86° par articulation, constant par env

# --- Commandes -------------------------------------------------------------
# Plages FIXES et modestes (pas de curriculum d'élargissement) : une rampe vers
# lin ±0,4 / ang ±2,0 dépassait les capacités du robot et suivait un déclin de
# la récompense après l'itération 1000. ang ±1,0 est le vrai changement : c'est
# ce qui rend le virage apprenable.
CMD_LIN_VEL_X = (-0.4, 0.4)
CMD_LIN_VEL_Y = (-0.3, 0.3)
CMD_ANG_VEL_Z = (-1.0, 1.0)
# Part d'envs « tenue debout » (commande nulle) : par paliers, voir
# STANDING_ENVS_STAGES plus bas — faible mais non nulle dès le départ.
REL_FORWARD_ENVS = 0.2  # envs « marche avant seule » (repris du gabarit mjlab)

# (Les plages de la commande de pose de tête sont par paliers : voir
# HEAD_POSE_RANGE_STAGES plus bas.)
BODY_POSE_RANGES = (
    (-0.005, 0.005),  # x (m)
    (-0.005, 0.005),  # y (m)
    (-0.005, 0.005),  # z (m)
    (-0.05, 0.05),  # roll (rad)
    (-0.05, 0.05),  # pitch (rad)
    (-0.05, 0.05),  # yaw (rad)
)

# --- Tolérances de la récompense « pose » ----------------------------------
# hip_roll serré à 0,05 : tient la position à 5° vers l'intérieur (semelle à
# plat) et empêche les jambes de s'écarter jusqu'à la verticale.
STD_STANDING = {
    "hip_yaw": 0.1,
    "hip_roll": 0.05,
    "hip_pitch": 0.15,
    "knee": 0.15,
    "ankle": 0.1,
}
STD_WALKING = {
    "hip_yaw": 0.3,
    "hip_roll": 0.05,
    "hip_pitch": 0.4,
    "knee": 0.4,
    "ankle": 0.25,  # était 0.15
}
WALKING_THRESHOLD = 0.01

# --- Poids des récompenses -------------------------------------------------
# Multipliés par le pas de contrôle (0,02 s) à l'accumulation, comme le
# RewardManager de mjlab (scale_by_dt=True par défaut).
REWARD_WEIGHTS: dict[str, float] = {
    "track_linear_velocity": 2.0,
    "track_angular_velocity": 2.0,
    # upright volontairement fort (2,0 avec std²=0,05, contre 1,0 / 0,1 avant).
    # Éval tangage-vs-vitesse 2026-07 : le robot marche avec 2-4° d'inclinaison
    # avant permanente et ~2/3 des chutes sous poussée à vitesse sont vers
    # l'AVANT. À 1,0/0,1 une inclinaison de 4° coûtait ~0,05/pas — gratuit. À
    # 2,0/0,05 elle coûte ~0,19/pas : assez de gradient pour tenir le tronc
    # droit en régime établi, tout en laissant l'inclinaison transitoire
    # (rattrapage de poussée, accélération) abordable.
    "upright": 2.0,
    "pose": 1.0,
    "body_ang_vel": -0.05,
    "angular_momentum": -0.02,
    "dof_pos_limits": -1.0,
    "action_rate_l2": -0.1,  # valeur d'étape 0 ; le curriculum rampe vers -1,0
    "air_time": 3.0,
    "foot_clearance": -2.0,
    "foot_swing_height": -0.25,
    # foot_slip volontairement faible (-0,1 et pas -1,0) : -1,0 bridait trop le
    # virage en pivot, qui est la façon dont ce robot tourne.
    "foot_slip": -0.1,
    "self_collisions": -1.0,
    # head_pose_tracking est un objectif PRIMAIRE de cet env.
    "head_pose_tracking": 2.0,
    # Rampé par curriculum (0 avant l'itération 600).
    "head_pose_bias": 0.0,
    # Infrastructure conservée mais DÉSACTIVÉE : le slot d'obs et la commande
    # restent vivants pour les envs qui montent ce poids (standup).
    "body_pose_tracking": 0.0,
}

REWARD_PARAMS = {
    "track_linear_velocity_std": math.sqrt(0.1),
    "track_angular_velocity_std": math.sqrt(0.5),
    "upright_std": math.sqrt(0.05),
    # Fenêtre de temps de vol [0,125 ; 0,300] s. L'immobilité à commande nulle
    # est enseignée par le curriculum standing_envs (→25 % d'envs immobiles vers
    # l'itération 2000), pas par un terme explicite.
    "air_time_min": 0.125,
    "air_time_max": 0.300,
    "command_threshold": 0.01,
    # Relevés de 0,01 à 0,02 pour pénaliser le pied qui traîne et forcer le
    # levé de pied.
    "foot_clearance_target": 0.02,
    "foot_swing_height_target": 0.02,
    # std=0,5 : à la commande pleine de ±1,0 rad, une politique qui ne suit pas
    # voit encore exp(-(1/0,5)²) ≈ 0,018 par articulation — gradient faible mais
    # non nul, donc l'élargissement du curriculum ne tue pas le signal.
    "head_pose_std": 0.5,
    "head_pose_bias_tau_s": 1.0,
    "self_collision_force_threshold": 10.0,
}

# --- Bruit d'observation ---------------------------------------------------
OBS_NOISE = {
    "base_ang_vel": 0.03,  # était 0.2
    "projected_gravity": 0.01,  # était 0.15
    "joint_pos": 0.001,  # était 0.05
    "joint_vel": 0.25,  # était 2.0
}
# Retards d'observation, en PAS DE CONTRÔLE (20 ms). max_lag ramené de 3 à 1 :
# 3 pas = 60 ms au pire, alors que le chemin IMU réel (bus dxl) tient dans une
# enveloppe de ±20 ms (audit 2026-07).
OBS_DELAY = {
    "base_ang_vel": (0, 1, 64),  # (min_lag, max_lag, update_period)
    "projected_gravity": (0, 1, 64),
    # Le firmware Dynamixel calcule present_velocity par moyenne glissante sur
    # la fenêtre d'échantillons précédente : la valeur lue par la politique a
    # donc ~1 période de contrôle de retard. Fixe, pas aléatoire.
    "joint_vel": (1, 1, 0),
}

# --- Épisode / simulation --------------------------------------------------
EPISODE_LENGTH_S = 20.0
SIM_DT = 0.005  # 200 Hz
DECIMATION = 4  # → contrôle à 50 Hz, la cadence de déploiement
ACTION_SCALE = 1.0
RESET_HEIGHT_RANGE = (0.12, 0.13)
TERMINATION_TILT_DEG = 70.0

# --- Curricula (en pas d'environnement cumulés) ----------------------------
# Rampe du poids action_rate : lissage doux le temps que la démarche s'amorce,
# puis on serre à -1,0 vers l'itération 1500.
ACTION_RATE_WEIGHT_STAGES = [
    (0, -0.1),
    (500 * NUM_STEPS_PER_ENV, -0.2),
    (750 * NUM_STEPS_PER_ENV, -0.4),
    (1000 * NUM_STEPS_PER_ENV, -0.6),
    (1250 * NUM_STEPS_PER_ENV, -0.8),
    (1500 * NUM_STEPS_PER_ENV, -1.0),
]

# head_pose_bias : à 0 jusqu'à l'itération 600, puis 1,0 → 3,0 vers 1500.
# Tenu à 0 au début parce qu'un terme de précision posturale est une distraction
# tant qu'il n'y a pas de démarche. À 3,0 un biais résiduel de 15° coûte
# 0,79/pas et un biais de 2° coûte 0,10/pas.
HEAD_POSE_BIAS_WEIGHT_STAGES = [
    (0, 0.0),
    (600 * NUM_STEPS_PER_ENV, 1.0),
    (1000 * NUM_STEPS_PER_ENV, 2.0),
    (1500 * NUM_STEPS_PER_ENV, 3.0),
]

# Part d'envs « tenue debout » (commande de vitesse nulle).
STANDING_ENVS_STAGES = [
    (0, 0.02),
    (500 * NUM_STEPS_PER_ENV, 0.05),
    (750 * NUM_STEPS_PER_ENV, 0.1),
    (1000 * NUM_STEPS_PER_ENV, 0.15),
    (1500 * NUM_STEPS_PER_ENV, 0.2),
    (2000 * NUM_STEPS_PER_ENV, 0.25),
]

# Élargissement par articulation, à 5 → 15 → 35 → 65 → 100 % du plafond
# mécanique — le delta atteignable depuis HOME (limites XML moins HOME, ~10 % de
# marge) : neck_pitch / head_pitch ±1,10 rad, head_yaw ±1,40, head_roll ±0,31.
HEAD_POSE_RANGE_STAGES = [
    (0, ((-0.05, 0.05), (-0.05, 0.05), (-0.07, 0.07), (-0.015, 0.015))),
    (500 * NUM_STEPS_PER_ENV, ((-0.17, 0.17), (-0.17, 0.17), (-0.21, 0.21), (-0.047, 0.047))),
    (1000 * NUM_STEPS_PER_ENV, ((-0.39, 0.39), (-0.39, 0.39), (-0.49, 0.49), (-0.11, 0.11))),
    (1500 * NUM_STEPS_PER_ENV, ((-0.72, 0.72), (-0.72, 0.72), (-0.91, 0.91), (-0.20, 0.20))),
    (2000 * NUM_STEPS_PER_ENV, ((-1.10, 1.10), (-1.10, 1.10), (-1.40, 1.40), (-0.31, 0.31))),
]

# Plafonné à ±15 mm (audit 2026-07) : la rampe précédente jusqu'à ±30 mm
# dépassait le polygone de sustentation (le talon n'est qu'à 20 mm derrière la
# cheville) — le CoM randomisé pouvait sortir entièrement du support, ce qui
# force une démarche large et hyper-réactive et rend l'équilibre ARRIÈRE
# inapprenable. La chronologie des régressions suivait les hausses de la rampe.
COM_RANGE_STAGES = [
    (0, 0.003),
    (500 * NUM_STEPS_PER_ENV, 0.005),
    (1000 * NUM_STEPS_PER_ENV, 0.01),
    (1500 * NUM_STEPS_PER_ENV, 0.015),
]
# Plafonné à ±10 mm — même souci, et la tête a un grand bras de levier (elle
# pèse 38 % de la masse totale).
HEAD_COM_RANGE_STAGES = [
    (0, 0.003),
    (500 * NUM_STEPS_PER_ENV, 0.005),
    (1000 * NUM_STEPS_PER_ENV, 0.01),
]


def stage_value(stages, step):
    """Dernière étape dont le seuil est atteint (curricula par paliers)."""
    value = stages[0][1]
    for threshold, v in stages:
        if step >= threshold:
            value = v
    return value


TRAIN_CFG = {
    "algorithm": {
        "class_name": "PPO",
        "clip_param": 0.2,
        "desired_kl": 0.01,
        "entropy_coef": 0.01,
        "gamma": 0.99,
        "lam": 0.95,
        "learning_rate": 1.0e-3,
        "max_grad_norm": 1.0,
        "num_learning_epochs": 5,
        "num_mini_batches": 4,
        "schedule": "adaptive",
        "use_clipped_value_loss": True,
        "value_loss_coef": 1.0,
    },
    "actor": {
        "class_name": "MLPModel",
        "hidden_dims": [512, 256, 128],
        "activation": "elu",
        # INVARIANT : la normalisation d'obs est ACTIVE → elle doit être cuite
        # dans l'ONNX à l'export. En simulation le bug est invisible (play
        # applique le normaliseur de toute façon).
        "obs_normalization": True,
        "distribution_cfg": {
            "class_name": "GaussianDistribution",
            "init_std": 1.0,
            "std_type": "scalar",
        },
    },
    "critic": {
        "class_name": "MLPModel",
        "hidden_dims": [512, 256, 128],
        "activation": "elu",
        "obs_normalization": True,
    },
    "obs_groups": {"actor": ["policy"], "critic": ["policy", "privileged"]},
    "num_steps_per_env": NUM_STEPS_PER_ENV,
    # 50 et pas 250 : la vidéo de progression a besoin de checkpoints
    # DENSES au début, là où l'apprentissage se joue (~4,5 Mo pièce).
    "save_interval": 50,
    "logger": "tensorboard",
}
