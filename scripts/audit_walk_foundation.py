"""Bounded nominal model/feedback diagnostic before another walking intervention."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    import genesis as gs
    import torch
    import numpy as np
    import mujoco
    from microduck.velocity_env import MicroduckVelocityEnv
    from microduck.constants import MICRODUCK_WALK_XML, JOINT_NAMES
    from evaluator.core import EvaluatorCore
    from experiments.laser.gait import GaitProbe
    from scripts.evaluate_laser import digest
    torch.set_num_threads(1)
    gs.init(backend=gs.cpu, logging_level="warning", seed=26090510)
    env = MicroduckVelocityEnv(1, demo=True)
    core = EvaluatorCore(a.policy, ROOT/".workspace/bam", "microduck.walking.v1")
    probe = GaitProbe(core)
    model = mujoco.MjModel.from_xml_path(MICRODUCK_WALK_XML)
    inertials = []
    for link in env.robot.links:
        try:
            body = model.body(link.name)
        except KeyError:
            continue
        inertials.append({"body": link.name, "genesis_mass": float(link.inertial_mass),
                         "mujoco_mass": float(body.mass[0]),
                         "genesis_inertia": np.asarray(link.inertial_i).tolist(),
                         "mujoco_principal_inertia": body.inertia.tolist()})
    result = {"policy_sha256": digest(a.policy), "inertials": inertials,
              "genesis_total_mass": sum(float(l.inertial_mass) for l in env.robot.links),
              "mujoco_total_mass": float(model.body_mass.sum()), "cases": []}
    for name, command, seconds in (("zero", [0.,0.,0.], 3), ("forward", [.12,0.,0.], 10), ("turn", [0.,0.,.5], 10)):
        env.reset(); env.set_twist(*command); obs = env.place([0.,0.,.125], yaw=0)
        rows = []
        for i in range(seconds*50):
            action, _ = core.policy.infer(obs["policy"].cpu().numpy())
            if name == "zero": action[:] = 0
            obs, _, done, _ = env.step(torch.from_numpy(action).to(env.device))
            root = env.base_pos[0].cpu().numpy()
            q = env.dof_pos[0].cpu().numpy()
            core.data.qpos[:3] = root
            core.data.qpos[3:7] = env.base_quat[0].cpu().numpy()
            core.data.qpos[core.qpos_indices] = q
            core.data.qvel[:] = 0
            mujoco.mj_forward(core.model, core.data)
            clear = []
            for geom, vertices in zip(probe.feet, probe.vertices):
                world = vertices @ core.data.geom_xmat[geom].reshape(3,3).T + core.data.geom_xpos[geom]
                clear.append(float(world[:,2].min()))
            rows.append({"time_s": (i+1)*.02, "root": root.tolist(), "q": q.tolist(),
                         "foot_site_m": env.foot_height[0].cpu().tolist(), "sole_min_m": clear,
                         "load_z_n": env.foot_contact_force[0,:,2].cpu().tolist(),
                         "air_time_s": env.feet_air_time[0].cpu().tolist(),
                         "body_velocity": env.base_lin_vel[0].cpu().tolist(),
                         "angular_velocity": env.base_ang_vel[0].cpu().tolist(),
                         "action": action[0].tolist()})
            if bool(done.any()): break
        (a.output/f"{name}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in rows))
        stable = rows[50:]
        result["cases"].append({"case": name, "duration_s": rows[-1]["time_s"],
            "max_sole_clearance": np.max([r["sole_min_m"] for r in stable],axis=0).tolist(),
            "max_site_height": np.max([r["foot_site_m"] for r in stable],axis=0).tolist(),
            "max_air_s": np.max([r["air_time_s"] for r in stable],axis=0).tolist(),
            "mean_v": np.mean([r["body_velocity"] for r in stable],axis=0).tolist(),
            "mean_w": np.mean([r["angular_velocity"] for r in stable],axis=0).tolist(),
            "mean_joint_delta": (np.mean([r["q"] for r in stable],axis=0)-np.array(env.default_dof_pos.cpu())).tolist(),
            "minimum_root_height": min(r["root"][2] for r in rows)})
        print(json.dumps(result["cases"][-1]), flush=True)
    (a.output/"audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("inertials","cases")}),flush=True)


if __name__ == "__main__": main()
