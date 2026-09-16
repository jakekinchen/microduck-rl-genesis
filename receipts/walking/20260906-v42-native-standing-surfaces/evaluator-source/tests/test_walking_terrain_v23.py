import tempfile
from pathlib import Path
import unittest
import mujoco
import numpy as np
from experiments.walking.terrain_v23 import Ground, materialize_terrain
from experiments.walking.collision_model import verify_physical_arrays


class TerrainTests(unittest.TestCase):
    def test_compiled_slope_rays_and_robot_invariance(self):
        with tempfile.TemporaryDirectory() as td:
            flat = mujoco.MjModel.from_xml_path(str(materialize_terrain(Path(td)/"flat", {"kind":"flat"})))
            m = mujoco.MjModel.from_xml_path(str(materialize_terrain(Path(td)/"slope", {"kind":"slope","axis":"y","degrees":-3})))
            verify_physical_arrays(flat,m)
            ground = Ground(m)
            m.geom_group[:]=0
            m.geom_group[ground.ids]=5
            d = mujoco.MjData(m)
            mujoco.mj_forward(m,d)
            for x,y in [(0,0),(1,.2),(-1,-.5)]:
                hit=np.zeros(1,np.int32)
                distance=mujoco.mj_ray(m,d,np.array([x,y,2.]),np.array([0.,0.,-1.]),np.array([0,0,0,0,0,1],np.uint8),True,-1,hit)
                self.assertEqual(int(hit[0]),m.geom("floor").id)
                self.assertAlmostEqual(2-distance,ground.height([[x,y]])[0],places=9)

    def test_seam_center_clearance_and_collision_mask(self):
        with tempfile.TemporaryDirectory() as td:
            path=materialize_terrain(Path(td),{"kind":"seams"})
            m=mujoco.MjModel.from_xml_path(str(path))
            ground=Ground(m)
            vertices=np.array([[.30,-.05,.007],[.40,-.05,.007],[.30,.05,.007],[.40,.05,.007]])
            self.assertAlmostEqual(ground.clearance(vertices),.004)
            np.testing.assert_allclose(ground.height([[.35,0],[.2,0]]),[.003,0])
            m.geom_contype[m.geom("terrain_0").id]=0
            with self.assertRaises(ValueError): Ground(m)

    def test_layout_reproduction_and_independent_models(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"a"
            recipe={"kind":"tiles","layout_seed":2301}
            path=materialize_terrain(target,recipe)
            before=path.read_bytes()
            materialize_terrain(target,recipe)
            self.assertEqual(before,path.read_bytes())
            with self.assertRaises(ValueError):
                materialize_terrain(target,{"kind":"tiles","layout_seed":2302})
            a=mujoco.MjModel.from_xml_path(str(path))
            b=mujoco.MjModel.from_xml_path(str(path))
            a.geom_pos[a.geom("terrain_0").id,2]=10
            self.assertLess(Ground(b).height([[.32,-1.12]])[0],.01)


if __name__ == "__main__": unittest.main()
