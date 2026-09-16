"""V29 correction-headroom heading on the exposed V24 endurance/terrain bank."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest
from scripts.evaluate_walking_physical_development import SOURCES as PRIOR, WALK_SHA, STAND_SHA, validate_regressions

SUITE=ROOT/"experiments/walking/heading-persistence-v24.json"
FREEZE=ROOT/"experiments/walking/heading-headroom-endurance-freeze-v29.json"
from scripts.evaluate_walking_terrain_endurance import SOURCES as V23_SOURCES
SOURCES=list(dict.fromkeys(V23_SOURCES+[
    "scripts/evaluate_walking_heading_persistence.py", "microduck/persistent_heading_servo_v24.py",
    "tests/test_persistent_heading_v24.py", "experiments/walking/heading-persistence-v24.json",
    "experiments/walking/HEADING-PERSISTENCE-v24.md", "scripts/audit_v23_session_heading.py"]))

SOURCES=list(dict.fromkeys(SOURCES+['microduck/motion_heading_servo_v28.py', 'tests/test_motion_heading_v28.py', 'experiments/walking/MOTION-HEADING-v28.md', 'scripts/evaluate_motion_heading_endurance_v28.py']))

SOURCES=list(dict.fromkeys(SOURCES+['microduck/heading_headroom_v29.py', 'tests/test_heading_headroom_v29.py', 'experiments/walking/HEADING-HEADROOM-v29.md', 'scripts/evaluate_motion_heading_endurance_v28.py', 'scripts/evaluate_heading_headroom_endurance_v29.py']))


def verify_sources(frozen):
    for name,sha in frozen["source_sha256"].items():
        if digest(ROOT/name)!=sha: raise ValueError(f"frozen source drift: {name}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--freeze",action="store_true")
    p.add_argument("--bank",choices=("diagnostic",))
    p.add_argument("--output",type=Path)
    p.add_argument("--video",action="store_true")
    a=p.parse_args()
    validate_regressions()
    if a.freeze:
        with FREEZE.open("x") as f:
            json.dump({"schema":"microduck.terrain-endurance-freeze/v1",
                       "created_at":datetime.now(timezone.utc).isoformat(),
                       "walking_checkpoint_sha256":WALK_SHA,"standing_checkpoint_sha256":STAND_SHA,
                       "held_out":False,"source_sha256":{name:digest(ROOT/name) for name in SOURCES}},f,indent=2)
            f.write("\n")
        return
    if not a.bank or a.output is None: p.error("bank and fresh output required")
    frozen=json.loads(FREEZE.read_text())
    verify_sources(frozen)
    import numpy as np
    import torch
    import imageio.v2 as imageio
    from PIL import Image,ImageDraw
    from scripts.export_walking import export_walking
    from experiments.walking.terrain_v23 import TerrainWorld,TerrainGaitProbe,materialize_terrain
    from experiments.walking.self_load import record_self_loads,evaluate_self_load
    from experiments.walking.self_contact import SelfContactProbe,evaluate_self_contact
    from experiments.walking.posture import evaluate_case
    from experiments.walking.endurance_v23 import evaluate_endurance
    from scripts.audit_v23_session_heading import audit
    from microduck.heading_headroom_v29 import HeadingHeadroomServo
    torch.set_num_threads(1)
    suite=json.loads(SUITE.read_text())
    sessions=[s for s in suite["sessions"] if s["bank"]==a.bank]
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"standing").mkdir()
    walk,wp,walk_export=export_walking("walking-20260906-v21",a.output)
    stand,sp,stand_export=export_walking("standing-20260906-v15",a.output/"standing")
    for path,sha in ((a.output/"training.json",WALK_SHA),(a.output/"standing/training.json",STAND_SHA)):
        if json.loads(path.read_text())["checkpoint_sha256"]!=sha: raise ValueError("frozen actor identity mismatch")
    for source in SOURCES:
        dest=a.output/"evaluator-source"/source
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/source,dest)
    shutil.copy2(SUITE,a.output/"suite.json")
    shutil.copy2(FREEZE,a.output/"evaluator-freeze.json")
    reports,session_reports,errors=[],[],{"walking":0.,"standing":0.}
    model_dir=ROOT/"experiments/walking/models/contact-v11"
    geometry=SelfContactProbe(model_dir/"scene.xml")
    exception=None
    try:
        with (a.output/"trajectory.jsonl").open("w") as stream:
            for session in sessions:
                scene=materialize_terrain(a.output/"terrain-models"/session["id"],session["terrain"])
                world=TerrainWorld(walk,ROOT/".workspace/bam",standing_policy=stand,model_directory=model_dir,
                    terrain_scene=scene,domain=session["domain"],motor_ticks=suite["motor_ticks"],sensor_ticks=suite["sensor_ticks"],
                    yaw=session["yaw"],seed=session["seed"],render=a.video)
                world.heading_servo = HeadingHeadroomServo()
                full_rows = []
                probe=TerrainGaitProbe(world.core)
                session_cases=[]
                raised_samples=0
                try:
                    with record_self_loads(world) as loads:
                        offset=0.
                        for index,window in enumerate(session["windows"]):
                            name=f'{session["id"]}--window-{index+1}'
                            rows,actions=[],[]
                            writer=imageio.get_writer(a.output/f"{name}.mp4",fps=25,codec="libx264",quality=7) if a.video else None
                            try:
                                for i in range(round(window["duration_s"]*50)):
                                    if world.fell: break
                                    command=window["command"] if window["move_start_s"]<=i*.02<window["stop_start_s"] else [0,0,0]
                                    row=probe.sample(world.step_command(command))
                                    role=row["actor_mode"]
                                    row.update(case_id=name,session_id=session["id"],session_time_s=row["time_s"],time_s=(i+1)*.02,
                                        actor_observation=world.last_observation[0].tolist(),
                                        self_load_physics=[{**s,"interval_start_s":i*.02+j*.005} for j,s in enumerate(loads[-4:])])
                                    np.testing.assert_allclose(world.core.data.time,offset+row["time_s"],rtol=0,atol=1e-7)
                                    np.testing.assert_array_equal(np.asarray(row["command"],np.float32),np.asarray(command,np.float32))
                                    with torch.no_grad():
                                        expected=(stand_export if role=="standing" else walk_export)(torch.from_numpy(world.last_observation)).numpy()[0]
                                    error=float(abs(expected-world.last_action).max())
                                    if not np.isfinite(error) or error>=1e-4: raise ValueError("actual observation actor parity failed")
                                    errors[role]=max(errors[role],error)
                                    raised_samples+=sum(c["ground"].startswith("terrain_") and c["normal_n"]>1 for c in row["terrain_contacts"])
                                    rows.append(row)
                                    full_rows.append(row)
                                    actions.append(world.last_action.copy())
                                    stream.write(json.dumps(row)+"\n")
                                    if writer and i%2==0:
                                        frame=Image.fromarray(world.walking_frame())
                                        draw=ImageDraw.Draw(frame)
                                        draw.rectangle((0,0,720,38),fill=(15,20,30))
                                        draw.text((8,8),f'V29 | {name} | {row["session_time_s"]:.2f}s | {role}',fill="white")
                                        writer.append_data(np.asarray(frame))
                                np.save(a.output/f"{name}-actions-float32.npy",np.asarray(actions,np.float32).reshape(-1,14))
                                if not rows:
                                    report={"passed":False,"failures":["not_run_after_terminal_fall"],"metrics":{}}
                                else:
                                    scoring={**suite,**window}
                                    try:
                                        report=evaluate_case(rows,{"id":name,"command":window["command"]},scoring)
                                    except (ValueError, IndexError) as invalid:
                                        report={"passed":False,"failures":["missing_or_invalid_case_evidence:"+str(invalid)],"metrics":{}}
                                    report.update(self_contact=evaluate_self_contact(rows,geometry,round(window["duration_s"]*50)),
                                        self_load=evaluate_self_load([s for row in rows for s in row["self_load_physics"]],window["duration_s"]),
                                        endurance=evaluate_endurance(rows,window,suite["thresholds"]))
                                    for key in ("self_contact","self_load","endurance"):
                                        report["failures"] += [key+":"+f for f in report[key]["failures"]]
                                    report["passed"]=not report["failures"]
                                report.update(case_id=name,session_id=session["id"],bucket=session["bucket"],window_start_s=offset,
                                              observed_duration_s=len(rows)*.02,required_duration_s=window["duration_s"])
                                reports.append(report)
                                session_cases.append(report)
                                (a.output/"progress.json").write_text(json.dumps({"case_reports":reports},indent=2)+"\n")
                                print(json.dumps({"case":name,"passed":report["passed"],"failures":report["failures"],"duration_s":len(rows)*.02}),flush=True)
                                offset+=window["duration_s"]
                            finally:
                                if writer: writer.close()
                        duration=sum(w["duration_s"] for w in session["windows"])
                        continuity=evaluate_self_load(loads,duration)
                        exposure=raised_samples>=10 if session["terrain"]["kind"] in ("seams","tiles") else True
                        try:
                            heading = audit(full_rows, duration)
                        except (ValueError, AssertionError) as exc:
                            heading = {"passed":False, "failure":str(exc)}
                        session_reports.append({"session_id":session["id"],"bucket":session["bucket"],
                            "passed":all(r["passed"] for r in session_cases) and continuity["passed"] and exposure and heading["passed"],
                            "whole_session_heading":heading,
                            "failures":(["session_heading_failure"] if not heading["passed"] else [])+(["window_failure"] if not all(r["passed"] for r in session_cases) else [])+
                                       (["terrain_not_encountered"] if not exposure else [])+continuity["failures"],
                            "full_session_internal_load":continuity,"raised_surface_loaded_contact_samples":raised_samples,
                            "materialized_domain":world.materialized_domain,"materialized_terrain":world.materialized_terrain,
                            "simulated_duration_s":float(world.core.data.time),"required_duration_s":duration,
                            "independent_world":True,"resets_within_session":0})
                finally: world.close()
        verify_sources(frozen)
    except Exception as exc:
        exception=f"{type(exc).__name__}: {exc}"
        raise
    finally:
        buckets=defaultdict(lambda:{"passed":0,"total":0})
        for session in sessions:
            buckets[session["bucket"]]["total"]+=1
        for report in session_reports:
            buckets[report["bucket"]]["passed"]+=int(report["passed"])
        result={"schema":"microduck.terrain-endurance-result/v1","bank":a.bank,"proof_class":"visible_development",
                "held_out":False,"complete":exception is None and len(session_reports)==len(sessions),"exception":exception,
                "passed_sessions":sum(s["passed"] for s in session_reports),"total_sessions":len(sessions),
                "passed_windows":sum(r["passed"] for r in reports),"total_windows":sum(len(s["windows"]) for s in sessions),
                "buckets":dict(buckets),"session_reports":session_reports,"case_reports":reports,
                "max_real_observation_action_error_rad":errors,"export_parity":{"walking":wp,"standing":sp},
                "policy_sha256":digest(walk),"standing_policy_sha256":digest(stand),"evaluator_freeze_sha256":digest(FREEZE),
                "physical_transfer_validated":False,"measurement_calibrated":False,"reserved_opened":False,
                "boundary":suite["claim_boundary"]}
        (a.output/"probe.json").write_text(json.dumps(result,indent=2)+"\n")
        (a.output/"SHA256SUMS").write_text("".join(f"{digest(f)}  {f.relative_to(a.output)}\n" for f in sorted(a.output.rglob("*")) if f.is_file() and f.name!="SHA256SUMS"))
        print(json.dumps({"passed_sessions":result["passed_sessions"],"total_sessions":result["total_sessions"],"exception":exception}),flush=True)


if __name__=="__main__": main()
