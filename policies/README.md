# Politiques exportées

Fichiers ONNX prêts à être chargés par le runtime embarqué du Microduck.

| Fichier | Tâche | Entraîné sur | Itérations | Durée d'épisode atteinte |
|---|---|---|---|---|
| `velocity.onnx` | marche | sol plat | 3000 | 944 / 1000 pas |
| `rough.onnx` | marche | terrain accidenté (repris de la marche) | +1200 | 962 / 1000 pas |
| `backlash.onnx` | marche | sol plat, ±1° de jeu par servo (repris) | +1200 | 961 / 1000 pas |

Chaque fichier respecte le contrat décrit dans [`../SIM2REAL.md`](../SIM2REAL.md) :
entrée `obs` de 61 dimensions, sortie `action` de 14, normaliseur d'observation
**cuit dans le graphe**. Cadence de contrôle : 50 Hz.

## Un fichier, et un seul

Chaque `.onnx` est **autoportant** : les poids sont dedans (~790 Ko). Il n'y a
rien d'autre à copier sur le robot.

Ce n'est pas gratuit. L'exportateur récent de PyTorch écrit par défaut les poids
dans un fichier voisin `<nom>.onnx.data`, et le `.onnx` ne fait alors que 2,6 Ko.
Un tel fichier copié seul **échoue au chargement**, pas à la copie :

```
FAIL : External data path validation failed for initializer: mlp.0.bias
```

Sur un robot, cette erreur arrive au démarrage du contrôleur, loin de la
manipulation qui l'a causée. `export_onnx.py` réécrit donc l'ONNX en un seul
fichier et supprime le fichier de poids. Vérifié : les trois politiques se
chargent depuis un dossier vide, hors de leur emplacement d'origine.

## Régénérer

```bash
python export_onnx.py -e microduck-velocity -o policies/velocity.onnx
python export_onnx.py -e microduck-rough    -o policies/rough.onnx
python export_onnx.py -e microduck-backlash -o policies/backlash.onnx
```

Le script compare la sortie ONNX au module PyTorch sur un lot d'observations
aléatoires (écart attendu < 1e-4 rad, soit 0,006°), refuse un export dont le
normaliseur ne serait pas intégré au graphe, et avertit si la politique rend la
même action quelle que soit l'observation.

Pour vérifier la chaîne de déploiement **complète** — l'ONNX rejoué sur de
vraies observations d'épisode — voir `tests/test_onnx_deploy.py`, décrit dans
[`../SIM2REAL.md`](../SIM2REAL.md).

> Aucune de ces politiques n'a été essayée sur un robot physique.
