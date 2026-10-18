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
