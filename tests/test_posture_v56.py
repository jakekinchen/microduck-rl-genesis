"""Protect unchanged stepping, routing, reset and curriculum contracts in V56."""
import ast
from pathlib import Path
import unittest
from microduck.native_posture_env_v56 import standing_face_cost
from experiment_ops.activity import parse_processes
ROOT=Path(__file__).resolve().parents[1]
class PostureTests(unittest.TestCase):
    def test_walking_and_control_arm_never_receive_face_penalty(self):
        for pitch in [-90,-30,-25,0,25,30,90]:
            self.assertEqual(standing_face_cost(pitch,False,2),0)
            self.assertEqual(standing_face_cost(pitch,True,0),0)
        self.assertEqual(standing_face_cost(25,True,2),0)
        self.assertEqual(standing_face_cost(30,True,2),2)
        self.assertEqual(standing_face_cost(-30,True,2),2)

    def test_non_reward_functions_are_identical_to_frozen_v55(self):
        old=ast.parse((ROOT/'microduck/native_yaw_env_v55.py').read_text())
        new=ast.parse((ROOT/'microduck/native_posture_env_v56.py').read_text())
        def functions(tree):
            return {node.name:ast.dump(node) for node in ast.walk(tree)
                    if isinstance(node,ast.FunctionDef) and node.name not in ['__init__','step','standing_face_cost']}
        self.assertEqual(functions(old),functions(new))
        old_class=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='NativeSequenceEnv')
        new_class=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='NativeSequenceEnv')
        def stepping(node):
            f=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='step')
            # Ignore only the declared new reward telemetry and face-cost lines.
            class RemoveFace(ast.NodeTransformer):
                def visit_Assign(self,n):
                    names=[ast.unparse(x) for x in n.targets]
                    if any(x in ['face_pitch','face_cost','reward_components','reward_components[i]'] for x in names):return None
                    return self.generic_visit(n)
                def visit_AugAssign(self,n):
                    if ast.unparse(n)=='cost += face_cost':return None
                    return self.generic_visit(n)
            return ast.dump(RemoveFace().visit(f))
        self.assertEqual(stepping(old_class),stepping(new_class))

    def test_new_diagnostics_are_visible_to_compute_guard(self):
        for entry in ['probe_posture_feasibility_v56','probe_posture_head_v56','probe_posture_v56','evaluate_posture_flat_v56','evaluate_posture_endurance_v56','evaluate_posture_surfaces_v56','visual_follow_v1_evaluate','run_upstream_diagnostic','run_coacd_v58','coacd_worker_v58','validate_proxy_v58']:
            with self.subTest(entry=entry):
                self.assertEqual(parse_processes(f'123 1 00:01 python3 scripts/{entry}.py')[0]['workload'],'simulation_diagnostic')
if __name__=='__main__':unittest.main()
