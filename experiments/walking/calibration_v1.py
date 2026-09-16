"""First measured-physics stage: passive mass, planar COM and kinetic friction.

No motor commands, simulator mutation or overall calibration admission.
"""
import hashlib
import json
import math
from pathlib import Path
import statistics

KINDS={"total_mass_kg": {"unit":"kg","tolerance":.015,"range":[.3,1.5]},
       "home_com_x_m": {"unit":"m","tolerance":.003,"range":[-.2,.2]},
       "home_com_y_m": {"unit":"m","tolerance":.003,"range":[-.2,.2]},
       "kinetic_friction": {"unit":"dimensionless","tolerance":.15,"range":[.05,2.]}}
IDENTITY=("robot_serial","assembly_revision","battery_id","foot_material_id","surface_id","instrument_id")
REMAINING=["individual_link_mass_COM_full_inertia", "joint_axes_zero_limits_and_backlash",
           "actuator_torque_speed_friction_voltage_temperature", "IMU_extrinsics_bias_noise_and_timestamp_latency",
           "ground_compliance_impact_and_contact_slip", "independent_physical_motion_replay"]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def template():
    return {"schema":"microduck.passive-calibration-input/v1",
        "identity":{key:None for key in IDENTITY},
        "boundary":"Real measurements required. No policy activation or automatic simulator parameter replacement.",
        "records":[{"kind":kind,"split":split,"trial_id":f"{kind}-{split}-{i}",
                    "session_id":None,"path":f"raw/{kind}-{split}-{i}.json","sha256":None}
                   for kind in KINDS for split,n in (("fit",5),("validation",3)) for i in range(1,n+1)]}


def validate_manifest(bundle, manifest):
    failures=[]
    if manifest.get("schema")!="microduck.passive-calibration-input/v1": failures.append("input_schema")
    if set(manifest.get("identity",{}))!=set(IDENTITY): failures.append("identity_fields")
    for key in IDENTITY:
        value=manifest.get("identity",{}).get(key)
        if not isinstance(value,str) or not value.strip() or value.lower() in ("unknown","todo","null"):
            failures.append("missing_identity:"+key)
    records=manifest.get("records",[])
    expected={(kind,split):n for kind in KINDS for split,n in (("fit",5),("validation",3))}
    if not isinstance(records,list): return failures+["records_must_be_list"]
    for (kind,split),count in expected.items():
        selected=[r for r in records if r.get("kind")==kind and r.get("split")==split]
        if len(selected)!=count: failures.append(f"required_count:{kind}:{split}")
        if len({r.get("session_id") for r in selected if isinstance(r.get("session_id"),str) and r["session_id"].strip()})<2:
            failures.append(f"two_acquisition_sessions_required:{kind}:{split}")
    if len(records)!=32: failures.append("exact_32_records_required")
    seen_trials=set()
    split_digests={"fit":set(),"validation":set()}
    split_sessions={"fit":set(),"validation":set()}
    seen_paths=set()
    for r in records:
        trial=r.get("trial_id")
        if not isinstance(trial,str) or trial in seen_trials: failures.append("duplicate_or_missing_trial_id")
        seen_trials.add(trial)
        if (r.get("kind"),r.get("split")) not in expected: failures.append("unknown_kind_or_split"); continue
        split=r["split"]
        session=r.get("session_id")
        if not isinstance(session,str) or not session.strip(): failures.append("missing_session:"+str(trial))
        else: split_sessions[split].add(session)
        relative=r.get("path")
        if not isinstance(relative,str): failures.append("missing_raw_path"); continue
        path=(Path(bundle)/relative).resolve()
        if not path.is_relative_to(Path(bundle).resolve()) or path in seen_paths:
            failures.append("unsafe_or_duplicate_raw_path"); continue
        seen_paths.add(path)
        if not path.is_file(): failures.append("missing_raw:"+relative); continue
        actual=sha(path)
        if r.get("sha256")!=actual: failures.append("raw_hash_mismatch:"+relative)
        if actual in split_digests[split]: failures.append("duplicate_raw_record")
        split_digests[split].add(actual)
    if split_digests["fit"] & split_digests["validation"]: failures.append("fit_validation_raw_overlap")
    if split_sessions["fit"] & split_sessions["validation"]: failures.append("fit_validation_session_overlap")
    return sorted(set(failures))


