# Licence des fichiers de ce dossier : CC BY-SA-NC, PAS Apache 2.0

> Le reste du dépôt est sous Apache 2.0. **Ce dossier ne l'est pas.**

Les MJCF et les 47 maillages STL du Microduck présents ici proviennent de
[pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl),
dont le README indique :

> *3D model files are licensed under Creative Commons BY-SA-NC.*

## Ce que ça implique concrètement

| Clause | Conséquence |
|---|---|
| **BY**, attribution | Créditer **Pollen Robotics** partout où ces modèles sont redistribués ou affichés. |
| **SA**, partage à l'identique | Toute œuvre dérivée de ces modèles (MJCF modifié, maillage retravaillé) reste sous CC BY-SA-NC. |
| **NC**, non commercial | L'usage ne doit pas être **principalement destiné à un avantage commercial**. |

La clause **NC** est celle qui demande de la vigilance. Publier ce dépôt et des
vidéos de recherche n'est pas un usage commercial. En revanche, se servir de ces
modèles, ou d'images qui les montrent, comme support de promotion d'une
activité commerciale sort du cadre de la licence. En cas de doute sur un usage
donné, la voie sûre est de demander une autorisation à Pollen Robotics.

## Fichiers concernés

Tout ce dossier, à l'exception de :

- `xl330_m6.json` : paramètres d'actionneur identifiés, issus de
  [Rhoban/bam](https://github.com/Rhoban/bam) (Apache 2.0) ;
- `microduck/add_backlash.py` : script de transformation MJCF, Apache 2.0.

## Ce que ce dépôt n'a pas modifié

Les maillages sont repris **tels quels**. Les seules transformations appliquées
au robot sont faites à l'exécution (jeu d'engrenage inséré dans le MJCF par
`add_backlash.py`), pas sur les fichiers 3D eux-mêmes.
