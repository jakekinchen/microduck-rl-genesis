"""Actionneur BAM M6 (Dynamixel XL330) vectorisé pour Genesis.

Portage de `bam.mjlab.BamActuator` (998 lignes, dépendantes de mujoco_warp) sur
l'API Genesis. La physique du modèle est identique — c'est le cœur du sim2real
du Microduck : à cette échelle (14 XL330 sous un bipède de 800 g), la fidélité
de l'actionneur est l'essentiel de l'écart sim→réel.

Pipeline BAM, inchangé :

  1. **Loi de commande firmware** — contrôleur P en position → rapport cyclique
     → tension, avec limiteur de courant modélisé comme une contrainte sur le
     rapport cyclique (le firmware ne peut agir que sur le PWM, pas synthétiser
     une tension arbitraire).
  2. **Couple moteur CC** — τ = kt·V/R − kt²·q̇/R (force contre-électromotrice).
  3. **Budget de frottement** — Coulomb + Stribeck + terme dépendant de la
     charge, directionnel et quadratique (variante m6).

Point clé du portage : comme MuJoCo, Genesis implémente `frictionloss` comme une
*contrainte* à jacobienne identité (le solveur écrête lui-même le couple d'arrêt
— l'algorithme 1 de BAM). On écrit donc le budget dans `dofs_info.frictionloss`
à chaque pas physique au lieu d'injecter un couple de frottement passif, ce qui
reproduit exactement le comportement amont. C'est ce qui rend le portage fidèle
plutôt qu'approximatif.

Prérequis Genesis : `RigidOptions(batch_dofs_info=True)`, sans quoi
`frictionloss` / `armature` sont partagés par tous les envs et les écritures
par-env sont silencieusement invalides.
"""

from __future__ import annotations

import json

import torch

import genesis as gs
from genesis.utils.misc import qd_to_torch

from .constants import (
    BAM_KP_FW,
    BAM_VIN_DROP_RESISTANCE_RANGE,
    BAM_VIN_MIN,
    BAM_VIN_RANGE,
    BAM_XL330_M6_JSON,
    XL330_ERROR_GAIN,
    XL330_MAX_CURRENT,
    XL330_MAX_PWM,
)


class DelayBuffer:
    """Retard par-env, tiré dans [min_lag, max_lag], en pas de la boucle appelante.

    Reproduit `mjlab.utils.buffers.DelayBuffer` : un historique circulaire de
    (max_lag + 1) entrées, un lag entier par env, retiré tous les
    `update_period` pas. Sert au retard de commande de l'actionneur (pas
    physiques) et aux retards d'observation (pas de contrôle).
    """

    def __init__(self, shape, min_lag: int, max_lag: int, update_period: int, device):
        self.min_lag = int(min_lag)
        self.max_lag = int(max_lag)
        self.update_period = int(update_period)
        self.device = device
        self.num_envs = shape[0]
        self._len = self.max_lag + 1
        self._buf = torch.zeros((self._len, *shape), dtype=gs.tc_float, device=device)
        self._head = 0
        self._lag = torch.randint(
            self.min_lag, self.max_lag + 1, (self.num_envs,), device=device
        )
        # Phase décalée par env : sans ça tous les envs retirent leur lag au même
        # pas et le bruit de latence devient corrélé sur le batch.
        self._phase = torch.randint(
            0, max(self.update_period, 1), (self.num_envs,), device=device
        )
        self._needs_fill = torch.ones(self.num_envs, dtype=torch.bool, device=device)
        self._step = 0

    def reset(self, env_ids):
        # Ne PAS mettre l'historique à zéro : un env fraîchement réinitialisé
        # lirait alors une gravité projetée nulle pendant `max_lag` pas, ce qui
        # ressemble à une chute libre. On marque plutôt l'env pour que le
        # prochain appel réécrive tout son historique avec la valeur courante.
        self._needs_fill[env_ids] = True

    def __call__(self, value: torch.Tensor) -> torch.Tensor:
        if self.max_lag == 0:
            return value
        self._buf[self._head] = value
        if self._needs_fill.any():
            # Historique pas encore valide (démarrage ou env réinitialisé) :
            # un lag y pointerait sur des zéros. On le remplit avec la valeur
            # courante, pour ces envs seulement.
            fill = self._needs_fill.unsqueeze(0).unsqueeze(-1)
            self._buf = torch.where(fill, value.unsqueeze(0).expand_as(self._buf), self._buf)
            self._needs_fill[:] = False
        if self.update_period > 0 and self.max_lag > self.min_lag:
            due = ((self._step + self._phase) % self.update_period) == 0
            if due.any():
                new = torch.randint(
                    self.min_lag, self.max_lag + 1, (self.num_envs,), device=self.device
                )
                self._lag = torch.where(due, new, self._lag)
        idx = (self._head - self._lag) % self._len
        out = self._buf[idx, torch.arange(self.num_envs, device=self.device)]
        self._head = (self._head + 1) % self._len
        self._step += 1
        return out


