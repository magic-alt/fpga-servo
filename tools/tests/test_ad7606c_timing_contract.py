"""Reject unqualified timing claims for the fitted 3.3 V/5 V translator path."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.rules.adc import ad7606c_api


class FittedAD7606CTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = resolve_project('ad7606c')
        cls.api = ad7606c_api(cls.project)
        cls.profile = json.loads((cls.project.schematic.parent / 'adc_profile.json').read_text())
        cls.xdc = (cls.project.schematic.parent / 'ax7010_servo_ad7606c.xdc').read_text()

    def errors(self, profile):
        return self.api.profile_errors(profile, self.xdc)

    def test_current_profile_has_explicit_unqualified_round_trip_contract(self):
        self.assertIn('board_timing', self.profile['timing'])
        self.assertEqual(self.errors(self.profile), [])

    def test_absent_board_timing_is_rejected(self):
        bad = copy.deepcopy(self.profile)
        bad['timing'].pop('board_timing', None)
        self.assertTrue(any('board timing' in e for e in self.errors(bad)))

    def test_20mhz_cannot_be_authorized_by_chip_frequency_alone(self):
        bad = copy.deepcopy(self.profile)
        bad['timing']['board_timing'] = {'implementation_status': 'QUALIFIED',
                                        'opposite_edge_20mhz_qualified': True}
        self.assertTrue(any('board timing' in e for e in self.errors(bad)))

    def test_undercounted_propagation_is_rejected(self):
        for key in ('sclk_translator_max_ns', 'adc_data_access_max_ns', 'dout_translator_max_ns'):
            bad = copy.deepcopy(self.profile)
            bad['timing'].setdefault('board_timing', {})[key] = 0
            with self.subTest(key=key):
                self.assertTrue(any('board timing' in e for e in self.errors(bad)))

    def test_conversion_bound_cannot_be_confused_with_analog_phase(self):
        bad = copy.deepcopy(self.profile)
        bad['timing']['conversion_time_max_us'] = 0.5
        self.assertTrue(any('0.65' in e for e in self.errors(bad)))

    def test_phase_delay_is_not_bandwidth_or_a_worst_case_guarantee(self):
        bad = copy.deepcopy(self.profile)
        bad['timing']['analog_3db_bandwidth_khz'] = 220
        self.assertTrue(any('150' in e for e in self.errors(bad)))

    def test_raw_half_cycle_margins_are_independent_calculations(self):
        # TI SCES936A table 7.11, full temperature; ADI Rev.A table 5.
        self.assertAlmostEqual(9 + 15.7 + 10, 34.7)
        self.assertAlmostEqual(1e9 / 5e6 / 2 - 34.7, 65.3)
        self.assertAlmostEqual(1e9 / 20e6 / 2 - 34.7, -9.7)


if __name__ == '__main__':
    unittest.main()
