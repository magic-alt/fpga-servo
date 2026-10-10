"""Meaningful fault-injection tests for ADC inhibit contracts on fresh XML."""
from pathlib import Path
import tempfile
import sys
import unittest
import xml.etree.ElementTree as ET
from check_adc_validity import verify


class AdcValidityTests(unittest.TestCase):
    # Generate this file through kicad-cli; never use a tracked historical XML.
    source = Path('artifacts/adc_validity.xml')

    def mutate(self, change):
        if not self.source.is_file():
            self.fail('fresh XML missing; pass --netlist PATH after native export')
        root = ET.parse(self.source).getroot()
        change(root)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'mutation.xml'
            ET.ElementTree(root).write(path, encoding='utf-8')
            return verify(path)

    def test_restoring_old_supervisor_rejected(self):
        def change(root):
            root.find("./components/comp[@ref='U25']/value").text = 'TPS3808G50'
        errors, _ = self.mutate(change)
        self.assertTrue(any('U25' in e for e in errors))

    def test_reset_disconnected_from_latch_rejected(self):
        def change(root):
            for net in root.findall('./nets/net'):
                node = net.find("node[@ref='U25'][@pin='6']")
                if node is not None:
                    net.remove(node)
        errors, _ = self.mutate(change)
        self.assertTrue(any('U25' in e for e in errors))

    def test_replacing_precision_divider_with_loose_resistors_rejected(self):
        def change(root):
            root.find("./components/comp[@ref='R92']/fields/field[@name='Tolerance']").text = '1%'
        errors, _ = self.mutate(change)
        self.assertTrue(any('R92' in e for e in errors))

    def test_low_trip_resistor_substitution_rejected(self):
        def change(root):
            root.find("./components/comp[@ref='R92']/value").text = '3k'
        errors, _ = self.mutate(change)
        self.assertTrue(any('R92' in e for e in errors))

    def test_transient_qualification_never_inferred_from_static_pass(self):
        errors, numeric = self.mutate(lambda root: None)
        self.assertEqual(errors, [])
        self.assertFalse(numeric['transient_gate_off_qualified'])
        self.assertGreater(numeric['falling_threshold_V'][0], numeric['adc_min_V'])
        self.assertLess(numeric['rising_threshold_max_V'], numeric['regulated_static_V'][0] - .01)


if __name__ == '__main__':
    if '--netlist' in sys.argv:
        index = sys.argv.index('--netlist')
        AdcValidityTests.source = Path(sys.argv[index + 1])
        del sys.argv[index:index + 2]
    unittest.main()
