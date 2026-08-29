"""Terrain accidenté du Microduck — champ de hauteurs + curriculum.

mjlab compose ses terrains avec des boîtes (`mjlab.terrains`) ; Genesis attend un
champ de hauteurs. On génère donc nous-mêmes la grille, ce qui a deux avantages
par rapport à laisser Genesis générer ses sous-terrains :

  - on garde le tableau numpy, donc la hauteur du sol sous un pied se lit par
    interpolation bilinéaire — c'est l'équivalent exact du `TerrainHeightSensor`
    amont (raycast vers le bas), sans lancer de rayon ;
  - on reproduit la disposition ligne = difficulté / colonne = variante, seule
    façon d'implémenter le curriculum `terrain_levels_vel`.

Les paramètres sont ceux de `MICRODUCK_ROUGH_TERRAINS_CFG` amont, transposés à
des parcelles plus petites (le Microduck plafonne à 0,4 m/s : sur 20 s il
parcourt ~8 m, une parcelle de 8 m était surdimensionnée). Les AMPLITUDES
verticales, elles, sont conservées à l'identique — c'est ce qui compte : le
robot ne lève le pied que de 1 à 2 cm, donc marches ≤ 1,5 cm et bosses ≤ 1 cm.

Taille de la grille : Genesis construit une SDF sur tout le terrain. 10×10
parcelles de 3 m à 5 cm de maille (0,44 M cellules) se compilent en ~30 s ;
la grille 10×20 de 4 m que mjlab utilise (2,2 M cellules) ne finissait pas en
5 minutes. Ce n'est pas une perte : les envs Genesis sont des mondes
INDÉPENDANTS partageant la même géométrie statique, donc la variété vient du
placement des origines, pas de la taille du terrain.
"""

from __future__ import annotations

import numpy as np

# Proportions amont : plat 25 %, escaliers 25 %, damier 30 %, pente 20 %.
SUB_TERRAIN_PROPORTIONS: tuple[tuple[str, float], ...] = (
    ("flat", 0.25),
    ("pyramid_stairs", 0.25),
    ("random_grid", 0.30),
    ("pyramid_slope", 0.20),
)


def _flat(h: np.ndarray, difficulty: float, hs: float, rng) -> None:
    pass


def _pyramid_stairs(h: np.ndarray, difficulty: float, hs: float, rng) -> None:
    """Escalier pyramidal, marche 0 → 1,5 cm selon la difficulté.

    Plateforme au SOMMET (pas de fosse) : une pyramide inversée place l'origine
    de l'env au fond du trou, et le robot est alors réinitialisé sous le sol —
    c'est pour ça que l'amont a retiré la variante inversée.
    """
    step_h = 0.015 * difficulty
    step_w = max(int(round(0.15 / hs)), 1)
    platform = max(int(round(1.2 / hs)), 1)
    n = min(h.shape)
    level = 0.0
    i = 0
    while n - 2 * i > platform:
        level += step_h
        i += step_w
        h[i : h.shape[0] - i, i : h.shape[1] - i] = level


def _random_grid(h: np.ndarray, difficulty: float, hs: float, rng) -> None:
    """Damier de cellules à hauteur aléatoire (pavés), 0 → 1 cm.

    `grid_width` doit rester grossier : à 0,12 m une parcelle de 8 m faisait
    4 356 boîtes côté mjlab et saturait la mémoire. Ici c'est un champ de
    hauteurs donc le coût est nul, mais on garde la maille large parce que c'est
    elle qui a été validée — des cellules plus fines que le pied changent la
    nature du sol.
    """
    amp = 0.010 * difficulty
    cell = max(int(round(0.45 / hs)), 1)
    platform = max(int(round(1.5 / hs)), 1)
    nx, ny = h.shape
    for i in range(0, nx, cell):
        for j in range(0, ny, cell):
            h[i : i + cell, j : j + cell] = rng.uniform(0.0, amp)
    # Plateforme plate au centre : le robot y est réinitialisé debout.
    cx, cy = nx // 2, ny // 2
    p = platform // 2
    h[cx - p : cx + p, cy - p : cy + p] = 0.0


def _pyramid_slope(h: np.ndarray, difficulty: float, hs: float, rng) -> None:
    """Pente pyramidale douce ; slope_range 0,03 → 0,10 (soit 1,7° → 5,7°).

    Petit robot, petites pentes. Le pas vertical est fin (1 mm côté amont) pour
    qu'une pente douce reste lisse au lieu d'être un escalier de ressauts.
    """
    slope = 0.03 + (0.10 - 0.03) * difficulty
    platform = 1.2
    nx, ny = h.shape
    x = (np.arange(nx) - (nx - 1) / 2.0) * hs
    y = (np.arange(ny) - (ny - 1) / 2.0) * hs
    dist = np.maximum(np.abs(x)[:, None], np.abs(y)[None, :])
    rise = np.clip(dist - platform / 2.0, 0.0, None) * slope
    h[:] = rise.max() - rise  # plateforme EN HAUT (cf. _pyramid_stairs)


_GENERATORS = {
    "flat": _flat,
    "pyramid_stairs": _pyramid_stairs,
    "random_grid": _random_grid,
    "pyramid_slope": _pyramid_slope,
}


