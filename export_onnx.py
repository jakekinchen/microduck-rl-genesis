"""Export ONNX de la politique acteur, normaliseur d'observation CUIT DANS LE GRAPHE.

    python export_onnx.py -e microduck-velocity --ckpt 1000 -o policies/walk.onnx

INVARIANT (AGENTS.md du dépôt amont) : la normalisation d'observation est ACTIVE à
l'entraînement. Elle DOIT donc être intégrée à l'ONNX. En simulation le bug est
invisible — `play.py` applique le normaliseur de toute façon — mais sur le robot
la politique verrait des observations non normalisées. Ne jamais convertir un
checkpoint à la main : passer par ce script.

Entrée du graphe  : obs (1, 61), dans l'ordre de `constants.OBS_LAYOUT`.
Sortie du graphe  : action (1, 14), moyenne déterministe de la gaussienne, dans
                    l'ordre canonique des 14 servos.
"""

import argparse
import os
import pickle

import torch
import torch.nn as nn

import genesis as gs
from rsl_rl.runners import OnPolicyRunner

from microduck.constants import NUM_ACTIONS, NUM_OBS, OBS_LAYOUT
from microduck.velocity_env import MicroduckVelocityEnv


class ExportedPolicy(nn.Module):
    """Normaliseur + MLP en un seul module traçable, entrée/sortie tenseur nu."""

    def __init__(self, actor):
        super().__init__()
        self.mlp = actor.mlp
        norm = actor.obs_normalizer
        if hasattr(norm, "_mean"):
            self.register_buffer("mean", norm._mean.detach().clone())
            self.register_buffer("std", norm._std.detach().clone())
            self.eps = float(norm.eps)
        else:  # obs_normalization=False → identité
            self.register_buffer("mean", torch.zeros(1, NUM_OBS))
            self.register_buffer("std", torch.ones(1, NUM_OBS))
            self.eps = 0.0

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        x = (obs - self.mean) / (self.std + self.eps)
        # La gaussienne de rsl_rl porte son écart-type dans un paramètre à part
        # (`std_param`) : la sortie du MLP EST la moyenne, donc l'action
        # déterministe de déploiement. Le découpage est une ceinture de
        # sécurité si une future distribution ajoutait des sorties.
        return self.mlp(x)[..., :NUM_ACTIONS]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-e", "--exp-name", default="microduck-velocity")
    p.add_argument("--ckpt", type=int, default=-1)
    p.add_argument("-o", "--output", default="walk.onnx")
    args = p.parse_args()

    gs.init(backend=gs.cpu, logging_level="warning")
    log_dir = os.path.join("logs", args.exp_name)
    with open(os.path.join(log_dir, "cfgs.pkl"), "rb") as f:
        saved = pickle.load(f)

    # 1 env suffit : on ne veut que les poids.
    env = MicroduckVelocityEnv(num_envs=1, rough=saved["rough"], backlash=saved.get("backlash", False))
    runner = OnPolicyRunner(env, saved["train_cfg"], log_dir, device="cpu")
    if args.ckpt < 0:
        ckpts = [f for f in os.listdir(log_dir) if f.startswith("model_")]
        ckpt = max(ckpts, key=lambda f: int(f.split("_")[1].split(".")[0]))
    else:
        ckpt = f"model_{args.ckpt}.pt"
    runner.load(os.path.join(log_dir, ckpt))

    # rsl_rl 5.x expose l'acteur sous `alg.actor` ; `_raw_actor` est le modèle
    # non enveloppé (identique hors multi-GPU) — on le préfère quand il existe.
    actor = getattr(runner.alg, "_raw_actor", None) or runner.alg.actor
    exported = ExportedPolicy(actor).eval()

    dummy = torch.zeros(1, NUM_OBS)
    with torch.no_grad():
        ref = exported(dummy)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    torch.onnx.export(
        exported,
        dummy,
        args.output,
        input_names=["obs"],
        output_names=["action"],
        dynamic_axes={"obs": {0: "batch"}, "action": {0: "batch"}},
        opset_version=17,
    )
    # UN SEUL FICHIER, poids compris.
    #
    # L'exportateur récent de PyTorch écrit les poids à côté, dans un
    # `<nom>.onnx.data` : le `.onnx` ne fait alors que 2,6 Ko et **refuse de se
    # charger** si le second fichier n'est pas dans le même dossier (vérifié :
    # « External data path validation failed for initializer »). Sur un robot,
    # ça veut dire qu'une politique copiée à moitié échoue à l'exécution, pas
    # au moment de la copie. On réécrit donc l'ONNX en un fichier autoportant
    # et on supprime le fichier de poids devenu inutile.
    import onnx

    modele = onnx.load(args.output)  # tire les poids externes
    onnx.save_model(modele, args.output, save_as_external_data=False)
    externe = args.output + ".data"
    if os.path.exists(externe):
        os.remove(externe)

    taille = os.path.getsize(args.output) / 1e6
    print(f"écrit {args.output}  (obs {NUM_OBS} → action {NUM_ACTIONS}, "
          f"{taille:.2f} Mo, fichier unique)")
    print("découpe de l'observation :")
    off = 0
    for name, dim in OBS_LAYOUT:
        print(f"  [{off:2d}:{off + dim:2d}] {name}")
        off += dim

    # Vérification : l'ONNX doit rendre EXACTEMENT ce que rend le module torch.
    #
    # On NE teste PAS sur un vecteur nul seul. Une observation nulle est le pire
    # cas de test possible : tout ce qui est proportionnel à l'entrée disparaît,
    # donc une permutation d'articulations, un normaliseur oublié ou un poids
    # perdu peuvent passer inaperçus. On tire un lot aléatoire à l'échelle des
    # observations réelles (bruit centré réduit, l'entrée que voit le
    # normaliseur), on garde le vecteur nul comme cas limite, et on vérifie
    # aussi que le lot dynamique fonctionne — c'est ce que fera le robot.
    try:
        import numpy as np
        import onnxruntime as ort

        torch.manual_seed(0)
        probe = torch.cat([dummy, torch.randn(32, NUM_OBS)], dim=0)
        with torch.no_grad():
            ref_probe = exported(probe)

        sess = ort.InferenceSession(args.output, providers=["CPUExecutionProvider"])
        out = sess.run(None, {"obs": probe.numpy()})[0]
        err = float(np.abs(out - ref_probe.numpy()).max())
        # Seuil à 1e-4 rad, soit 0,006° sur une action qui vaut ~1 rad : cent
        # fois plus fin que tout ce qui a un sens physique sur un XL330, et
        # assez lâche pour ne pas faire échouer la chaîne sur du bruit float32
        # (mesuré ~6e-6 avec un lot aléatoire, contre ~1e-7 sur un vecteur nul
        # — l'écart grandit simplement parce que le test sollicite le réseau).
        print(f"contrôle onnxruntime : écart max {err:.3e} sur {probe.shape[0]} observations")
        assert err < 1e-4, f"l'ONNX diverge du module torch (écart {err:.3e})"

        # Une politique qui rend la même action quelle que soit l'observation
        # s'exporte sans erreur et se déploie en statue. Le cas arrive pour de
        # bon : checkpoint pris avant tout apprentissage, ou poids mal chargés.
        spread = float(out.std(axis=0).max())
        if spread < 1e-6:
            print(f"ATTENTION : actions insensibles à l'observation (écart-type {spread:.1e})")
    except ImportError:
        print("onnxruntime absent — contrôle numérique sauté")


if __name__ == "__main__":
    main()