class BamActuator:
    """BAM M6 sur Genesis — batché (num_envs, 14) de bout en bout.

    Args:
        entity: l'entité rigide du robot.
        dofs_idx_local: indices locaux (entité) des 14 DOF servo.
        num_envs / device / dt: dt est le pas PHYSIQUE (1/200 s), pas le pas de
            contrôle : la loi de commande firmware tourne à la fréquence physique.
        backlash_dofs_idx_local: indices locaux des articulations passives de
            jeu d'engrenage, alignés sur `dofs_idx_local` (None = modèle sans
            jeu). Sur le vrai servo, l'encodeur magnétique est du côté SORTIE du
            jeu : la boucle de position du firmware se referme donc sur
            main + backlash — tant que le servo traverse la zone morte, la
            position mesurée, et donc l'erreur, ne bougent pas. C'est ce que
            reproduit cet argument.
    """

    def __init__(
        self,
        entity,
        dofs_idx_local,
        num_envs: int,
        device,
        dt: float,
        json_path: str = BAM_XL330_M6_JSON,
        kp_fw: float = BAM_KP_FW,
        vin_range=BAM_VIN_RANGE,
        vin_drop_resistance_range=BAM_VIN_DROP_RESISTANCE_RANGE,
        vin_min: float = BAM_VIN_MIN,
        delay_min_lag: int = 0,
        delay_max_lag: int = 0,
        quadratic_sign_gate: bool = False,
        backlash_dofs_idx_local=None,
    ):
        self.entity = entity
        self.solver = entity.solver
        self.num_envs = num_envs
        self.device = device
        self.dt = dt
        self.n_joints = len(dofs_idx_local)

        self.dofs_idx_local = torch.as_tensor(
            dofs_idx_local, dtype=torch.long, device=device
        )
        # Indices GLOBAUX solveur : `dyn_state.dofs` / `dyn_info.dofs` sont
        # indexés sur tous les DOF de la scène, pas sur ceux de l'entité.
        self.dofs_idx_global = self.dofs_idx_local + entity.dof_start
        self.backlash_dofs_idx_local = (
            None if backlash_dofs_idx_local is None
            else torch.as_tensor(backlash_dofs_idx_local, dtype=torch.long, device=device)
        )

        p = json.load(open(json_path))
        self.kt = float(p["kt"])
        self.R = float(p["R"])
        self.armature = float(p["armature"])
        self.friction_base = float(p["friction_base"])
        self.friction_stribeck = float(p["friction_stribeck"])
        self.load_friction_motor = float(p["load_friction_motor"])
        self.load_friction_external = float(p["load_friction_external"])
        self.load_friction_motor_stribeck = float(p["load_friction_motor_stribeck"])
        self.load_friction_external_stribeck = float(
            p["load_friction_external_stribeck"]
        )
        self.load_friction_motor_quad = float(p["load_friction_motor_quad"])
        self.load_friction_external_quad = float(p["load_friction_external_quad"])
        self.dtheta_stribeck = float(p["dtheta_stribeck"])
        self.alpha = float(p["alpha"])
        self.friction_viscous = float(p["friction_viscous"])

        self.kp_fw = kp_fw
        self.error_gain = XL330_ERROR_GAIN
        self.max_pwm = XL330_MAX_PWM
        self.max_current = XL330_MAX_CURRENT
        self.vin_min = vin_min
        self.quadratic_sign_gate = quadratic_sign_gate

        shape1 = (num_envs, 1)
        # Tension batterie par env, tirée une fois pour tout le run (c'est un
        # biais systématique par robot, pas un bruit par épisode).
        self.vin_nominal = torch.empty(shape1, device=device).uniform_(*vin_range)
        self.vin_drop_resistance = torch.empty(shape1, device=device).uniform_(
            *vin_drop_resistance_range
        )

        ones = torch.ones(shape1, device=device)
        self.kp_scale = ones.clone()
        self.kd_scale = ones.clone()
        # Multiplicateur par-env du budget de frottement indépendant de la
        # vitesse (Coulomb + Stribeck + charge) : c'est le terme qui porte
        # l'essentiel de l'incertitude sim2real (striction / réducteur).
        self.friction_scale = ones.clone()

        self._delay = DelayBuffer(
            (num_envs, self.n_joints),
            delay_min_lag,
            delay_max_lag,
            update_period=0,
            device=device,
        )

        # Couple appliqué au pas précédent : BAM s'en sert comme charge côté
        # moteur pour le budget de frottement ET comme estimateur de courant
        # pour la chute de tension batterie.
        self.prev_torque = torch.zeros(
            (num_envs, self.n_joints), dtype=gs.tc_float, device=device
        )

        self._install_dof_properties()

    # -- installation dans le modèle -----------------------------------------

    def _install_dof_properties(self) -> None:
        """Aligne les propriétés DOF du MJCF sur ce que BAM attend.

        Équivalent de `BamActuator.edit_spec` amont : l'armature devient
        l'inertie rotorique ajustée de BAM, l'amortissement devient le terme
        visqueux de BAM, et `frictionloss` est mis à zéro — c'est BAM qui le
        réécrit à chaque pas. Laisser le frottement du MJCF en place le
        compterait deux fois.
        """
        n = self.n_joints
        idx = self.dofs_idx_local
        self.entity.set_dofs_armature(
            torch.full((n,), self.armature, device=self.device), idx
        )
        self.entity.set_dofs_damping(
            torch.full((n,), self.friction_viscous, device=self.device), idx
        )
        self.entity.set_dofs_frictionloss(torch.zeros(n, device=self.device), idx)
        # BAM produit le couple lui-même : on désactive tout ressort/PD interne.
        self.entity.set_dofs_kp(torch.zeros(n, device=self.device), idx)
        self.entity.set_dofs_kv(torch.zeros(n, device=self.device), idx)
        self.entity.set_dofs_stiffness(torch.zeros(n, device=self.device), idx)
        self.default_armature = torch.full(
            (self.num_envs, n), self.armature, dtype=gs.tc_float, device=self.device
        )
        self._armature = self.default_armature.clone()

    # -- DR ------------------------------------------------------------------

    def set_friction_scale(self, env_ids, scale: torch.Tensor) -> None:
        self.friction_scale[env_ids] = scale

    def set_armature_scale(self, env_ids, scale: torch.Tensor) -> None:
        """DR d'armature, NON accumulante : on repart toujours du défaut BAM.

        ATTENTION — à n'appeler qu'AU DÉMARRAGE, jamais par épisode. Mesuré sur
        Genesis 1.2.2 : `set_dofs_armature` coûte **1,7 s par appel**, avec ou
        sans `envs_idx` (changer l'armature invalide la matrice de masse, que
        Genesis refactorise). Les setters voisins sont à 0,02 ms
        (`set_dofs_frictionloss`, `set_dofs_damping`) : c'est propre à
        l'armature. Appelé à chaque reset, il multipliait par 6 le temps
        d'itération.

        Ce n'est pas qu'un contournement de performance : l'inertie rotorique
        d'un servo ne change pas d'un épisode à l'autre sur un vrai robot. Un
        tirage par ENV tenu pour tout le run couvre la même distribution — c'est
        exactement l'argument que l'amont applique déjà à la DR de masse
        ("startup mode = fixed per env for the whole run; standard for mass DR").
        """
        self._armature[env_ids] = self.default_armature[env_ids] * scale
        self.entity.set_dofs_armature(self._armature, self.dofs_idx_local)

    def reset(self, env_ids) -> None:
        self.prev_torque[env_ids] = 0.0
        self._delay.reset(env_ids)

    # -- couple externe vu par le réducteur ----------------------------------

    def _dof_friction_force(self) -> torch.Tensor:
        """Effort de contrainte produit par NOTRE propre `frictionloss`.

        Les contraintes de frottement DOF occupent le bloc contigu
        [n_constraints_equality, +n_frictionloss) et ont une jacobienne
        identité : `efc_force` sur ces lignes EST l'effort en espace DOF. Elles
        sont empilées dans l'ordre croissant des DOF, donc la k-ième ligne
        correspond au k-ième DOF à frottement non nul. (Même raisonnement que
        `RigidSolver.get_dofs_actuator_force`.)
        """
        cs = self.solver.constraint_solver
        efc_force = qd_to_torch(cs.efc_force, transpose=True)
        n_eq = qd_to_torch(cs.n_constraints_equality)
        frictionloss = qd_to_torch(
            self.solver.dyn_info.dofs.frictionloss, transpose=True
        )
        if frictionloss.ndim == 1:  # batch_dofs_info=False
            frictionloss = frictionloss.unsqueeze(0).expand(self.num_envs, -1)
        has_fl = frictionloss > gs.EPS
        rank = torch.cumsum(has_fl, dim=-1) - 1
        gather_idx = (n_eq[:, None] + rank).clamp_(min=0)
        return torch.gather(efc_force, 1, gather_idx) * has_fl

    def _external_torque(self) -> torch.Tensor:
        """Charge externe sur le réducteur : gravité + Coriolis + contraintes.

        On RETIRE la contrainte de frottement DOF qu'on a nous-même injectée au
        pas précédent : sans ça les termes de frottement dépendants de la charge
        se rebouclent sur eux-mêmes.
        """
        qf_bias = qd_to_torch(self.solver.dyn_state.dofs.qf_bias, transpose=True)
        qf_constraint = qd_to_torch(
            self.solver.dyn_state.dofs.qf_constraint, transpose=True
        )
        qf_friction = self._dof_friction_force()
        g = self.dofs_idx_global
        return -qf_bias[:, g] + qf_constraint[:, g] - qf_friction[:, g]

    # -- budget de frottement ------------------------------------------------

    def _friction_budget(
        self,
        motor_torque: torch.Tensor,
        external_torque: torch.Tensor,
        stribeck_coeff: torch.Tensor,
    ) -> torch.Tensor:
        """Budget de frottement indépendant de la vitesse, variante m6.

        m6 = frottement de charge directionnel (côté moteur vs côté externe)
        + terme quadratique de Stribeck.
        """
        fl = torch.full_like(motor_torque, self.friction_base)
        fl = fl + stribeck_coeff * self.friction_stribeck

        gearbox = torch.abs(
            external_torque * self.load_friction_external
            - motor_torque * self.load_friction_motor
        )
        fl = fl + gearbox

        gearbox_stribeck = torch.abs(
            external_torque * self.load_friction_external_stribeck
            - motor_torque * self.load_friction_motor_stribeck
        )
        fl = fl + stribeck_coeff * gearbox_stribeck

        abs_ext = torch.abs(external_torque)
        abs_mot = torch.abs(motor_torque)
        drive = (abs_mot > abs_ext).to(motor_torque.dtype)
        quad = (
            drive * self.load_friction_external_quad * abs_ext**2
            + (1.0 - drive) * self.load_friction_motor_quad * abs_mot**2
        )
        if self.quadratic_sign_gate:
            # Le modèle BAM de référence (bam/model.py, numpy) n'active le terme
            # quadratique que quand couples moteur et externe sont de signes
            # OPPOSÉS. `bam.mjlab` — le chemin qui a réellement entraîné les
            # politiques déployées sur le robot — a perdu cette garde. Écart
            # mesuré : 1,5 % au pire sur le budget de frottement (voir le test
            # tests/test_bam_formulas.py). Par défaut on reproduit mjlab, pour rester sur
            # la recette qui transfère ; ce flag remet la version du papier.
            quad = quad * (torch.sign(external_torque) != torch.sign(motor_torque)).to(
                motor_torque.dtype
            )
        fl = fl + stribeck_coeff * quad

        # DR par-env sur la partie indépendante de la vitesse uniquement ; le
        # terme visqueux reste au nominal (il porte moins d'incertitude).
        return fl * self.friction_scale

    # -- boucle principale ---------------------------------------------------

    def compute(self, position_target: torch.Tensor) -> torch.Tensor:
        """Un pas de l'actionneur. Retourne le couple moteur (num_envs, 14).

        Écrit au passage le budget de frottement dans le modèle : le solveur
        Genesis fera lui-même l'écrêtage statique au pas suivant.
        """
        q = self.entity.get_dofs_position(self.dofs_idx_local)
        dq = self.entity.get_dofs_velocity(self.dofs_idx_local)
        if self.backlash_dofs_idx_local is not None:
            # La boucle firmware lit l'encodeur À TRAVERS le jeu (côté sortie).
            # La VITESSE, elle, reste côté moteur : dans BAM elle n'intervient
            # que dans la contre-FEM et le frottement, qui sont de la physique
            # de rotor, pas un signal dérivé de l'encodeur.
            q = q + self.entity.get_dofs_position(self.backlash_dofs_idx_local)

        # Retard bus/firmware sur la cible (3-6 pas physiques = 15-30 ms).
        target = self._delay(position_target)

        # Tension d'alimentation par env, moins la chute sous charge.
        # I ≈ Σ|τ| / kt sur les articulations pilotées.
        vin = self.vin_nominal
        if self.vin_drop_resistance is not None:
            current = self.prev_torque.abs().sum(dim=-1, keepdim=True) / self.kt
            vin = vin - self.vin_drop_resistance * current
            vin = torch.clamp(vin, min=self.vin_min)

        # kd_scale ne module que l'amortissement ÉLECTRIQUE (contre-FEM) : les
        # deux endroits qui utilisent la vitesse (limiteur de courant et couple
        # moteur) sont exactement ces termes-là, donc une vitesse mise à
        # l'échelle applique kd_scale de façon cohérente.
        vel = dq * self.kd_scale
        kp = self.kp_fw * self.kp_scale

        # 1. Loi firmware : erreur de position → rapport cyclique.
        duty = (target - q) * kp * self.error_gain
        # Limiteur de courant firmware : borne le duty pour que
        # I = (duty·vin − kt·q̇)/R reste dans ±max_current. Ce n'est qu'une
        # TENTATIVE — l'écrêtage PWM physique ci-dessous est appliqué en
        # dernier, donc à grande vitesse la contre-FEM peut rendre la limite
        # inatteignable, exactement comme le vrai firmware.
        back_emf = self.kt * vel
        duty_span = self.R * self.max_current / vin
        duty_center = back_emf / vin
        duty = torch.clamp(duty, duty_center - duty_span, duty_center + duty_span)
        duty = torch.clamp(duty, -self.max_pwm, self.max_pwm)
        volts = vin * duty

        # 2. Couple moteur CC avec contre-FEM.
        motor_torque = self.kt * volts / self.R - (self.kt**2) * vel / self.R

        # 3. Coefficient de Stribeck : 1 à l'arrêt → 0 en mouvement.
        stribeck = torch.exp(-torch.pow(torch.abs(dq) / self.dtheta_stribeck, self.alpha))

        # 4. Budget de frottement → frictionloss du modèle. On utilise le couple
        # du pas PRÉCÉDENT comme charge côté moteur (comme BAM/MuJoCo), pas le
        # couple fraîchement calculé.
        external_torque = self._external_torque()
        frictionloss = self._friction_budget(
            self.prev_torque, external_torque, stribeck
        )
        self.entity.set_dofs_frictionloss(frictionloss, self.dofs_idx_local)

        self.prev_torque = motor_torque
        return motor_torque
