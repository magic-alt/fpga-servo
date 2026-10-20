"""Reject undersized banks and physical bypasses of the bus shunt."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.rules.dc_link import evaluate, physical_errors


def fixture():
    caps = ['C1', 'C2', *[f'C{i}' for i in range(120, 128)]]
    branches = [{'capacitor': c, 'resistor': f'R{120+i}'} for i, c in enumerate(caps)]
    profile = {'continuous_phase_arms': 10.0, 'peak_phase_amplitude_a': 20.0,
               'peak_duration_s': 30, 'waveform': 'BALANCED_SINUSOIDAL',
               'branches': branches, 'sharing_factor': .8, 'waveform_allowance': 1.1,
               'resistor_hot_power_limit_w': .708,
               'qualification_status': 'STATIC_DESIGN_ONLY_BENCH_OPEN'}
    pins = {('RSH4', '1'): '/VBUS_PROT', ('RSH4', '2'): '/VBUS_BRIDGE'}
    parts = {}
    parts['J7'] = {'MPN': '1714971', 'Value': 'EXT_SINK'}
    pins['J7', '1'] = '/VBUS_PROT'
    pins['J7', '2'] = '/GND'
    for b in branches:
        c, r = b['capacitor'], b['resistor']
        parts[c] = {'MPN': 'EKZN101ELL101MJ20S', 'Value': '100uF'}
        parts[r] = {'MPN': 'WSL2512R3300FEA', 'Value': '0.33R'}
        pins[c, '1'] = pins[r, '2'] = f'/Bank/DC_LINK_{c}_P'
        pins[c, '2'] = '/GND'
        pins[r, '1'] = '/VBUS_PROT'
    return profile, parts, pins


class DCLinkTests(unittest.TestCase):
    def external_fixture(self):
        profile = {'mode': 'EXTERNAL_CAPACITOR_BLEEDER',
                   'continuous_phase_arms': 10.0, 'peak_phase_amplitude_a': 20.0,
                   'peak_duration_s': 30, 'waveform': 'BALANCED_SINUSOIDAL',
                   'branches': [], 'waveform_allowance': 1.1,
                   'qualification_status': 'STATIC_DESIGN_ONLY_BENCH_OPEN',
                   'external_requirements': {
                       'nominal_capacitance_uf': 1000, 'minimum_effective_capacitance_uf': 800,
                       'maximum_capacitance_uf': 1200, 'minimum_voltage_rating_v': 100,
                       'minimum_ripple_current_arms': 11, 'maximum_bus_voltage_v': 60,
                       'discharge_target_v': 5, 'maximum_discharge_time_s': 10,
                       'bleeder_resistance_ohm': 2200, 'bleeder_tolerance': .05,
                       'bleeder_minimum_hot_power_w': 3.5,
                       'independent_branch_protection_required': True,
                       'remain_connected_until_discharged': True,
                       'bleeder_is_not_regeneration_sink': True}}
        parts = {'J7': {'MPN': '1714971', 'Value': 'EXT_DC_LINK'},
                 'C3': {'Value': '1uF'}, 'C4': {'Value': '100nF'}}
        pins = {('J7', '1'): '/VBUS_PROT', ('J7', '2'): '/GND',
                ('RSH4', '1'): '/VBUS_PROT', ('RSH4', '2'): '/VBUS_BRIDGE',
                ('C3', '1'): '/VBUS_PROT', ('C3', '2'): '/GND',
                ('C4', '1'): '/VBUS_PROT', ('C4', '2'): '/GND'}
        return profile, parts, pins

    def test_external_network_requires_one_protected_bus_interface_and_no_bank(self):
        profile, parts, pins = self.external_fixture()
        result, errors = evaluate(profile)
        self.assertEqual(errors, [])
        self.assertEqual(result['required_external_ripple_arms'], 11)
        self.assertLess(result['bleeder_worst_discharge_time_s'], 10)
        self.assertEqual(physical_errors(profile, parts, pins), [])
        parts['C120'] = {'Value': '100uF'}
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_external_interface_cannot_bypass_shunt_or_reverse_protection(self):
        profile, parts, pins = self.external_fixture()
        for net in ('/VBUS_BRIDGE', '/power_input/VIN_RAW'):
            pins['J7', '1'] = net
            self.assertTrue(physical_errors(profile, parts, pins))

    def test_external_mode_cannot_remove_local_hf_bypass_or_add_second_interface(self):
        profile, parts, pins = self.external_fixture()
        del pins['C4', '1']
        self.assertTrue(physical_errors(profile, parts, pins))
        profile, parts, pins = self.external_fixture()
        parts['J8'] = {'Value': 'EXT_DC_LINK'}
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_external_budget_cannot_claim_qualified_or_omit_discharge_and_ripple(self):
        for key, value in [('minimum_ripple_current_arms', 1),
                           ('bleeder_resistance_ohm', 1e6),
                           ('bleeder_minimum_hot_power_w', .25),
                           ('independent_branch_protection_required', False),
                           ('bleeder_is_not_regeneration_sink', False)]:
            profile, _, _ = self.external_fixture()
            profile['external_requirements'][key] = value
            self.assertTrue(evaluate(profile)[1], key)
        profile, _, _ = self.external_fixture()
        profile['qualification_status'] = 'QUALIFIED'
        self.assertTrue(evaluate(profile)[1])

    def test_damped_bank_has_stated_ripple_and_hot_resistor_margin(self):
        profile, parts, pins = fixture()
        result, errors = evaluate(profile)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(result['peak_capacitor_bank_arms_bound'], 10)
        self.assertGreater(result['allocated_ripple_arms'], 11)
        self.assertEqual(physical_errors(profile, parts, pins), [])

    def test_original_two_can_bank_is_rejected(self):
        profile, _, _ = fixture()
        profile['branches'] = profile['branches'][:2]
        self.assertTrue(evaluate(profile)[1])

    def test_twenty_amp_peak_is_not_twenty_arms(self):
        result, _ = evaluate(fixture()[0])
        self.assertAlmostEqual(result['peak_phase_arms'], 20 / 2 ** .5)

    def test_missing_damping_part_or_lower_rated_substitution_fails(self):
        profile, parts, pins = fixture()
        parts['R120']['MPN'] = 'UNREVIEWED'
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_downstream_bank_bypassing_fast_shunt_is_rejected(self):
        profile, parts, pins = fixture()
        pins['R120', '1'] = '/VBUS_BRIDGE'
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_extra_branch_node_and_direct_undamped_connection_fail(self):
        profile, parts, pins = fixture()
        pins['X1', '1'] = pins['C1', '1']
        self.assertTrue(physical_errors(profile, parts, pins))
        pins = copy.deepcopy(fixture()[2])
        pins['C1', '1'] = '/VBUS_PROT'
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_external_sink_cannot_be_stranded_before_reverse_protection(self):
        profile, parts, pins = fixture()
        pins['J7', '1'] = '/VIN_RAW'
        self.assertTrue(physical_errors(profile, parts, pins))

    def test_nonfinite_budget_and_false_bench_claim_fail(self):
        profile, _, _ = fixture()
        profile['resistor_hot_power_limit_w'] = float('nan')
        self.assertTrue(evaluate(profile)[1])
        profile = fixture()[0]
        profile['qualification_status'] = 'QUALIFIED'
        self.assertTrue(evaluate(profile)[1])


if __name__ == '__main__':
    unittest.main()
