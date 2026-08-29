# Contrat de déploiement : ce que le robot doit recevoir

**Français** · [English](SIM2REAL.md)

Ce document décrit **exactement** ce qu'attend une politique exportée par
`export_onnx.py`. Il est le pendant du runtime embarqué de
[pollen-robotics/microduck](https://github.com/pollen-robotics/microduck) : une
politique entraînée ici respecte le même contrat que celles entraînées en amont,
donc elle s'y branche sans modification.

Tout ce qui suit est vérifiable dans le code : `microduck/constants.py` pour la
découpe, `microduck/velocity_env.py::_compute_observations` pour la construction.

## 1. Cadence

| | |
|---|---|
| Fréquence de contrôle | **50 Hz** (période 20 ms) |
| Pas physique en simulation | 5 ms, décimation 4 |
| Filtrage de l'action | **aucun** |

⚠️ **La politique n'est pas filtrée.** Aucun passe-bas n'est appliqué à l'action
pendant l'entraînement. En ajouter un côté runtime, ou en retirer un, casse le
transfert dans les deux sens.

## 2. Entrée : vecteur d'observation 61-D

Ordre **strict**. Toutes les grandeurs sont en unités SI, dans le repère du
tronc (« body frame ») sauf mention contraire.

| Indices | Nom | Dim | Contenu |
|---|---|---|---|
| `[0:3]` | `base_ang_vel` | 3 | vitesse angulaire du tronc, repère tronc, rad/s (gyroscope IMU) |
| `[3:6]` | `projected_gravity` | 3 | vecteur gravité **unitaire** projeté dans le repère tronc |
| `[6:20]` | `joint_pos` | 14 | position articulaire **relative à HOME**, rad |
| `[20:34]` | `joint_vel` | 14 | vitesse articulaire, rad/s |
| `[34:48]` | `actions` | 14 | action **précédente**, brute (avant mise à l'échelle) |
| `[48:51]` | `twist` | 3 | commande `[vx, vy, ωz]` en m/s, m/s, rad/s |
| `[51:55]` | `head_pose` | 4 | commande de pose de tête, deltas depuis HOME, rad |
| `[55:61]` | `body_pose` | 6 | commande de pose du tronc `[x, y, z, roll, pitch, yaw]` |

Les 48 premières dimensions sont la proprioception, les 13 dernières les
commandes. **Un slot de commande inutilisé se met à zéro, il ne se supprime
jamais** : c'est ce qui permet au runtime de permuter les politiques à chaud
derrière un buffer d'observation unique.

### Détails qui comptent

- **`projected_gravity`** est le vecteur `(0, 0, −1)` du monde exprimé dans le
  repère du tronc. Debout et à plat, il vaut `(0, 0, −1)`.
- **`joint_pos` est relative à HOME**, pas absolue. Soustraire
  `constants.DEFAULT_JOINT_POS` de la lecture encodeur.
- **`actions`** est l'action **brute** rendue par le réseau au pas précédent,
  pas la consigne articulaire qui en découle.
- Aucune mise à l'échelle par terme n'est appliquée à l'entrée : la
  normalisation est **cuite dans l'ONNX** (moyenne et écart-type empiriques
  appris pendant l'entraînement). Ne jamais convertir un checkpoint à la main.

## 3. Sortie : 14 actions

L'ONNX rend un vecteur de 14 valeurs, dans l'ordre canonique des servos :

```
0  left_hip_yaw     5  neck_pitch     9  right_hip_yaw
1  left_hip_roll    6  head_pitch    10  right_hip_roll
2  left_hip_pitch   7  head_yaw      11  right_hip_pitch
3  left_knee        8  head_roll     12  right_knee
4  left_ankle                        13  right_ankle
```

La consigne envoyée aux servos est :

```
q_target[i] = HOME[i] + action[i] * ACTION_SCALE      # ACTION_SCALE = 1.0
```

`HOME` est `constants.HOME_JOINT_POS` (pose STAND2 : tronc avancé de ~5 mm pour
que le centre de masse tombe sur l'axe de cheville).

C'est une consigne de **position**, envoyée au contrôleur de position du servo.
La simulation modélise ce contrôleur (loi de tension du firmware XL330, gain
`kp = 200`), elle ne le remplace pas.

## 4. Ce que la simulation a modélisé du robot réel

Si l'un de ces points ne correspond pas au robot cible, le transfert se dégrade :

| Élément | Valeur simulée |
|---|---|
| Servos | Dynamixel XL330, modèle BAM M6 ajusté sur banc |
| Gain firmware | `kp = 200` (raideur conservée du Microduck) |
| Tension d'alimentation | tirée par robot dans **6,5 – 8,2 V** |
| Chute de tension sous charge | `V = V₀ − R·I`, `R ∈ [0 ; 0,2] Ω`, plancher 6,0 V |
| Limite de courant firmware | 1,75 A |
| Retard de commande (bus) | 3 à 6 pas physiques = **15 à 30 ms** |
| Retard IMU | 0 à 1 pas de contrôle = 0 à 20 ms |
| Retard `joint_vel` | exactement 1 pas de contrôle (moyenne glissante du firmware) |
| Biais d'encodeur | ±0,015 rad (±0,86°), constant par robot |
| Jeu d'engrenage | ±1° par servo, encodeur lu à travers (avec `--backlash`) |
| Désalignement IMU | rotation d'axe aléatoire, ≤ 6° |
| Friction de semelle | ratio tiré dans 0,7 – 1,3 |
| Masse / inertie du tronc | ±5 % |
| Centre de masse tronc / tête | ±15 mm / ±10 mm (rampés par curriculum) |
| Poussées | ±0,3 m/s toutes les 3 à 6 s |

## 5. Limites connues

1. **Aucun essai sur robot réel n'a été fait depuis ce dépôt.** Le contrat est
   respecté et la physique est validée numériquement contre MuJoCo (voir le
   README, §7), mais ça ne remplace pas un déploiement.
2. **Le moteur de contact est Genesis, pas MuJoCo.** L'écart mesuré sur une
   seconde de marche est faible, mais non nul.
3. **Le jeu d'engrenage est modélisé, mais il faut l'activer.** `--backlash`
   entraîne sur le modèle où chaque servo porte ±1° de jeu en série, avec la
   boucle firmware ET les observations lues *à travers* le jeu (l'encodeur du
   vrai servo est du côté sortie). Sans ce drapeau, la simulation est plus
   optimiste que le robot réel sur la précision de position. Les dimensions
   d'observation et d'action sont identiques, donc le runtime ne voit aucune
   différence.
4. **Pas d'exteroception.** Proprioception seule : la politique ne peut pas
   éviter un obstacle qu'elle ne voit pas.

## 6. Vérifier un export

```bash
python export_onnx.py -e microduck-velocity -o walk.onnx
```

Le script affiche la découpe de l'observation et compare la sortie ONNX à celle
du module PyTorch sur un lot d'observations tirées au hasard (l'écart doit
rester < 1e-4 rad, soit 0,006°, cent fois plus fin que tout ce qui a un sens
sur un XL330). Il échoue si le normaliseur n'a pas été correctement intégré au
graphe, et avertit si la politique rend la même action quelle que soit
l'observation, ce qui arrive avec un point de contrôle pris trop tôt.

**Ce contrôle valide la conversion, pas le câblage.** Avant de mettre quoi que
ce soit sur le robot, lancer aussi :

```bash
python tests/test_onnx_deploy.py microduck-velocity
```

Celui-là déroule un vrai épisode et compare, à chaque pas, l'action de la
politique entraînée à celle que rend onnxruntime nourri de **la même
observation que celle assemblée par l'environnement**. C'est la seule
vérification qui attraperait :

- une permutation des 14 servos entre l'ordre d'entraînement et l'ordre exporté ;
- un normaliseur resté adaptatif au lieu d'être figé ;
- le mauvais groupe d'observation lu dans le `TensorDict` (l'acteur ne lit que
  `policy`, jamais `privileged`).

Aucune de ces trois erreurs ne lève d'exception. Elles ne se voient qu'au moment
où le robot tombe.

Mesuré sur la politique de marche : **4,8·10⁻⁷ rad** d'écart maximal sur 60 pas.