def measure(raw, kind, identity):
    if raw.get("source")!="physical_measurement" or raw.get("identity")!=identity:
        raise ValueError("physical source and exact assembly/surface/instrument identity required")
    for field in ("captured_at_utc","instrument_calibration_reference","operator","setup_evidence"):
        if not isinstance(raw.get(field),str) or not raw[field].strip(): raise ValueError("missing provenance:"+field)
    u=raw.get("expanded_uncertainty_95")
    limit=KINDS[kind]
    if type(u) not in (float,int) or not math.isfinite(u) or not 0<u<=limit["tolerance"]/3:
        raise ValueError("missing/excessive measurement uncertainty")
    if raw.get("unit")!=limit["unit"]: raise ValueError("measurement unit mismatch")
    if kind=="total_mass_kg":
        gross,tare=float(raw["scale_gross_kg"]),float(raw["scale_tare_kg"])
        if not math.isfinite(gross) or not math.isfinite(tare) or not 0<=tare<gross:
            raise ValueError("invalid scale readings")
        value=gross-tare
    elif kind.startswith("home_com"):
        if raw.get("pose")!="measured_HOME" or raw.get("coordinate_frame")!="trunk_HOME_xy_m":
            raise ValueError("HOME pose and surveyed trunk frame required")
        supports=raw["tare_corrected_supports"]
        if len(supports)<3: raise ValueError("three noncollinear surveyed platform supports required")
        forces=[float(s["normal_force_n"]) for s in supports]
        if any(f<0 or not math.isfinite(f) for f in forces) or sum(forces)<=0: raise ValueError("invalid support loads")
        xy=[(float(s["x_m"]),float(s["y_m"])) for s in supports]
        area=max(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
                 for a in xy for b in xy for c in xy)
        if not math.isfinite(area) or area<1e-4: raise ValueError("degenerate support survey")
        axis=0 if kind=="home_com_x_m" else 1
        value=sum(f*p[axis] for f,p in zip(forces,xy))/sum(forces)
    else:
        if raw.get("test")!="constant_speed_horizontal_sled_with_actual_sole_material":
            raise ValueError("kinetic friction requires sliding, not tilt-breakaway/static friction")
        samples=raw["steady_samples"]
        if len(samples)<50: raise ValueError("at least 50 steady drag-force samples required")
        times=[float(s["time_s"]) for s in samples]
        if not all(math.isfinite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:])) or times[-1]-times[0]<1:
            raise ValueError("insufficient/invalid steady interval")
        ratios=[]
        for s in samples:
            speed,accel=float(s["speed_m_s"]),float(s["acceleration_m_s2"])
            force,normal=float(s["tangential_force_n"]),float(s["normal_force_n"])
            if not all(math.isfinite(v) for v in (speed,accel,force,normal)) or not .02<=speed<=.15 or abs(accel)>.02 or normal<=0 or force<0:
                raise ValueError("invalid steady kinetic-friction conditions")
            ratios.append(force/normal)
        value=statistics.mean(ratios)
    if not math.isfinite(value) or not limit["range"][0]<=value<=limit["range"][1]:
        raise ValueError("measurement outside declared intake envelope")
    return value,float(u)


def analyze(bundle, manifest):
    failures=validate_manifest(bundle,manifest)
    reports={}
    if not failures:
        for kind,definition in KINDS.items():
            groups={split:[] for split in ("fit","validation")}
            for record in manifest["records"]:
                if record["kind"]==kind:
                    raw=json.loads((Path(bundle)/record["path"]).read_text())
                    groups[record["split"]].append(measure(raw,kind,manifest["identity"]))
            values=[v for v,u in groups["fit"]]
            estimate=statistics.mean(values)
            # Do not divide shared systematic instrument uncertainty by sqrt(n).
            uncertainty=max(u for v,u in groups["fit"])+2.776*statistics.stdev(values)/math.sqrt(len(values))
            residuals=[abs(v-estimate)+u+uncertainty for v,u in groups["validation"]]
            passed=max(residuals)<=definition["tolerance"]
            reports[kind]={"fit_estimate":estimate,"unit":definition["unit"],"fit_expanded_uncertainty_95":uncertainty,
                "heldout_values_and_uncertainty":groups["validation"],"heldout_conservative_residuals":residuals,
                "tolerance":definition["tolerance"],"passed":passed,"fit_count":5,"validation_count":3}
            if not passed: failures.append("heldout_residual:"+kind)
    return {"schema":"microduck.passive-calibration-result/v1","status":"blocked_inputs" if not reports else "passive_stage_passed" if not failures else "passive_stage_failed",
        "failures":failures,"quantities":reports,"remaining_physics_components":REMAINING,
        "physical_calibration_complete":False,"simulator_parameters_changed":False,
        "boundary":"Only the four named passive measured quantities can pass. A fitted total mass cannot identify individual link inertias; kinetic sled friction does not calibrate foot impact/compliance. No automatic parameter application or policy activation."}
