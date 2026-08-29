"""Environnement Velocity du Microduck sous Genesis.

Portage de `Mjlab-Velocity-{Flat,Rough}-MicroDuck` : marche avec suivi de
commande de vitesse + commande de pose de tête, à 50 Hz, actionneurs BAM.

Ce qui vient de mjlab et qu'il fallait reconstruire ici, faute d'équivalent
Genesis : les managers (observation / reward / event / curriculum / command), le
capteur de contact avec temps de vol, le capteur de hauteur de terrain sous le
pied, et la couche de randomisation de domaine. La physique de l'actionneur,
elle, est dans `bam_actuator.py`.

INVARIANT (AGENTS.md du dépôt amont) : l'observation acteur fait 61 dimensions, dans l'ordre
figé de `constants.OBS_LAYOUT`. C'est le contrat qui permet au runtime embarqué
de permuter les politiques à chaud. Ne jamais supprimer un slot de commande
inutilisé — le mettre à zéro.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from tensordict import TensorDict

import genesis as gs
from genesis.utils.geom import inv_quat, quat_to_xyz, transform_by_quat

from . import velocity_cfg as C
from .bam_actuator import BamActuator, DelayBuffer
from .constants import (
    BAM_DELAY_MAX_LAG,
    BAM_DELAY_MIN_LAG,
    DEFAULT_JOINT_POS,
    FOOT_LINKS,
    FOOT_SITE_OFFSETS,
    HEAD_BODY_NAMES,
    HEAD_JOINT_IDS,
    JOINT_NAMES,
    LEG_JOINT_IDS,
    MICRODUCK_WALK_BACKLASH_XML,
    MICRODUCK_WALK_XML,
    NUM_ACTIONS,
    NUM_OBS,
    TRUNK_BODY,
)
from .terrain import FlatTerrain, RoughTerrain


def _rand(lo, hi, shape, device):
    return torch.empty(shape, dtype=gs.tc_float, device=device).uniform_(lo, hi)


def _quat_from_angle_axis(angle, axis):
    """Quaternion (w, x, y, z) depuis angle + axe unitaire, batché."""
    half = 0.5 * angle
    return torch.cat(
        [torch.cos(half).unsqueeze(-1), axis * torch.sin(half).unsqueeze(-1)], dim=-1
    )


class MicroduckVelocityEnv:
    def __init__(
        self,
        num_envs: int,
        rough: bool = False,
        show_viewer: bool = False,
        play: bool = False,
        device=None,
        extra_morphs=None,
        camera_cfg=None,
        demo: bool = False,
        terrain_override=None,
        backlash: bool = False,
    ):
        """
        Args:
            extra_morphs: morphs Genesis ajoutés à la scène avant `build()`
                (décor de la vidéo : totems, logo), chacun soit un morph, soit
                un couple `(morph, surface)`. Ils sont statiques et ne touchent
                ni les observations ni les récompenses.
            camera_cfg: dict ou liste de dicts pour `scene.add_camera` — le
                rendu vidéo.
            terrain_override: objet terrain déjà construit (parcours de
                démonstration). Doit exposer `height_field`, `hs`, `vs`, `x0`,
                `y0` et `height_at` — même contrat que `terrain.RoughTerrain`.
            backlash: variante à JEU D'ENGRENAGE. Charge le modèle où chaque
                servo porte en série une articulation passive de ±1° (2° de jeu
                total). L'encodeur du vrai servo étant du côté SORTIE du jeu, la
                boucle firmware ET les observations `joint_pos` / `joint_vel`
                lisent à travers — sans quoi la politique laisserait le jeu
                gratuitement ET serait punie de le compenser. Dimensions d'obs
                et d'action inchangées (14 servos) : l'export ONNX et le runtime
                n'ont rien à changer.
            demo: mode « vitrine ». Coupe TOUT ce qui est là pour l'entraînement
                et rendrait une vidéo illisible : poussées, DR, bruit capteur,
                biais encodeur, désalignement IMU, rééchantillonnage automatique
                des commandes et réinitialisation sur chute. Les LIMITES
                PHYSIQUES, elles, restent actives — l'actionneur BAM, ses
                frottements et ses saturations sont le comportement honnête du
                robot, pas une perturbation.
        """
        self.num_envs = num_envs
        self.rough = rough
        self.play = play
        self.demo = demo
        self.backlash = backlash
        self._terrain_override = terrain_override
        self.device = device or gs.device

        self.dt = C.SIM_DT * C.DECIMATION  # pas de contrôle = 0,02 s (50 Hz)
        self.sim_dt = C.SIM_DT
        self.decimation = C.DECIMATION
        self.max_episode_length_s = C.EPISODE_LENGTH_S
        self.max_episode_length = math.ceil(C.EPISODE_LENGTH_S / self.dt)
        self.num_actions = NUM_ACTIONS
        self.num_obs = NUM_OBS
        # rsl_rl journalise `env.cfg` dans le checkpoint : on y met de quoi
        # reconstruire l'env à l'identique au moment du replay / de l'export.
        self.cfg = {
            "task": (
                "Course-Demo" if terrain_override is not None
                else ("Velocity-Rough" if rough else "Velocity-Flat")
                + ("-Backlash" if backlash else "")
            ),
            "num_envs": num_envs,
            "sim_dt": C.SIM_DT,
            "decimation": C.DECIMATION,
            "control_hz": 1.0 / (C.SIM_DT * C.DECIMATION),
            "episode_length_s": C.EPISODE_LENGTH_S,
            "action_scale": C.ACTION_SCALE,
            "num_obs": NUM_OBS,
            "num_actions": NUM_ACTIONS,
            "joint_names": list(JOINT_NAMES),
            "reward_weights": dict(C.REWARD_WEIGHTS),
        }

        self._build_scene(show_viewer, extra_morphs, camera_cfg)
        self._build_buffers()
        self._build_actuator()
        self._startup_randomization()
        self.reset()

    # ======================================================================
    # Construction
    # ======================================================================

    def _build_scene(self, show_viewer: bool, extra_morphs=None, camera_cfg=None) -> None:
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.sim_dt, substeps=1),
            rigid_options=gs.options.RigidOptions(
                # INDISPENSABLE : sans ça `frictionloss` et `armature` sont
                # partagés par tous les envs et la DR par-env est silencieusement
                # invalide (et BAM écrit un frottement par-env à chaque pas).
                batch_dofs_info=True,
                # Le modèle « walk » n'a que 5 géométries de collision : les 2
                # semelles et 3 géométries `self_collision_only` (support de
                # batterie + une par jambe). L'auto-collision est donc bon marché
                # ici, contrairement au modèle allcollisions.
                enable_self_collision=C.ENABLE_SELF_COLLISION_PENALTY,
                # Terrain accidenté : arêtes vives entre cases → le solveur de
                # contact décroche. mjlab compense en montant nconmax de 35 à 200
                # et les itérations de 10/20 à 30/50 ; même logique ici.
                iterations=30 if (self.rough or self._terrain_override) else 10,
                ls_iterations=50 if (self.rough or self._terrain_override) else 20,
                # Le décor de la vidéo (totems) ajoute des paires potentielles.
                max_collision_pairs=120 if self._terrain_override else (60 if self.rough else 30),
            ),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(0.8, 0.0, 0.5),
                camera_lookat=(0.0, 0.0, 0.12),
                camera_fov=40,
            ),
            vis_options=gs.options.VisOptions(
                rendered_envs_idx=[0],
                # Réglages de RENDU seulement, sans effet sur la physique. Par
                # défaut le sol et le ciel sont blancs : à l'image, un robot
                # blanc sur fond blanc disparaît. Fond sombre + lumière
                # rasante = silhouette lisible et ombres qui donnent le relief.
                **(
                    dict(
                        background_color=(0.055, 0.066, 0.092),
                        ambient_light=(0.35, 0.36, 0.40),
                        shadow=True,
                        plane_reflection=False,
                        lights=[
                            {"type": "directional", "dir": (-0.6, -0.5, -0.7),
                             "color": (1.0, 0.97, 0.92), "intensity": 6.0},
                            {"type": "directional", "dir": (0.7, 0.4, -0.4),
                             "color": (0.75, 0.82, 1.0), "intensity": 2.5},
                        ],
                    )
                    if self.demo
                    else {}
                ),
            ),
            show_viewer=show_viewer,
        )

        if self._terrain_override is not None:
            self.terrain = self._terrain_override
            self.rough = True  # relief non plan : mêmes réglages de solveur
            # Sol teinté en mode démo : le Microduck est blanc et jaune, sur un
            # sol blanc il disparaît à l'image.
            terrain_surface = (
                gs.surfaces.Default(color=(0.34, 0.36, 0.40, 1.0)) if self.demo else None
            )
            self.scene.add_entity(
                gs.morphs.Terrain(
                    height_field=self.terrain.height_field,
                    horizontal_scale=self.terrain.hs,
                    vertical_scale=self.terrain.vs,
                    pos=(self.terrain.x0, self.terrain.y0, 0.0),
                    name=f"microduck_course_{self.terrain.height_field.shape}",
                ),
                **({"surface": terrain_surface} if terrain_surface is not None else {}),
            )
        elif self.rough:
            self.terrain = RoughTerrain(
                num_rows=4 if self.play else 10,
                num_cols=4 if self.play else 10,
            )
            self.scene.add_entity(
                gs.morphs.Terrain(
                    height_field=self.terrain.height_field,
                    horizontal_scale=self.terrain.hs,
                    vertical_scale=self.terrain.vs,
                    pos=(self.terrain.x0, self.terrain.y0, 0.0),
                    # Le nom sert de clé de CACHE côté Genesis : il doit
                    # encoder la géométrie, sinon une grille « play » 4×4
                    # recharge silencieusement le terrain 10×10 d'entraînement.
                    name=(
                        f"microduck_rough_{self.terrain.num_rows}x"
                        f"{self.terrain.num_cols}_{self.terrain.patch_size}"
                        f"_{self.terrain.hs}"
                    ),
                )
            )
        else:
            self.terrain = FlatTerrain()
            self.scene.add_entity(gs.morphs.Plane())

        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file=MICRODUCK_WALK_BACKLASH_XML if self.backlash else MICRODUCK_WALK_XML,
                pos=(0.0, 0.0, 0.125),
            )
        )

        # Décor de la vidéo : statique, ajouté APRÈS le robot pour que les
        # indices de links du robot restent ceux du modèle seul.
        self.decor = []
        for item in extra_morphs or []:
            # Chaque entrée est soit un morph, soit un couple (morph, surface) :
            # `surface` appartient à `add_entity`, pas au morph.
            morph, surface = item if isinstance(item, tuple) else (item, None)
            self.decor.append(
                self.scene.add_entity(morph, surface=surface) if surface is not None
                else self.scene.add_entity(morph)
            )

        self.cams = []
        if camera_cfg is not None:
            cfgs = camera_cfg if isinstance(camera_cfg, (list, tuple)) else [camera_cfg]
            for c in cfgs:
                self.cams.append(
                    self.scene.add_camera(
                        res=c.get("res", (960, 720)),
                        pos=c.get("pos", (1.0, 0.0, 0.5)),
                        lookat=c.get("lookat", (0.0, 0.0, 0.12)),
                        fov=c.get("fov", 40),
                        GUI=False,
                    )
                )
        self.cam = self.cams[0] if self.cams else None

        self.scene.build(n_envs=self.num_envs)

        # -- indices ---------------------------------------------------------
        joint_by_name = {j.name: j for j in self.robot.joints}
        missing = [n for n in JOINT_NAMES if n not in joint_by_name]
        assert not missing, f"articulations absentes du MJCF : {missing}"
        # dof_idx_local dans l'ordre CANONIQUE de JOINT_NAMES, pas l'ordre du
        # MJCF : c'est ce qui garantit que l'action k pilote bien le servo k du
        # contrat de déploiement même si l'export Onshape réordonne un jour.
        self.motors_dof_idx = [joint_by_name[n].dof_start for n in JOINT_NAMES]
        # Articulations de jeu, dans le MÊME ordre que les servos. Sur le modèle
        # avec jeu, les articulations passives S'INTERCALENT entre les servos :
        # sélectionner par NOM plutôt que par indice est ce qui garantit
        # l'alignement (invariant amont : « ne jamais coder en dur un indice
        # d'articulation »).
        if self.backlash:
            missing_bl = [n for n in JOINT_NAMES
                          if f"passive_{n}_backlash" not in joint_by_name]
            assert not missing_bl, f"articulations de jeu absentes : {missing_bl}"
            self.backlash_dof_idx = [
                joint_by_name[f"passive_{n}_backlash"].dof_start for n in JOINT_NAMES
            ]
        else:
            self.backlash_dof_idx = None

        link_names = [l.name for l in self.robot.links]
        self.trunk_idx = link_names.index(TRUNK_BODY)
        self.foot_link_idx = [link_names.index(n) for n in FOOT_LINKS]
        self.head_link_idx = [
            link_names.index(n) for n in HEAD_BODY_NAMES if n in link_names
        ]
        self.robot_link_ids_global = set(
            range(self.robot.link_start, self.robot.link_start + self.robot.n_links)
        )

        self.foot_site_offset = torch.tensor(
            FOOT_SITE_OFFSETS, dtype=gs.tc_float, device=self.device
        )  # (2, 3)

        # Limites articulaires souples (facteur 0,9 amont) : la récompense
        # dof_pos_limits ne mord qu'au-delà.
        lo, hi = self.robot.get_dofs_limit(self.motors_dof_idx)
        lo = lo.to(self.device).flatten()[: NUM_ACTIONS]
        hi = hi.to(self.device).flatten()[: NUM_ACTIONS]
        mid, half = 0.5 * (lo + hi), 0.5 * (hi - lo)
        self.soft_limit_lo = mid - 0.9 * half
        self.soft_limit_hi = mid + 0.9 * half

    def _build_buffers(self) -> None:
        n, d = self.num_envs, self.device
        self.default_dof_pos = torch.tensor(
            DEFAULT_JOINT_POS, dtype=gs.tc_float, device=d
        )
        self.head_ids = torch.tensor(HEAD_JOINT_IDS, dtype=torch.long, device=d)
        self.leg_ids = torch.tensor(LEG_JOINT_IDS, dtype=torch.long, device=d)

        self.actions = torch.zeros((n, NUM_ACTIONS), dtype=gs.tc_float, device=d)
        self.last_actions = torch.zeros_like(self.actions)
        self.dof_pos = torch.zeros_like(self.actions)
        self.dof_vel = torch.zeros_like(self.actions)

        self.twist_cmd = torch.zeros((n, 3), dtype=gs.tc_float, device=d)
        self.head_cmd = torch.zeros((n, 4), dtype=gs.tc_float, device=d)
        self.body_cmd = torch.zeros((n, 6), dtype=gs.tc_float, device=d)
        self.is_standing_env = torch.zeros(n, dtype=torch.bool, device=d)
        self.twist_resample_at = torch.zeros(n, dtype=torch.long, device=d)
        self.head_resample_at = torch.zeros(n, dtype=torch.long, device=d)
        self.body_resample_at = torch.zeros(n, dtype=torch.long, device=d)
        self.push_at = torch.zeros(n, dtype=torch.long, device=d)

        self.episode_length_buf = torch.zeros(n, dtype=torch.long, device=d)
        self.reset_buf = torch.ones(n, dtype=torch.bool, device=d)
        self.time_out_buf = torch.zeros(n, dtype=torch.bool, device=d)
        self.rew_buf = torch.zeros(n, dtype=gs.tc_float, device=d)

        self.feet_air_time = torch.zeros((n, 2), dtype=gs.tc_float, device=d)
        self.last_contacts = torch.zeros((n, 2), dtype=torch.bool, device=d)
        self.first_contact = torch.zeros((n, 2), dtype=torch.bool, device=d)
        self.peak_swing_height = torch.zeros((n, 2), dtype=gs.tc_float, device=d)
        self.head_bias_ema = torch.zeros((n, 4), dtype=gs.tc_float, device=d)

        self.global_gravity = torch.tensor(
            [0.0, 0.0, -1.0], dtype=gs.tc_float, device=d
        ).repeat(n, 1)

        # Retards d'observation, en pas de CONTRÔLE.
        self.obs_delays = {
            k: DelayBuffer((n, dim), *C.OBS_DELAY[k], device=d)
            for k, dim in (("base_ang_vel", 3), ("projected_gravity", 3), ("joint_vel", NUM_ACTIONS))
        }

        # Curriculum de terrain : niveau (ligne) et variante (colonne) par env.
        rows, cols = self.terrain.num_rows, self.terrain.num_cols
        if getattr(self.terrain, "has_curriculum", False):
            # Démarrage sur les 5 premiers niveaux (max_init_terrain_level=5).
            self.terrain_levels = torch.randint(
                0, min(5, rows), (n,), device=d, dtype=torch.long
            )
            self.terrain_types = (
                torch.arange(n, device=d, dtype=torch.long) % cols
            )
            self.terrain_origins = torch.tensor(
                self.terrain.origins, dtype=gs.tc_float, device=d
            )
        else:
            self.terrain_levels = torch.zeros(n, dtype=torch.long, device=d)
            self.terrain_types = torch.zeros(n, dtype=torch.long, device=d)
            self.terrain_origins = torch.zeros((1, 1, 3), dtype=gs.tc_float, device=d)
        self.env_origins = self._current_env_origins()

        self.reward_names = list(C.REWARD_WEIGHTS)
        self.reward_weights = dict(C.REWARD_WEIGHTS)
        self.episode_sums = {
            k: torch.zeros(n, dtype=gs.tc_float, device=d) for k in self.reward_names
        }
        self.extras: dict = {"observations": {}, "episode": {}, "log": {}}
        self.common_step_counter = 0

    def _build_actuator(self) -> None:
        self.bam = BamActuator(
            entity=self.robot,
            dofs_idx_local=self.motors_dof_idx,
            num_envs=self.num_envs,
            device=self.device,
            dt=self.sim_dt,
            delay_min_lag=BAM_DELAY_MIN_LAG,
            delay_max_lag=BAM_DELAY_MAX_LAG,
            backlash_dofs_idx_local=self.backlash_dof_idx,
        )

    def _startup_randomization(self) -> None:
        """DR tirée UNE FOIS pour tout le run (biais systématiques par robot)."""
        n, d = self.num_envs, self.device

        if self.demo:
            # Vitrine : aucune perturbation d'entraînement, mais on garde les
            # tirages à leur valeur NEUTRE plutôt que de supprimer le code —
            # ainsi le chemin d'observation reste rigoureusement le même.
            self.imu_misalign_quat = None
            self.encoder_bias = torch.zeros((n, NUM_ACTIONS), dtype=gs.tc_float, device=d)
            self._cache_link_inertials()
            return

        # Désalignement de montage IMU : rotation constante par env, d'axe
        # aléatoire, amplitude ≤ 6°. Appliquée à l'ACTEUR uniquement — le critique
        # garde les vraies valeurs (information privilégiée).
        if C.ENABLE_IMU_ORIENTATION_RANDOMIZATION:
            axis = torch.randn(n, 3, device=d)
            axis = axis / (axis.norm(dim=-1, keepdim=True) + 1e-8)
            angle = torch.rand(n, device=d) * math.radians(
                C.IMU_ORIENTATION_RANDOMIZATION_ANGLE
            )
            self.imu_misalign_quat = _quat_from_angle_axis(angle, axis)
        else:
            self.imu_misalign_quat = None

        # Offset de calibration encodeur : constant par env, vu par l'acteur seul.
        if C.ENABLE_ENCODER_BIAS:
            self.encoder_bias = _rand(*C.ENCODER_BIAS_RANGE, (n, NUM_ACTIONS), d)
        else:
            self.encoder_bias = torch.zeros((n, NUM_ACTIONS), dtype=gs.tc_float, device=d)

        # Friction de la semelle : partagée par les deux pieds (un robot a UN
        # sol), tirée au démarrage comme amont.
        if C.ENABLE_FOOT_FRICTION_RANDOMIZATION:
            ratio = _rand(*C.FOOT_FRICTION_RANDOMIZATION_RANGE, (n, 1), d)
            self.robot.set_friction_ratio(
                ratio.repeat(1, len(self.foot_link_idx)),
                links_idx_local=self.foot_link_idx,
            )

        # Inertie rotorique ramenée à l'arbre (armature) : ±10 %, tirage par env
        # tenu pour tout le run. Voir `BamActuator.set_armature_scale` : écrire
        # l'armature coûte 1,7 s dans Genesis, donc par épisode c'est exclu — et
        # physiquement l'inertie d'un rotor ne change pas entre deux épisodes.
        if C.ENABLE_ARMATURE_RANDOMIZATION:
            self.bam.set_armature_scale(
                torch.arange(n, device=d),
                _rand(*C.ARMATURE_RANDOMIZATION_RANGE, (n, 1), d),
            )

        # Masse + inertie du tronc : ±5 %, tirage de démarrage (usage standard
        # pour la DR de masse, et pas d'accumulation possible).
        if C.ENABLE_MASS_INERTIA_RANDOMIZATION:
            lo, hi = C.MASS_INERTIA_RANDOMIZATION_RANGE
            base = float(self.robot.links[self.trunk_idx].inertial_mass)
            shift = base * (_rand(lo, hi, (n, 1), d) - 1.0)
            self.robot.set_mass_shift(shift, links_idx_local=[self.trunk_idx])

        self._cache_link_inertials()

    def _cache_link_inertials(self) -> None:
        """Masses / inerties / CoM des links, constants — pour le moment angulaire."""
        d = self.device
        self._link_inertia_local = torch.tensor(
            np.stack([np.asarray(l.inertial_i) for l in self.robot.links]),
            dtype=gs.tc_float, device=d,
        )
        self._link_mass = torch.tensor(
            [float(l.inertial_mass) for l in self.robot.links],
            dtype=gs.tc_float, device=d,
        )
        self._link_com_local = torch.tensor(
            np.stack([np.asarray(l.inertial_pos) for l in self.robot.links]),
            dtype=gs.tc_float, device=d,
        )

    # ======================================================================
    # Origines / terrain
    # ======================================================================

    def _current_env_origins(self) -> torch.Tensor:
        if not getattr(self.terrain, "has_curriculum", False):
            return torch.zeros((self.num_envs, 3), dtype=gs.tc_float, device=self.device)
        return self.terrain_origins[self.terrain_levels, self.terrain_types]

    # ======================================================================
    # Boucle
    # ======================================================================

    def step(self, actions: torch.Tensor):
        self.last_actions.copy_(self.actions)
        self.actions = torch.clip(actions, -100.0, 100.0)
        # `use_default_offset` amont : l'action est un delta autour de HOME.
        target = self.default_dof_pos + self.actions * C.ACTION_SCALE

        for _ in range(self.decimation):
            tau = self.bam.compute(target)
            self.robot.control_dofs_force(tau, self.motors_dof_idx)
            self.scene.step()

        self.episode_length_buf += 1
        self.common_step_counter += 1
        self._refresh_state()
        self._update_contacts()
        self._apply_curricula()
        self._resample_due_commands()
        self._maybe_push()

        self._compute_rewards()
        self._check_termination()

        env_ids = self.reset_buf.nonzero(as_tuple=False).flatten()
        if len(env_ids) > 0:
            self.reset_idx(env_ids)
            self._refresh_state()

        obs = self._compute_observations()
        self.extras["time_outs"] = self.time_out_buf
        return obs, self.rew_buf, self.reset_buf, self.extras

    def _refresh_state(self) -> None:
        self.base_pos = self.robot.get_pos()
        self.base_quat = self.robot.get_quat()
        inv_q = inv_quat(self.base_quat)
        self.base_lin_vel = transform_by_quat(self.robot.get_vel(), inv_q)
        self.base_ang_vel = transform_by_quat(self.robot.get_ang(), inv_q)
        self.base_ang_vel_w = self.robot.get_ang()
        self.projected_gravity = transform_by_quat(self.global_gravity, inv_q)
        self.dof_pos = self.robot.get_dofs_position(self.motors_dof_idx)
        self.dof_vel = self.robot.get_dofs_velocity(self.motors_dof_idx)
        if self.backlash_dof_idx is not None:
            # Vue ENCODEUR : l'encodeur du vrai servo est du côté sortie du jeu,
            # il mesure donc servo + jeu. Le firmware dérive present_velocity de
            # positions d'encodeur, donc la vitesse lue passe aussi par le jeu.
            self.dof_pos_enc = self.dof_pos + self.robot.get_dofs_position(
                self.backlash_dof_idx)
            self.dof_vel_enc = self.dof_vel + self.robot.get_dofs_velocity(
                self.backlash_dof_idx)
        else:
            self.dof_pos_enc, self.dof_vel_enc = self.dof_pos, self.dof_vel

        links_pos = self.robot.get_links_pos()
        links_quat = self.robot.get_links_quat()
        links_vel = self.robot.get_links_vel()
        links_ang = self.robot.get_links_ang()
        self._links_pos, self._links_quat = links_pos, links_quat
        self._links_vel, self._links_ang = links_vel, links_ang

        # Repères de pied : Genesis n'expose pas les <site>, on compose la pose
        # depuis le link cheville et l'offset local lu dans le MJCF.
        fp = links_pos[:, self.foot_link_idx]  # (n, 2, 3)
        fq = links_quat[:, self.foot_link_idx]
        off = transform_by_quat(
            self.foot_site_offset.unsqueeze(0).expand(self.num_envs, -1, -1), fq
        )
        self.foot_pos = fp + off
        # v_site = v_link + ω × (p_site − p_link)
        self.foot_vel = links_vel[:, self.foot_link_idx] + torch.cross(
            links_ang[:, self.foot_link_idx], off, dim=-1
        )
        self.foot_height = self.foot_pos[..., 2] - self.terrain.height_at(
            self.foot_pos[..., :2]
        )

    def _update_contacts(self) -> None:
        forces = self.robot.get_links_net_contact_force()  # (n, n_links, 3)
        self.foot_contact_force = forces[:, self.foot_link_idx]
        contact = self.foot_contact_force.norm(dim=-1) > 1.0
        # `first_contact` = front montant (le pied vient de se poser) ;
        # `contact` reste la valeur instantanée, sans filtre anti-rebond.
        self.first_contact = contact & (~self.last_contacts)
        self.last_contacts = contact
        self.contact = contact

        # Hauteur de vol maximale, relevée tant que le pied est en l'air ; elle
        # est évaluée à l'ATTERRISSAGE puis remise à zéro.
        self.peak_swing_height = torch.where(
            ~contact,
            torch.maximum(self.peak_swing_height, self.foot_height),
            self.peak_swing_height,
        )
        self._peak_at_landing = self.peak_swing_height.clone()
        self.peak_swing_height = torch.where(
            self.first_contact,
            torch.zeros_like(self.peak_swing_height),
            self.peak_swing_height,
        )

        self.feet_air_time = torch.where(
            contact, torch.zeros_like(self.feet_air_time), self.feet_air_time + self.dt
        )

        if C.ENABLE_SELF_COLLISION_PENALTY:
            c = self.robot.get_contacts(with_entity=self.robot)
            mask = c.get("valid_mask")
            if mask is None:
                mask = torch.ones_like(c["link_a"], dtype=torch.bool)
            force = torch.norm(c["force_a"], dim=-1)
            hit = mask & (force > C.REWARD_PARAMS["self_collision_force_threshold"])
            self.self_collision_count = hit.sum(dim=-1).to(gs.tc_float)
        else:
            self.self_collision_count = torch.zeros(
                self.num_envs, dtype=gs.tc_float, device=self.device
            )

    # ======================================================================
    # Commandes
    # ======================================================================

    def _resample_twist(self, env_ids) -> None:
        n = len(env_ids)
        r = torch.empty(n, device=self.device)
        self.twist_cmd[env_ids, 0] = r.uniform_(*C.CMD_LIN_VEL_X)
        self.twist_cmd[env_ids, 1] = r.uniform_(*C.CMD_LIN_VEL_Y)
        self.twist_cmd[env_ids, 2] = r.uniform_(*C.CMD_ANG_VEL_Z)

        rel_standing = C.stage_value(C.STANDING_ENVS_STAGES, self.common_step_counter)
        self.is_standing_env[env_ids] = r.uniform_(0.0, 1.0) <= rel_standing

        # Envs « marche avant seule » (mécanisme du gabarit mjlab).
        fwd = env_ids[r.uniform_(0.0, 1.0) <= C.REL_FORWARD_ENVS]
        if len(fwd) > 0:
            self.twist_cmd[fwd, 0] = self.twist_cmd[fwd, 0].abs().clamp(min=0.3)
            self.twist_cmd[fwd, 1] = 0.0
            self.twist_cmd[fwd, 2] = 0.0

        # Bucket explicite « demi-tour sur place » (cf. TURN_IN_PLACE_FRACTION).
        rr = torch.empty(n, device=self.device)
        turn = env_ids[rr.uniform_(0.0, 1.0) < C.TURN_IN_PLACE_FRACTION]
        if len(turn) > 0:
            self.twist_cmd[turn, :2] = 0.0
            maxr = max(abs(C.CMD_ANG_VEL_Z[0]), abs(C.CMD_ANG_VEL_Z[1]))
            m = torch.empty(len(turn), device=self.device).uniform_(0.4 * maxr, maxr)
            s = torch.where(
                torch.rand(len(turn), device=self.device) < 0.5, -1.0, 1.0
            )
            self.twist_cmd[turn, 2] = s * m
            # Ces envs DOIVENT tourner : on les retire du bucket « immobile »,
            # qui remettrait la commande à zéro.
            self.is_standing_env[turn] = False

        self.twist_cmd[env_ids] *= (~self.is_standing_env[env_ids]).unsqueeze(1)
        lo, hi = C.TWIST_CMD_RESAMPLE_S
        self.twist_resample_at[env_ids] = self.episode_length_buf[env_ids] + (
            torch.rand(n, device=self.device) * (hi - lo) + lo
        ).div(self.dt).long()

    def _resample_pose_cmd(self, env_ids, buf, ranges, at_buf, resample_s) -> None:
        n = len(env_ids)
        r = torch.empty(n, device=self.device)
        for i, (lo, hi) in enumerate(ranges):
            buf[env_ids, i] = r.uniform_(lo, hi)
        lo, hi = resample_s
        at_buf[env_ids] = self.episode_length_buf[env_ids] + (
            torch.rand(n, device=self.device) * (hi - lo) + lo
        ).div(self.dt).long()

    def _resample_due_commands(self) -> None:
        if self.demo:
            # Les commandes sont pilotées de l'extérieur (parcours scripté).
            return
        due = (self.episode_length_buf >= self.twist_resample_at).nonzero().flatten()
        if len(due) > 0:
            self._resample_twist(due)
        head_ranges = C.stage_value(C.HEAD_POSE_RANGE_STAGES, self.common_step_counter)
        due = (self.episode_length_buf >= self.head_resample_at).nonzero().flatten()
        if len(due) > 0:
            self._resample_pose_cmd(
                due, self.head_cmd, head_ranges, self.head_resample_at,
                C.HEAD_POSE_CMD_RESAMPLE_S,
            )
        due = (self.episode_length_buf >= self.body_resample_at).nonzero().flatten()
        if len(due) > 0:
            self._resample_pose_cmd(
                due, self.body_cmd, C.BODY_POSE_RANGES, self.body_resample_at,
                C.BODY_POSE_CMD_RESAMPLE_S,
            )

    def _maybe_push(self) -> None:
        if not C.ENABLE_VELOCITY_PUSHES or self.demo:
            return
        due = (self.episode_length_buf >= self.push_at).nonzero().flatten()
        if len(due) == 0:
            return
        vel = self.robot.get_vel()
        vel[due, 0] += _rand(*C.VELOCITY_PUSH_RANGE, (len(due),), self.device)
        vel[due, 1] += _rand(*C.VELOCITY_PUSH_RANGE, (len(due),), self.device)
        self.robot.set_dofs_velocity(vel[due], dofs_idx_local=[0, 1, 2], envs_idx=due)
        lo, hi = (0.5, 1.0) if self.play else C.VELOCITY_PUSH_INTERVAL_S
        self.push_at[due] = self.episode_length_buf[due] + (
            torch.rand(len(due), device=self.device) * (hi - lo) + lo
        ).div(self.dt).long()

    # ======================================================================
    # Curricula
    # ======================================================================

    def _apply_curricula(self) -> None:
        s = self.common_step_counter
        self.reward_weights["action_rate_l2"] = C.stage_value(
            C.ACTION_RATE_WEIGHT_STAGES, s
        )
        self.reward_weights["head_pose_bias"] = C.stage_value(
            C.HEAD_POSE_BIAS_WEIGHT_STAGES, s
        )
        self.com_range = C.stage_value(C.COM_RANGE_STAGES, s)
        self.head_com_range = C.stage_value(C.HEAD_COM_RANGE_STAGES, s)

    def _terrain_curriculum(self, env_ids) -> None:
        """`terrain_levels_vel` : monte d'un niveau si le robot a marché loin.

        Loin = plus de la moitié d'une parcelle. Redescend s'il a parcouru moins
        de la moitié de ce que sa commande impliquait sur l'épisode.
        """
        if not getattr(self.terrain, "has_curriculum", False) or not hasattr(self, "base_pos"):
            # Sol plat, parcours de démo, ou tout premier reset (l'état n'a pas
            # encore été lu) : il n'y a pas de niveau à faire évoluer.
            return
        dist = torch.norm(
            self.base_pos[env_ids, :2] - self.env_origins[env_ids, :2], dim=1
        )
        move_up = dist > self.terrain.patch_size / 2
        move_down = (
            dist
            < torch.norm(self.twist_cmd[env_ids, :2], dim=1)
            * self.max_episode_length_s
            * 0.5
        ) & (~move_up)
        lv = self.terrain_levels[env_ids] + move_up.long() - move_down.long()
        self.terrain_levels[env_ids] = lv.clamp(0, self.terrain.num_rows - 1)
        self.env_origins = self._current_env_origins()

    # ======================================================================
    # Observations
    # ======================================================================

    def _compute_observations(self) -> TensorDict:
        ang_vel = self.base_ang_vel
        gravity = self.projected_gravity
        if self.imu_misalign_quat is not None:
            ang_vel = transform_by_quat(ang_vel, self.imu_misalign_quat)
            gravity = transform_by_quat(gravity, self.imu_misalign_quat)

        # Retards capteurs (pas de contrôle) puis bruit uniforme.
        ang_vel = self.obs_delays["base_ang_vel"](ang_vel)
        gravity = self.obs_delays["projected_gravity"](gravity)
        joint_vel = self.obs_delays["joint_vel"](self.dof_vel_enc)

        joint_pos_rel = self.dof_pos_enc - self.default_dof_pos
        # L'acteur voit la position ENCODEUR (biaisée) ; le critique la vraie.
        actor_joint_pos = joint_pos_rel + self.encoder_bias

        def noisy(x, key):
            if self.demo:
                return x
            a = C.OBS_NOISE[key]
            return x + _rand(-a, a, x.shape, self.device)

        policy = torch.cat(
            [
                noisy(ang_vel, "base_ang_vel"),
                noisy(gravity, "projected_gravity"),
                noisy(actor_joint_pos, "joint_pos"),
                noisy(joint_vel, "joint_vel"),
                self.actions,
                self.twist_cmd,
                self.head_cmd,
                self.body_cmd,
            ],
            dim=-1,
        )
        assert policy.shape[-1] == NUM_OBS, policy.shape

        privileged = torch.cat(
            [
                self.base_lin_vel,
                joint_pos_rel,
                self.contact.to(gs.tc_float),
                self.feet_air_time,
                self.foot_height,
                self.foot_contact_force.reshape(self.num_envs, -1),
            ],
            dim=-1,
        )
        privileged = torch.nan_to_num(privileged, nan=0.0, posinf=0.0, neginf=0.0)

        obs = TensorDict(
            {"policy": policy, "privileged": privileged},
            batch_size=[self.num_envs],
            device=self.device,
        )
        self.obs = obs
        return obs

    def get_observations(self) -> TensorDict:
        return self.obs

    # ======================================================================
    # Pilotage externe (mode démo)
    # ======================================================================

    def set_twist(self, vx: float, vy: float = 0.0, wz: float = 0.0) -> None:
        """Impose la commande de vitesse (m/s, m/s, rad/s) à tous les envs."""
        self.twist_cmd[:, 0] = vx
        self.twist_cmd[:, 1] = vy
        self.twist_cmd[:, 2] = wz

    def set_head_pose(self, neck_pitch=0.0, head_pitch=0.0, head_yaw=0.0, head_roll=0.0):
        """Impose la commande de pose de tête (deltas depuis HOME, en rad)."""
        for i, v in enumerate((neck_pitch, head_pitch, head_yaw, head_roll)):
            self.head_cmd[:, i] = v

    def place(self, pos, yaw: float = 0.0, env_ids=None) -> None:
        """Repose le robot debout à un endroit et un cap donnés (rendu vidéo).

        Le placement du rendu doit être DÉTERMINISTE : `reset_idx` tire une
        position et un cap aléatoires, ce qui rend deux clips incomparables.
        """
        if env_ids is None:
            env_ids = torch.arange(self.num_envs, device=self.device)
        n = len(env_ids)
        p = torch.as_tensor(pos, dtype=gs.tc_float, device=self.device)
        p = p.unsqueeze(0).repeat(n, 1) if p.ndim == 1 else p
        y = torch.full((n,), float(yaw), device=self.device)
        quat = torch.stack(
            [torch.cos(y / 2), torch.zeros_like(y), torch.zeros_like(y), torch.sin(y / 2)],
            dim=-1,
        )
        self.robot.set_pos(p, envs_idx=env_ids)
        self.robot.set_quat(quat, envs_idx=env_ids)
        self.robot.zero_all_dofs_velocity(envs_idx=env_ids)
        self.robot.set_dofs_position(
            self.default_dof_pos.unsqueeze(0).repeat(n, 1),
            self.motors_dof_idx, envs_idx=env_ids,
        )
        if self.backlash_dof_idx is not None:
            self.robot.set_dofs_position(
                torch.zeros((n, NUM_ACTIONS), dtype=gs.tc_float, device=self.device),
                self.backlash_dof_idx, envs_idx=env_ids,
            )
        self.bam.reset(env_ids)
        self.actions[env_ids] = 0.0
        self.last_actions[env_ids] = 0.0
        self.episode_length_buf[env_ids] = 0
        self._refresh_state()
        self._update_contacts()
        return self._compute_observations()

    # ======================================================================
    # Récompenses
    # ======================================================================

    def _command_active(self) -> torch.Tensor:
        total = self.twist_cmd[:, :2].norm(dim=1) + self.twist_cmd[:, 2].abs()
        return (total > C.REWARD_PARAMS["command_threshold"]).to(gs.tc_float)

    def _compute_rewards(self) -> None:
        self.rew_buf.zero_()
        active = self._command_active()
        terms = {
            "track_linear_velocity": self._rew_track_lin,
            "track_angular_velocity": self._rew_track_ang,
            "upright": self._rew_upright,
            "pose": self._rew_pose,
            "body_ang_vel": self._rew_body_ang_vel,
            "angular_momentum": self._rew_angular_momentum,
            "dof_pos_limits": self._rew_dof_pos_limits,
            "action_rate_l2": self._rew_action_rate,
            "air_time": lambda: self._rew_air_time(active),
            "foot_clearance": lambda: self._rew_foot_clearance(active),
            "foot_swing_height": lambda: self._rew_foot_swing_height(active),
            "foot_slip": lambda: self._rew_foot_slip(active),
            "self_collisions": lambda: self.self_collision_count,
            "head_pose_tracking": self._rew_head_pose_tracking,
            "head_pose_bias": self._rew_head_pose_bias,
            "body_pose_tracking": self._rew_body_pose_tracking,
        }
        for name, fn in terms.items():
            w = self.reward_weights[name]
            if w == 0.0:
                continue
            # Comme le RewardManager de mjlab (scale_by_dt=True) : la récompense
            # est un TAUX, multiplié par le pas de contrôle.
            value = torch.nan_to_num(fn() * w * self.dt, nan=0.0, posinf=0.0, neginf=0.0)
            self.rew_buf += value
            self.episode_sums[name] += value

    def _rew_track_lin(self):
        std = C.REWARD_PARAMS["track_linear_velocity_std"]
        err = torch.sum(
            torch.square(self.twist_cmd[:, :2] - self.base_lin_vel[:, :2]), dim=1
        ) + torch.square(self.base_lin_vel[:, 2])
        return torch.exp(-err / std**2)

    def _rew_track_ang(self):
        std = C.REWARD_PARAMS["track_angular_velocity_std"]
        err = torch.square(self.twist_cmd[:, 2] - self.base_ang_vel[:, 2]) + torch.sum(
            torch.square(self.base_ang_vel[:, :2]), dim=1
        )
        return torch.exp(-err / std**2)

    def _rew_upright(self):
        std = C.REWARD_PARAMS["upright_std"]
        return torch.exp(
            -torch.sum(torch.square(self.projected_gravity[:, :2]), dim=1) / std**2
        )

    def _rew_pose(self):
        """`variable_posture` : tolérance dépendante de la vitesse commandée.

        Uniquement sur les JAMBES. La tête est pilotée par head_pose_tracking ;
        si elle était aussi dans ce terme, les deux objectifs se contrediraient
        et la politique converge vers « ignorer la commande » parce que la
        récompense de pose domine dès que le gradient de head_pose_tracking
        meurt aux grandes commandes.
        """
        speed = self.twist_cmd[:, :2].norm(dim=1) + self.twist_cmd[:, 2].abs()
        standing = (speed < C.WALKING_THRESHOLD).unsqueeze(1).to(gs.tc_float)
        std = standing * self._std_standing + (1.0 - standing) * self._std_walking
        err = torch.square(
            self.dof_pos[:, self.leg_ids] - self.default_dof_pos[self.leg_ids]
        )
        return torch.exp(-torch.mean(err / std**2, dim=1))

    def _rew_body_ang_vel(self):
        w = self._links_ang[:, self.trunk_idx, :2]  # z non pénalisé (c'est le virage)
        return torch.sum(torch.square(w), dim=1)

    def _rew_angular_momentum(self):
        """|L|² du corps entier autour de son CoM (capteur `subtreeangmom` amont).

        Décourage les mouvements de corps parasites : L = Σ [Iᵢωᵢ + mᵢ(cᵢ−c)×(vᵢ−v_c)].
        """
        R = _quat_to_mat(self._links_quat)  # (n, L, 3, 3)
        com_w = self._links_pos + torch.einsum(
            "nlij,lj->nli", R, self._link_com_local
        )
        v_com = self._links_vel + torch.cross(
            self._links_ang, com_w - self._links_pos, dim=-1
        )
        m = self._link_mass.view(1, -1, 1)
        total_m = m.sum()
        c = (com_w * m).sum(dim=1, keepdim=True) / total_m
        vc = (v_com * m).sum(dim=1, keepdim=True) / total_m
        I_w = torch.einsum(
            "nlij,ljk,nlmk->nlim", R, self._link_inertia_local, R
        )
        L = torch.einsum("nlij,nlj->nli", I_w, self._links_ang) + m * torch.cross(
            com_w - c, v_com - vc, dim=-1
        )
        L = L.sum(dim=1)
        return torch.sum(torch.square(L), dim=-1)

    def _rew_dof_pos_limits(self):
        out = -(self.dof_pos - self.soft_limit_lo).clip(max=0.0)
        out += (self.dof_pos - self.soft_limit_hi).clip(min=0.0)
        return torch.sum(out, dim=1)

    def _rew_action_rate(self):
        return torch.sum(torch.square(self.actions - self.last_actions), dim=1)

    def _rew_air_time(self, active):
        lo = C.REWARD_PARAMS["air_time_min"]
        hi = C.REWARD_PARAMS["air_time_max"]
        in_range = (self.feet_air_time > lo) & (self.feet_air_time < hi)
        return torch.sum(in_range.to(gs.tc_float), dim=1) * active

    def _rew_foot_clearance(self, active):
        target = C.REWARD_PARAMS["foot_clearance_target"]
        vel = self.foot_vel[..., :2].norm(dim=-1)
        cost = torch.sum(torch.abs(self.foot_height - target) * vel, dim=1)
        return cost * active

    def _rew_foot_swing_height(self, active):
        target = C.REWARD_PARAMS["foot_swing_height_target"]
        err = self._peak_at_landing / target - 1.0
        cost = torch.sum(
            torch.square(err) * self.first_contact.to(gs.tc_float), dim=1
        )
        return cost * active

    def _rew_foot_slip(self, active):
        vel_sq = torch.square(self.foot_vel[..., :2].norm(dim=-1))
        return torch.sum(vel_sq * self.contact.to(gs.tc_float), dim=1) * active

    def _head_pose_error(self):
        # Vue ENCODEUR, comme l'observation. Invariant amont : si une obs est
        # remappée sur une vue capteur, toute RÉCOMPENSE de suivi sur la même
        # grandeur doit mesurer la même vue — sinon la politique laisserait la
        # tête s'affaisser du jeu gratuitement ET serait punie de le compenser.
        measured = self.dof_pos_enc[:, self.head_ids] - self.default_dof_pos[self.head_ids]
        return measured - self.head_cmd

    def _rew_head_pose_tracking(self):
        std = C.REWARD_PARAMS["head_pose_std"]
        # Gaussienne PAR ARTICULATION puis moyenne : le gradient reste vivant
        # quand une seule articulation dérive, alors qu'une somme de carrés
        # tuerait toute la récompense pour une grosse erreur isolée.
        return torch.exp(-((self._head_pose_error() / std) ** 2)).mean(dim=-1)

    def _rew_head_pose_bias(self):
        """-mean(|EMA(erreur)|) : ne facture que la composante CONTINUE.

        Compagnon de head_pose_tracking, qui note l'erreur INSTANTANÉE. Serrer
        le std de ce dernier ne marche pas : marcher secoue forcément une tête
        qui fait 38 % de la masse, donc une tolérance instantanée serrée est une
        taxe permanente et INÉVITABLE sur la marche (mesurée à ~0,77/pas contre
        ~1,01/pas pour toute la récompense de temps de vol — le run du
        2026-08-20 a purement arrêté de marcher). L'affaissement moyen, lui, EST
        évitable : la politique peut biaiser sa commande de nuque vers le haut
        pour compenser la gravité. Moyenner sur tau_s laisse l'oscillation
        s'annuler et ne facture que ce biais. L1 et pas gaussien : le gradient
        reste constant aux grands biais, là où une gaussienne serrée serait
        plate et morte.
        """
        err = self._head_pose_error()
        fresh = self.episode_length_buf <= 1
        self.head_bias_ema[fresh] = 0.0
        alpha = min(1.0, self.dt / max(C.REWARD_PARAMS["head_pose_bias_tau_s"], 1e-6))
        self.head_bias_ema = (1.0 - alpha) * self.head_bias_ema + alpha * err
        return -self.head_bias_ema.abs().mean(dim=-1)

    def _rew_body_pose_tracking(self):
        """Suivi de pose du tronc 6-D : moyenne de 6 gaussiennes par axe.

        La commande est un DELTA depuis la pose debout nominale : xy par rapport
        à l'origine de l'env, z par rapport à `nominal_height`, angles par
        rapport à la verticale.

        Poids 0 dans l'env Velocity : l'infrastructure est conservée intacte
        pour que le slot d'obs et la commande restent vivants — l'env standup
        monte ce poids.
        """
        cmd = self.body_cmd
        rel = torch.nan_to_num(self.base_pos - self.env_origins, nan=0.0)
        x_err = rel[:, 0] - cmd[:, 0]
        y_err = rel[:, 1] - cmd[:, 1]
        z_err = rel[:, 2] - (0.095 + cmd[:, 2])
        rpy = quat_to_xyz(self.base_quat, rpy=True, degrees=False)
        roll_err = rpy[:, 0] - cmd[:, 3]
        pitch_err = rpy[:, 1] - cmd[:, 4]
        yaw_err = torch.atan2(
            torch.sin(rpy[:, 2] - cmd[:, 5]), torch.cos(rpy[:, 2] - cmd[:, 5])
        )
        xy_std, z_std, a_std = 0.05, 0.02, math.radians(15)
        terms = (
            torch.exp(-((x_err / xy_std) ** 2))
            + torch.exp(-((y_err / xy_std) ** 2))
            + torch.exp(-((z_err / z_std) ** 2))
            + torch.exp(-((roll_err / a_std) ** 2))
            + torch.exp(-((pitch_err / a_std) ** 2))
            + torch.exp(-((yaw_err / a_std) ** 2))
        )
        return terms / 6.0

    # ======================================================================
    # Terminaisons / reset
    # ======================================================================

    def _check_termination(self) -> None:
        self.time_out_buf = self.episode_length_buf >= self.max_episode_length
        # Chute : inclinaison du tronc au-delà de 70°.
        cos_tilt = -self.projected_gravity[:, 2].clamp(-1.0, 1.0)
        fell = cos_tilt < math.cos(math.radians(C.TERMINATION_TILT_DEG))
        # État numériquement invalide (impulsion de contact extrême) : on
        # réinitialise AVANT que le NaN ne contamine le buffer d'observation et
        # les poids du réseau.
        nan_state = self.scene.rigid_solver.get_error_envs_mask()
        nan_state = nan_state | ~torch.isfinite(self.base_pos).all(dim=1)
        nan_state = nan_state | ~torch.isfinite(self.dof_pos).all(dim=1)

        out_of_bounds = torch.zeros_like(self.time_out_buf)
        if self.rough:
            half_x = 0.5 * self.terrain.extent_x - 0.3
            half_y = 0.5 * self.terrain.extent_y - 0.3
            out_of_bounds = (self.base_pos[:, 0].abs() > half_x) | (
                self.base_pos[:, 1].abs() > half_y
            )
            self.time_out_buf |= out_of_bounds

        if self.demo:
            # On veut VOIR le robot s'effondrer aux premiers checkpoints : c'est
            # la preuve visuelle qu'il n'a pas encore appris. Seul un état
            # numériquement invalide force encore un reset.
            self.reset_buf = nan_state
        else:
            self.reset_buf = self.time_out_buf | fell | nan_state
        self._term_stats = {
            "fell_over": fell.to(gs.tc_float).mean(),
            "nan_state": nan_state.to(gs.tc_float).mean(),
            "out_of_bounds": out_of_bounds.to(gs.tc_float).mean(),
        }

    def reset_idx(self, env_ids) -> None:
        if len(env_ids) == 0:
            return
        n = len(env_ids)
        d = self.device

        self._terrain_curriculum(env_ids)
        origin = self.env_origins[env_ids]

        pos = origin.clone()
        pos[:, 0] += _rand(-0.5, 0.5, (n,), d)
        pos[:, 1] += _rand(-0.5, 0.5, (n,), d)
        pos[:, 2] += _rand(*C.RESET_HEIGHT_RANGE, (n,), d)
        yaw = _rand(-math.pi, math.pi, (n,), d)
        quat = torch.stack(
            [
                torch.cos(yaw / 2),
                torch.zeros_like(yaw),
                torch.zeros_like(yaw),
                torch.sin(yaw / 2),
            ],
            dim=-1,
        )
        self.robot.set_pos(pos, envs_idx=env_ids)
        self.robot.set_quat(quat, envs_idx=env_ids)
        self.robot.zero_all_dofs_velocity(envs_idx=env_ids)
        self.robot.set_dofs_position(
            self.default_dof_pos.unsqueeze(0).repeat(n, 1),
            self.motors_dof_idx,
            envs_idx=env_ids,
        )
        if self.backlash_dof_idx is not None:
            # Le jeu repart CENTRÉ. Les articulations de jeu passent leur vie
            # plaquées contre leurs butées ±1° ; les laisser au reset dans la
            # position de l'épisode précédent ferait démarrer chaque épisode
            # avec un décalage arbitraire de la vue encodeur.
            self.robot.set_dofs_position(
                torch.zeros((n, NUM_ACTIONS), dtype=gs.tc_float, device=d),
                self.backlash_dof_idx, envs_idx=env_ids,
            )

        # -- DR par épisode (NON accumulante : on repart du défaut à chaque fois)
        if C.ENABLE_COM_RANDOMIZATION and not self.demo:
            r = self.com_range
            self.robot.set_COM_shift(
                _rand(-r, r, (n, 1, 3), d),
                links_idx_local=[self.trunk_idx],
                envs_idx=env_ids,
            )
        if C.ENABLE_HEAD_COM_RANDOMIZATION and self.head_link_idx and not self.demo:
            r = self.head_com_range
            self.robot.set_COM_shift(
                _rand(-r, r, (n, len(self.head_link_idx), 3), d),
                links_idx_local=self.head_link_idx,
                envs_idx=env_ids,
            )
        if C.ENABLE_JOINT_FRICTION_RANDOMIZATION and not self.demo:
            self.bam.set_friction_scale(
                env_ids, _rand(*C.JOINT_FRICTION_RANDOMIZATION_RANGE, (n, 1), d)
            )
        if C.ENABLE_KP_RANDOMIZATION:
            self.bam.kp_scale[env_ids] = _rand(*C.KP_RANDOMIZATION_RANGE, (n, 1), d)
        if C.ENABLE_KD_RANDOMIZATION:
            self.bam.kd_scale[env_ids] = _rand(*C.KD_RANDOMIZATION_RANGE, (n, 1), d)

        self.bam.reset(env_ids)
        for buf in self.obs_delays.values():
            buf.reset(env_ids)

        self.actions[env_ids] = 0.0
        self.last_actions[env_ids] = 0.0
        self.feet_air_time[env_ids] = 0.0
        self.last_contacts[env_ids] = False
        self.peak_swing_height[env_ids] = 0.0
        # Les grandeurs de contact du pas précédent n'ont plus de sens après un
        # téléport : la physique n'a pas encore été intégrée dans la nouvelle
        # pose. On les met à zéro plutôt que de laisser une valeur d'un autre
        # endroit du terrain fuiter dans l'observation du critique.
        if hasattr(self, "contact"):
            self.contact[env_ids] = False
            self.first_contact[env_ids] = False
            self.foot_contact_force[env_ids] = 0.0
            self._peak_at_landing[env_ids] = 0.0
            self.self_collision_count[env_ids] = 0.0
        self.head_bias_ema[env_ids] = 0.0
        self.episode_length_buf[env_ids] = 0
        self.twist_resample_at[env_ids] = 0
        self.head_resample_at[env_ids] = 0
        self.body_resample_at[env_ids] = 0
        self.push_at[env_ids] = 0
        self._resample_twist(env_ids)
        self._resample_pose_cmd(
            env_ids,
            self.head_cmd,
            C.stage_value(C.HEAD_POSE_RANGE_STAGES, self.common_step_counter),
            self.head_resample_at,
            C.HEAD_POSE_CMD_RESAMPLE_S,
        )
        self._resample_pose_cmd(
            env_ids, self.body_cmd, C.BODY_POSE_RANGES, self.body_resample_at,
            C.BODY_POSE_CMD_RESAMPLE_S,
        )

        self.extras["episode"] = {}
        for key, value in self.episode_sums.items():
            self.extras["episode"]["rew_" + key] = (
                value[env_ids].mean() / self.max_episode_length_s
            )
            value[env_ids] = 0.0
        if self.rough:
            self.extras["episode"]["terrain_level"] = self.terrain_levels.float().mean()

    def reset(self):
        self.reset_buf[:] = True
        self._precompute_pose_stds()
        # AVANT reset_idx : la DR de CoM au reset lit les plages du curriculum.
        self._apply_curricula()
        self.reset_idx(torch.arange(self.num_envs, device=self.device))
        self._refresh_state()
        self._update_contacts()
        return self._compute_observations()

    def _precompute_pose_stds(self) -> None:
        def build(table):
            v = []
            for i in LEG_JOINT_IDS:
                name = JOINT_NAMES[i]
                match = [s for pat, s in table.items() if pat in name]
                assert match, f"pas de std pour {name}"
                v.append(match[0])
            return torch.tensor(v, dtype=gs.tc_float, device=self.device)

        self._std_standing = build(C.STD_STANDING)
        self._std_walking = build(C.STD_WALKING)


def _quat_to_mat(q: torch.Tensor) -> torch.Tensor:
    """Quaternions (..., 4) en (w, x, y, z) → matrices de rotation (..., 3, 3)."""
    w, x, y, z = q.unbind(-1)
    return torch.stack(
        [
            1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
            2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
            2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y),
        ],
        dim=-1,
    ).reshape(*q.shape[:-1], 3, 3)
