"""V37 retains authored collision hulls; all other V25 settings fixed."""
from .public_surface_env_v25 import PublicSurfaceWalkingEnv
from .velocity_env import (gs,C,FlatTerrain,JOINT_NAMES,TRUNK_BODY,
                           FOOT_LINKS,HEAD_BODY_NAMES,FOOT_SITE_OFFSETS,NUM_ACTIONS)
import torch


class CompatiblePatchWalkingEnv(PublicSurfaceWalkingEnv):
    def _build_scene(self, show_viewer: bool, extra_morphs=None, camera_cfg=None) -> None:
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.sim_dt, substeps=1),
            rigid_options=gs.options.RigidOptions(
                constraint_timeconst=.02,
                enable_mujoco_compatibility=True,
                contact_pruning_tolerance=None,
                use_gjk_collision=True,
                enable_contact_patch=True,
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
                max_collision_pairs=(
                    self._max_collision_pairs
                    if self._max_collision_pairs is not None
                    else (120 if self._terrain_override else (60 if self.rough else 30))
                ),
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

        self.terrain = FlatTerrain()
        self.ground = self.scene.add_entity(gs.morphs.MJCF(file=str(self.surface_xml)))

        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file=self.robot_xml,
                decimate=False,
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
