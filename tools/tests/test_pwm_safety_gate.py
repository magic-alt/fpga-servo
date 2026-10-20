"""Physical safety-gate regressions; no timing or DRV8300 device simulation."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.rules import protection


class SafetyGateTests(unittest.TestCase):
    def setUp(self):
        self.values = {'U1': 'DRV8300DPWR', 'U11': 'SN74LVC1G11DCKR'}
        self.pins = {('U11', '1'): '/GATE_EN', ('U11', '3'): '/PWR_READY',
                     ('U11', '6'): '/ARMED', ('U11', '4'): '/gate/RUN_OK',
                     ('U11', '5'): '/VIO_3V3', ('U11', '2'): '/GND'}
        for i, phase in enumerate('UVW'):
            gate = f'U{8+i}'
            self.values[gate] = 'SN74LVC2G08DCUR'
            self.pins.update({(gate, '8'): '/VIO_3V3', (gate, '4'): '/GND',
                              (gate, '2'): '/gate/RUN_OK', (gate, '6'): '/gate/RUN_OK'})
            for raw_pin, out_pin, driver, pull, side in (
                    ('1', '7', str(i+1), f'R{56+2*i}', 'H'),
                    ('5', '3', str(i+4), f'R{57+2*i}', 'L')):
                net = f'/gate/{side}IN_{phase}_SAFE'
                self.values[pull] = '10k'
                self.pins.update({(gate, raw_pin): f'/PWM_{phase}{side}',
                                  (gate, out_pin): net, ('U1', driver): net,
                                  (pull, '1'): net, (pull, '2'): '/GND'})

    def test_reviewed_physical_graph(self):
        self.assertEqual(protection.pwm_safety_errors(self.values, self.pins), [])

    def test_each_weak_or_missing_pulldown_rejected(self):
        for ref in [f'R{i}' for i in range(56, 62)]:
            for value in ('100k', None):
                with self.subTest(ref=ref, value=value):
                    values = dict(self.values)
                    if value is None:
                        del values[ref]
                    else:
                        values[ref] = value
                    self.assertTrue(protection.pwm_safety_errors(values, self.pins))

    def test_old_100k_alternative_cannot_survive_10k_selection(self):
        expected = {'Value': '10k', 'MPN': 'ABD03K1002FT', 'LCSC': 'C5139509',
                    'Footprint': 'Resistor_SMD:R_0603_1608Metric',
                    'Alternative_MPN': 'UNQUALIFIED', 'Alternative_LCSC': 'UNVERIFIED',
                    'Alternative_Status': 'UNQUALIFIED'}
        parts = {f'R{i}': dict(expected) for i in range(56, 62)}
        rows = {ref: {'Value / Part': part['Value'], 'MPN': part['MPN'],
                     'LCSC': part['LCSC'], 'Package': part['Footprint'],
                     'Alternative MPN': 'UNQUALIFIED', 'Alternative LCSC': 'UNVERIFIED'}
                for ref, part in parts.items()}
        self.assertEqual(protection.pwm_pulldown_selection_errors(parts, rows), [])
        parts['R56']['Alternative_MPN'] = '0603WAF1003T5E'
        self.assertTrue(protection.pwm_pulldown_selection_errors(parts, rows))
        parts['R56']['Alternative_MPN'] = 'UNQUALIFIED'
        rows['R61']['Alternative LCSC'] = 'C25803'
        self.assertTrue(protection.pwm_pulldown_selection_errors(parts, rows))

    def test_bypass_wrong_pin_and_missing_enable_rejected(self):
        for key, net in [(('U1', '1'), '/PWM_UH'), (('U8', '1'), '/PWM_UL'),
                         (('U8', '2'), '/VIO_3V3'), (('R61', '2'), '/VIO_3V3'),
                         (('U11', '6'), '/VIO_3V3'), (('U11', '3'), '/PWR_GOOD'),
                         (('U11', '4'), '/GND'), (('U9', '8'), '/GND')]:
            with self.subTest(key=key):
                pins = dict(self.pins)
                pins[key] = net
                self.assertTrue(protection.pwm_safety_errors(self.values, pins))

    def test_wrong_gate_or_inverted_driver_rejected(self):
        for ref in ('U1', 'U8', 'U9', 'U10', 'U11'):
            values = dict(self.values)
            values[ref] = 'DRV8300DIPWR' if ref == 'U1' else 'WRONG'
            self.assertTrue(protection.pwm_safety_errors(values, self.pins))

    def test_cross_channel_short_rejected(self):
        old = self.pins[('U1', '2')]
        new = self.pins[('U1', '1')]
        pins = {key: new if value == old else value for key, value in self.pins.items()}
        self.assertTrue(protection.pwm_safety_errors(self.values, pins))

    def test_high_low_channels_use_real_dcu_pin_map(self):
        # TI DCU8: 1A=1, 1B=2, 1Y=7; 2A=5, 2B=6, 2Y=3.
        for run in (0, 1):
            for mask in range(64):
                levels = {'/gate/RUN_OK': run}
                for i, phase in enumerate('UVW'):
                    levels[f'/PWM_{phase}H'] = (mask >> (2*i)) & 1
                    levels[f'/PWM_{phase}L'] = (mask >> (2*i+1)) & 1
                protection.pwm_gate_levels(self.pins, levels)
                for i in range(3):
                    for driver, bit in ((str(i+1), 2*i), (str(i+4), 2*i+1)):
                        self.assertEqual(levels[self.pins[('U1', driver)]], run & ((mask >> bit) & 1))
                if run and mask == 63:
                    self.assertTrue(all(levels[self.pins[('U1', str(i))]] for i in range(1, 7)))


if __name__ == '__main__':
    unittest.main()
