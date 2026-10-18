import unittest
from pcbtools.rules.aux_power import evaluate_5v, output_population_errors


class FiveVoltSupplyTests(unittest.TestCase):
    def setUp(self):
        self.profile = {'input_effective_uf': 5.99111955,
                        'output_effective_uf': 21.11346366,
                        'output_nominal_max_uf': 55.66,
                        'soft_start_min_ms': 1.510,
                        'qualification_status': 'TYPICAL_MODEL_WITH_RESERVES_BENCH_OPEN'}
        self.pins = {('U13', '8'): 'SS', ('C133', '1'): 'SS',
                     ('C133', '2'): '/GND', ('C132', '1'): '/VA_5V',
                     ('C132', '2'): '/GND', ('C31', '1'): '/VA_5V',
                     ('C31', '2'): '/GND', ('C30', '1'): '/VDRV_12V',
                     ('C30', '2'): '/GND', ('U13', '7'): '/VDRV_12V'}

    def test_reviewed_budget(self):
        self.assertEqual([], evaluate_5v(self.profile, self.pins))

    def test_floating_soft_start_fails(self):
        self.pins[('U13', '8')] = 'unconnected-SS'
        self.assertTrue(evaluate_5v(self.profile, self.pins))

    def test_missing_second_output_branch_fails(self):
        del self.pins[('C132', '1')]
        self.assertTrue(evaluate_5v(self.profile, self.pins))

    def test_nominal_capacitance_cannot_replace_effective_budget(self):
        self.profile['output_effective_uf'] = 9.9
        self.assertTrue(evaluate_5v(self.profile, self.pins))

    def test_low_esr_100uf_case_requires_new_review(self):
        self.profile['output_nominal_max_uf'] = 100
        self.assertTrue(evaluate_5v(self.profile, self.pins))

    def test_unbudgeted_parallel_capacitor_is_rejected(self):
        profile = {'output_capacitor_population': {'C31': '22uF', 'C132': '22uF'}}
        values = {'C31': '22uF', 'C132': '22uF'}
        self.assertEqual([], output_population_errors(profile, values, self.pins))
        values['C999'] = '47uF'
        self.pins.update({('C999', '1'): '/VA_5V', ('C999', '2'): '/GND'})
        self.assertTrue(output_population_errors(profile, values, self.pins))
