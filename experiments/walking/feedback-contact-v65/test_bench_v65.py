"""Analytic momentum fixtures guard contact-impulse and missing-tail accounting."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from bench_v65 import bench_metrics


def supported_rows(dt=.005):
    return [{'time_s':(i+1)*dt,'interval_start_s':i*dt,'velocity_m_s':0.,
        'velocity_before_m_s':0.,'contact_force_z_n':.03*9.81,'normal_load_n':.03*9.81,
        'penetration_m':.0001,'warnings':[]} for i in range(round(1/dt))]


class BenchTests(unittest.TestCase):
    def test_static_support_has_correct_integrated_weight_for_every_rate(self):
        for dt in (.005,.0025,.00125,.000625):
            r=bench_metrics(supported_rows(dt),.03,1.,dt)
            self.assertTrue(r['passed']);self.assertAlmostEqual(r['normal_impulse_ns'],.2943)

    def test_missing_tail_never_passes(self):
        r=bench_metrics(supported_rows()[:-1],.03,1.,.005)
        self.assertIn('incomplete_duration',r['failures']);self.assertIn('not_settled',r['failures'])

    def test_force_with_wrong_interval_or_missing_impulse_fails_balance(self):
        rows=supported_rows();rows[40]['contact_force_z_n']=0.
        self.assertIn('momentum_balance',bench_metrics(rows,.03,1.,.005)['failures'])


if __name__=='__main__':unittest.main()
