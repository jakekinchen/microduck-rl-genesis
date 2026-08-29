"""L'ONNX exporté rejoue-t-il la politique sur de VRAIES observations ?

C'est le test de la chaîne de déploiement complète, et le seul qui adresse
directement la question « ce que j'entraîne dans Genesis, je peux le mettre sur
le robot ». `export_onnx.py` compare déjà l'ONNX au module torch, mais sur des
observations tirées au hasard : il valide la conversion, pas le câblage.

Ici on ferme la boucle. On déroule un épisode dans l'environnement et, à chaque
pas, on compare :

    politique torque (celle qui a appris)   ⟷   session onnxruntime (celle qui
                                                 partira sur le robot)

nourries de la MÊME observation, celle que l'environnement vient de produire.
Ce test attrape ce que les autres laissent passer :

  • un groupe d'observation mal extrait du TensorDict (l'acteur lit « policy »,
    pas « privileged ») ;
  • un normaliseur non figé, qui continuerait de s'adapter à l'inférence ;
  • une permutation des 14 articulations entre l'ordre d'entraînement et
    l'ordre exporté ;
  • des observations réelles hors de la plage vue par le normaliseur.

Sans checkpoint disponible, le test se déclare non applicable plutôt que
d'échouer : il doit pouvoir tourner sur un dépôt fraîchement cloné.
"""

import os
import pickle
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import genesis as gs  # noqa: E402

from export_onnx import ExportedPolicy  # noqa: E402
from microduck.constants import NUM_ACTIONS, NUM_OBS  # noqa: E402

STEPS = 60
TOL = 1e-4          # rad ; cf. le seuil de export_onnx.py


def main() -> int:
    exp = sys.argv[1] if len(sys.argv) > 1 else "microduck-velocity"
    log_dir = os.path.join("logs", exp)
    if not os.path.isdir(log_dir) or not any(
        f.startswith("model_") for f in os.listdir(log_dir)
    ):
        print(f"aucun checkpoint dans {log_dir} — test non applicable")
        return 0

    try:
        import onnxruntime as ort
    except ImportError:
        print("onnxruntime absent — test non applicable")
        return 0

    from rsl_rl.runners import OnPolicyRunner

    from microduck.velocity_env import MicroduckVelocityEnv

    gs.init(backend=gs.cpu, logging_level="warning")
    with open(os.path.join(log_dir, "cfgs.pkl"), "rb") as f:
        saved = pickle.load(f)

    env = MicroduckVelocityEnv(
        num_envs=1, rough=saved["rough"], backlash=saved.get("backlash", False)
    )
    runner = OnPolicyRunner(env, saved["train_cfg"], log_dir, device="cpu")
    ckpt = max(
        (f for f in os.listdir(log_dir) if f.startswith("model_")),
        key=lambda f: int(f.split("_")[1].split(".")[0]),
    )
    runner.load(os.path.join(log_dir, ckpt))
    print(f"checkpoint : {ckpt}")

    actor = getattr(runner.alg, "_raw_actor", None) or runner.alg.actor
    exported = ExportedPolicy(actor).eval()

    tmp = os.path.join(
        os.environ.get("TMPDIR", "/tmp"), f"_deploy_{os.getpid()}.onnx"
    )
    torch.onnx.export(
        exported, torch.zeros(1, NUM_OBS), tmp,
        input_names=["obs"], output_names=["action"],
        dynamic_axes={"obs": {0: "batch"}, "action": {0: "batch"}},
        opset_version=17,
    )
    sess = ort.InferenceSession(tmp, providers=["CPUExecutionProvider"])

    policy = runner.get_inference_policy(device="cpu")
    obs = env.reset()
    if isinstance(obs, tuple):
        obs = obs[0]

    worst = 0.0
    seen = []
    with torch.no_grad():
        for _ in range(STEPS):
            # L'acteur ne lit QUE le groupe « policy » : c'est exactement le
            # vecteur que le robot assemblera. S'il en lisait un autre,
            # l'ONNX serait inutilisable et c'est ici qu'on le verrait.
            vec = obs["policy"]
            assert vec.shape[-1] == NUM_OBS, f"obs acteur {vec.shape} ≠ {NUM_OBS}"

            act_torch = policy(obs)
            act_onnx = sess.run(None, {"obs": vec.cpu().numpy()})[0]
            assert act_onnx.shape[-1] == NUM_ACTIONS

            worst = max(worst, float(np.abs(act_onnx - act_torch.cpu().numpy()).max()))
            seen.append(vec.cpu().numpy().copy())
            obs = env.step(act_torch)[0]

    os.remove(tmp)
    seen = np.concatenate(seen, axis=0)

    print(f"écart max torch ↔ onnx sur {STEPS} pas d'un épisode réel : {worst:.3e} rad")
    print(f"amplitude des observations vues : [{seen.min():+.2f}, {seen.max():+.2f}]")

    ok = True
    if worst >= TOL:
        print(f"ÉCHEC : écart {worst:.3e} ≥ {TOL:.0e}")
        ok = False

    # Une politique figée rendrait le même geste quoi qu'il arrive : elle
    # passerait la comparaison ci-dessus tout en étant inexploitable.
    bougé = float(seen.std(axis=0).max())
    if bougé < 1e-3:
        print(f"ÉCHEC : les observations ne varient pas (écart-type {bougé:.1e})")
        ok = False

    print("OK" if ok else "ÉCHEC")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
