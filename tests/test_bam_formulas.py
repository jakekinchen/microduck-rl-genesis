"""Les formules BAM portées doivent égaler celles de la bibliothèque de Rhoban.

Compare, sur 2000 tirages aléatoires, la loi de commande firmware, le couple
moteur et le budget de frottement m6 tels que ce dépôt les calcule, contre
`bam.actuator` / `bam.model` de référence.

Nécessite le dépôt BAM (branche mjlab_frictionloss) ; passer son chemin en
argument ou via BAM_REPO. Sans lui, le test est sauté.
"""
import sys, os, json

BAM_REPO = (
    sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BAM_REPO", "")
)
if not BAM_REPO or not os.path.isdir(BAM_REPO):
    print("SKIP — dépôt BAM absent (git clone -b mjlab_frictionloss "
          "https://github.com/Rhoban/bam.git puis BAM_REPO=<chemin>)")
    sys.exit(0)
sys.path.insert(0, BAM_REPO)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np, torch
from bam.model import load_model
from microduck.constants import (BAM_XL330_M6_JSON, BAM_KP_FW, XL330_ERROR_GAIN,
                                 XL330_MAX_PWM, XL330_MAX_CURRENT)

VIN = 7.35
m = load_model(BAM_XL330_M6_JSON)
m.actuator.kp = BAM_KP_FW
m.actuator.vin = VIN
p = json.load(open(BAM_XL330_M6_JSON))

rng = np.random.default_rng(0)
N = 2000
q = rng.uniform(-1.5, 1.5, N)
qt = q + rng.uniform(-0.5, 0.5, N)
dq = rng.uniform(-8.0, 8.0, N)
tau_m = rng.uniform(-0.6, 0.6, N)
tau_e = rng.uniform(-0.6, 0.6, N)

ref_v = np.array([m.actuator.compute_control(qt[i], q[i], dq[i], 0.005) for i in range(N)])
ref_t = np.array([m.actuator.compute_torque(ref_v[i], True, q[i], dq[i]) for i in range(N)])
ref_f = np.array([m.compute_frictions(tau_m[i], tau_e[i], dq[i])[0] for i in range(N)])

t = lambda x: torch.as_tensor(x, dtype=torch.float64)
kt, R = p["kt"], p["R"]
duty = (t(qt) - t(q)) * BAM_KP_FW * XL330_ERROR_GAIN
span = R * XL330_MAX_CURRENT / VIN
center = kt * t(dq) / VIN
duty = torch.clamp(torch.clamp(duty, center - span, center + span),
                   -XL330_MAX_PWM, XL330_MAX_PWM)
volts = VIN * duty
tau = kt * volts / R - (kt**2) * t(dq) / R

stri = torch.exp(-torch.pow(t(dq).abs() / p["dtheta_stribeck"], p["alpha"]))
mt, et = t(tau_m), t(tau_e)
fl = torch.full_like(mt, p["friction_base"]) + stri * p["friction_stribeck"]
fl += torch.abs(et * p["load_friction_external"] - mt * p["load_friction_motor"])
fl += stri * torch.abs(et * p["load_friction_external_stribeck"]
                       - mt * p["load_friction_motor_stribeck"])
drive = (mt.abs() > et.abs()).to(mt.dtype)
quad = (drive * p["load_friction_external_quad"] * et.abs() ** 2
        + (1 - drive) * p["load_friction_motor_quad"] * mt.abs() ** 2)
fl_mjlab = fl + stri * quad
# Version du papier : le terme quadratique n'est actif qu'à signes opposés.
gate = (torch.sign(et) != torch.sign(mt)).to(mt.dtype)
fl_paper = fl + stri * quad * gate


def cmp(name, a, b, tol):
    err = float(np.abs(np.asarray(a, float) - np.asarray(b, float)).max())
    print(f"{name:34s} écart max = {err:.3e}")
    assert err < tol, name
    return err


cmp("tension (loi firmware)", ref_v, volts.numpy(), 1e-12)
cmp("couple moteur (contre-FEM)", ref_t, tau.numpy(), 1e-12)
cmp("frottement m6 (version papier)", ref_f, fl_paper.numpy(), 1e-12)
d = float(np.abs(ref_f - fl_mjlab.numpy()).max())
rel = float((np.abs(ref_f - fl_mjlab.numpy()) / (np.abs(ref_f) + 1e-9)).max())
print(f"{'frottement m6 (version mjlab)':34s} écart max = {d:.3e} "
      f"({100*rel:.2f} % — garde enable_quadratic omise en amont, cf. README)")
assert rel < 0.02, "l'écart avec mjlab dépasse ce qui est documenté"
print("OK — formules BAM bit-exactes")
