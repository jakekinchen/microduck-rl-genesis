from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mujoco
import numpy as np
from experiments.walking.physical_domain import nominal_arrays, apply_domain, FIELDS
ROOT = Path(__file__).resolve().parents[1]


class PhysicalDomainTests(unittest.TestCase):
    def setUp(self):
        self.model = mujoco.MjModel.from_xml_path(str(ROOT/"experiments/walking/models/contact-v11/scene.xml"))
        self.base = nominal_arrays(self.model)

    def test_repeated_application_does_not_accumulate_and_nominal_restores(self):
        domain = {"mass_inertia_scale":1.1,"sliding_friction_scale":.6}
        first = apply_domain(self.model,self.base,domain)
        self.assertEqual(first,apply_domain(self.model,self.base,domain))
        np.testing.assert_array_equal(self.model.body_mass,self.base['body_mass']*1.1)
        np.testing.assert_array_equal(self.model.body_inertia,self.base['body_inertia']*1.1)
        np.testing.assert_array_equal(self.model.geom_friction[:,0],np.full(self.model.ngeom,.6))
        apply_domain(self.model,self.base,{"mass_inertia_scale":1.,"sliding_friction_scale":1.})
        for key in FIELDS:np.testing.assert_array_equal(getattr(self.model,key),self.base[key])

    def test_other_model_and_nominal_snapshots_are_unchanged(self):
        other = mujoco.MjModel.from_xml_path(str(ROOT/"experiments/walking/models/contact-v11/scene.xml"))
        apply_domain(self.model,self.base,{"mass_inertia_scale":1.1,"sliding_friction_scale":.6})
        for key in FIELDS:
            np.testing.assert_array_equal(getattr(other,key),self.base[key])
            self.assertFalse(self.base[key].flags.writeable)

    def test_invalid_domain_refuses_before_mutation(self):
        for domain in ({"mass_inertia_scale":float('nan'),"sliding_friction_scale":1.},
                       {"mass_inertia_scale":True,"sliding_friction_scale":1.},
                       {"mass_inertia_scale":1.,"sliding_friction_scale":-.6}, {}):
            with self.assertRaises(ValueError):apply_domain(self.model,self.base,domain)
            for key in FIELDS:np.testing.assert_array_equal(getattr(self.model,key),self.base[key])


if __name__ == '__main__':unittest.main()
