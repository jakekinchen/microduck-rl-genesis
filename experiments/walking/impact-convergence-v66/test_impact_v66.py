"""Analytic trajectory, phase, onset and missing-evidence checks; no simulator."""
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from impact_v66 import ADVANCE,DT,GRAVITY,start_state,ballistic_position,impact_prediction,impact_audit


class ImpactTests(unittest.TestCase):
    def test_phases_preserve_energy_and_continuous_impact_velocity(self):
        for tau in ADVANCE:
            q,v=start_state(tau)
            self.assertAlmostEqual(.5*v*v+GRAVITY*(.005+q),GRAVITY*.005,places=15)
            self.assertAlmostEqual(impact_prediction(.005,tau,DT[-1])['continuous_impact_velocity_m_s'],-math.sqrt(2*GRAVITY*.005),places=15)

    def test_finest_grid_has_four_distinct_quarter_phases(self):
        self.assertEqual([round((x/DT[-1])%1,8) for x in ADVANCE],[0.,.25,.5,.75])

    def test_closed_form_matches_iterated_semiimplicit_euler(self):
        for tau in ADVANCE:
            for dt in DT:
                q,v=start_state(tau);q0,v0=q,v
                for i in range(250):
                    self.assertAlmostEqual(q,ballistic_position(q0,v0,dt,i),places=13)
                    v-=GRAVITY*dt;q+=v*dt

    def test_predicted_onset_brackets_first_interference(self):
        for tau in ADVANCE:
            for dt in DT:
                r=impact_prediction(.005,tau,dt);n=r['solver_step'];q,v=start_state(tau)
                self.assertGreater(.005+ballistic_position(q,v,dt,n-1),0.)
                self.assertLessEqual(.005+ballistic_position(q,v,dt,n),0.)

    def test_known_v65_contact_onset_is_reproduced(self):
        self.assertEqual(impact_prediction(.005,0.,.000625)['solver_step'],51)

    def test_missing_contact_and_wrong_onset_cannot_pass(self):
        self.assertFalse(impact_audit([],.005,0.,DT[0])['passed'])
        dt=DT[0];n=impact_prediction(.005,0.,dt)['solver_step']+1
        rows=[{'normal_load_n':1. if i==n else 0.,'interval_start_s':i*dt,
               'position_before_m':ballistic_position(0.,0.,dt,i),'velocity_before_m_s':-GRAVITY*i*dt} for i in range(n+1)]
        self.assertIn('onset_not_predicted_by_discrete_freefall',impact_audit(rows,.005,0.,dt)['failures'])

    def test_nonfinite_and_unfrozen_parameters_rejected(self):
        for args in ((float('nan'),0.,DT[0]),(.005,0.,.003),(.005,.001,DT[0])):
            with self.assertRaises(ValueError):impact_prediction(*args)


if __name__=='__main__':unittest.main()