class RoughTerrain:
    """Grille de parcelles : lignes = difficulté, colonnes = variante.

    Expose le champ de hauteurs pour Genesis (`height_field`, en unités de
    `vertical_scale`) et la hauteur du sol en tout point (`height_at`).
    """

    # Seul ce terrain porte un curriculum : ses parcelles sont rangées par
    # difficulté croissante, et le curriculum fait monter ou descendre chaque
    # env d'une ligne. Un sol plat ou un parcours de démonstration n'ont pas de
    # niveaux — d'où ce drapeau plutôt qu'un test sur le type.
    has_curriculum = True

    def __init__(
        self,
        num_rows: int = 10,
        num_cols: int = 10,
        patch_size: float = 3.0,
        horizontal_scale: float = 0.05,
        vertical_scale: float = 0.001,
        border: float = 1.5,
        seed: int = 0,
    ):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.patch_size = patch_size
        self.hs = horizontal_scale
        self.vs = vertical_scale
        rng = np.random.default_rng(seed)

        # Répartition des colonnes selon les proportions amont.
        types: list[str] = []
        for name, prop in SUB_TERRAIN_PROPORTIONS:
            types += [name] * max(int(round(prop * num_cols)), 1)
        types = (types * num_cols)[:num_cols]
        self.col_types = types

        n_patch = int(round(patch_size / self.hs))
        n_border = int(round(border / self.hs))
        self.n_patch = n_patch
        self.n_border = n_border

        nx = num_rows * n_patch + 2 * n_border
        ny = num_cols * n_patch + 2 * n_border
        field = np.zeros((nx, ny), dtype=np.float64)

        # Origine de chaque parcelle, en mètres, repère monde (centré en 0).
        self.origins = np.zeros((num_rows, num_cols, 3), dtype=np.float64)
        self.x0 = -(nx * self.hs) / 2.0
        self.y0 = -(ny * self.hs) / 2.0

        for r in range(num_rows):
            # Difficulté linéaire sur les lignes ; ligne 0 = plat quasi partout.
            difficulty = r / max(num_rows - 1, 1)
            for c in range(num_cols):
                i0 = n_border + r * n_patch
                j0 = n_border + c * n_patch
                patch = np.zeros((n_patch, n_patch), dtype=np.float64)
                _GENERATORS[types[c]](patch, difficulty, self.hs, rng)
                field[i0 : i0 + n_patch, j0 : j0 + n_patch] = patch
                ci, cj = i0 + n_patch // 2, j0 + n_patch // 2
                self.origins[r, c, 0] = self.x0 + ci * self.hs
                self.origins[r, c, 1] = self.y0 + cj * self.hs
                self.origins[r, c, 2] = field[ci, cj]

        self.height_m = field
        # Genesis attend le champ en unités entières de vertical_scale.
        self.height_field = np.round(field / self.vs).astype(np.int16)
        # Relecture après quantification : `height_at` doit rendre la hauteur
        # RÉELLEMENT simulée, pas la hauteur théorique.
        self.height_m = self.height_field.astype(np.float64) * self.vs
        for r in range(num_rows):
            for c in range(num_cols):
                ci = int(round((self.origins[r, c, 0] - self.x0) / self.hs))
                cj = int(round((self.origins[r, c, 1] - self.y0) / self.hs))
                self.origins[r, c, 2] = self.height_m[ci, cj]

        self.extent_x = nx * self.hs
        self.extent_y = ny * self.hs

    # -- requête de hauteur ---------------------------------------------------

    def height_at(self, xy):
        """Hauteur du sol (m) sous des points XY monde, par bilinéaire.

        `xy` : tenseur torch (..., 2). Retourne un tenseur de même device et de
        forme (...). Remplace le raycast `TerrainHeightSensor` de mjlab.
        """
        import torch

        if not hasattr(self, "_hm_t") or self._hm_t.device != xy.device:
            self._hm_t = torch.as_tensor(
                self.height_m, dtype=torch.float32, device=xy.device
            )
        hm = self._hm_t
        nx, ny = hm.shape
        fx = (xy[..., 0] - self.x0) / self.hs
        fy = (xy[..., 1] - self.y0) / self.hs
        i0 = fx.floor().clamp(0, nx - 2).long()
        j0 = fy.floor().clamp(0, ny - 2).long()
        tx = (fx - i0).clamp(0.0, 1.0)
        ty = (fy - j0).clamp(0.0, 1.0)
        h00 = hm[i0, j0]
        h10 = hm[i0 + 1, j0]
        h01 = hm[i0, j0 + 1]
        h11 = hm[i0 + 1, j0 + 1]
        return (
            h00 * (1 - tx) * (1 - ty)
            + h10 * tx * (1 - ty)
            + h01 * (1 - tx) * ty
            + h11 * tx * ty
        )


class FlatTerrain:
    """Sol plan : hauteur nulle partout. Interface identique à RoughTerrain."""

    has_curriculum = False
    num_rows = 1
    num_cols = 1
    patch_size = 0.0

    def height_at(self, xy):
        import torch

        return torch.zeros(xy.shape[:-1], dtype=torch.float32, device=xy.device)
