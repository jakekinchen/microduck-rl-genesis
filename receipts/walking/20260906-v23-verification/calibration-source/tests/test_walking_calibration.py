"""Synthetic fixtures test the intake only; never physical calibration evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from experiments.walking.calibration_v1 import KINDS, template,sha,measure,analyze,validate_manifest


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.manifest=template()
        self.manifest["identity"]={k:"SYNTHETIC-TEST-ONLY-"+k for k in self.manifest["identity"]}
        for i,r in enumerate(self.manifest["records"]):
            r["session_id"]=r["split"]+str(i%2)
            raw={"source":"physical_measurement","identity":self.manifest["identity"],
                 "captured_at_utc":"2026-09-06T00:00:00Z","operator":"synthetic fixture",
                 "setup_evidence":"synthetic fixture, not measurement","instrument_calibration_reference":"synthetic",
                 "fixture_unique":i,"unit":KINDS[r["kind"]]["unit"],
                 "expanded_uncertainty_95":KINDS[r["kind"]]["tolerance"]/10,
                 "scale_gross_kg":.8,"scale_tare_kg":.06,"pose":"measured_HOME","coordinate_frame":"trunk_HOME_xy_m",
                 "tare_corrected_supports":[{"x_m":0,"y_m":.1,"normal_force_n":2},{"x_m":-.1,"y_m":-.1,"normal_force_n":1},{"x_m":.1,"y_m":-.1,"normal_force_n":1}],
                 "test":"constant_speed_horizontal_sled_with_actual_sole_material",
                 "steady_samples":[{"time_s":j*.025,"speed_m_s":.05,"acceleration_m_s2":0,"tangential_force_n":.6,"normal_force_n":1} for j in range(50)]}
            p=self.root/r["path"]
            p.parent.mkdir(exist_ok=True)
            p.write_text(json.dumps(raw))
            r["sha256"]=sha(p)

    def test_missing_physical_inputs_fail_closed(self):
        report=analyze(self.root,template())
        self.assertEqual(report["status"],"blocked_inputs")
        self.assertFalse(report["physical_calibration_complete"])

    def test_synthetic_complete_fixture_never_admits_full_physics(self):
        report=analyze(self.root,self.manifest)
        self.assertEqual(report["status"],"passive_stage_passed")
        self.assertAlmostEqual(report["quantities"]["total_mass_kg"]["fit_estimate"],.74)
        self.assertFalse(report["physical_calibration_complete"])
        self.assertFalse(report["simulator_parameters_changed"])

    def test_heldout_failure_does_not_modify_fit(self):
        r=next(r for r in self.manifest["records"] if r["kind"]=="total_mass_kg" and r["split"]=="validation")
        p=self.root/r["path"];raw=json.loads(p.read_text());raw["scale_gross_kg"]+=.1;p.write_text(json.dumps(raw));r["sha256"]=sha(p)
        report=analyze(self.root,self.manifest)
        self.assertEqual(report["status"],"passive_stage_failed")
        self.assertAlmostEqual(report["quantities"]["total_mass_kg"]["fit_estimate"],.74)

    def test_split_leakage_and_raw_hash_change_rejected(self):
        r=self.manifest["records"][5]
        r["session_id"]=self.manifest["records"][0]["session_id"]
        self.assertIn("fit_validation_session_overlap",validate_manifest(self.root,self.manifest))
        (self.root/r["path"]).write_text("{}")
        self.assertTrue(any(f.startswith("raw_hash_mismatch:") for f in validate_manifest(self.root,self.manifest)))

    def test_static_friction_and_bad_timestamps_rejected(self):
        r=next(r for r in self.manifest["records"] if r["kind"]=="kinetic_friction")
        raw=json.loads((self.root/r["path"]).read_text())
        raw["test"]="tilt_breakaway"
        with self.assertRaises(ValueError): measure(raw,r["kind"],self.manifest["identity"])
        raw["test"]="constant_speed_horizontal_sled_with_actual_sole_material"
        raw["steady_samples"][2]["time_s"]=float("nan")
        with self.assertRaises(ValueError): measure(raw,r["kind"],self.manifest["identity"])

    def test_collinear_load_cells_do_not_establish_planar_com(self):
        r=next(r for r in self.manifest["records"] if r["kind"]=="home_com_x_m")
        raw=json.loads((self.root/r["path"]).read_text())
        for s in raw["tare_corrected_supports"]: s["y_m"]=0
        with self.assertRaises(ValueError): measure(raw,r["kind"],self.manifest["identity"])


if __name__=="__main__": unittest.main()
