import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.rules.aux_power import evaluate, check_project


class AuxiliaryPowerTests(unittest.TestCase):
    def setUp(self):
        self.project = resolve_project('ad7606c')
        self.profile = json.loads((self.project.schematic.parent / 'aux_power_profile.json').read_text())

    def test_one_amp_design_has_current_margin(self):
        errors, result = evaluate(self.profile)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(result['minimum_peak_margin_a'], 0.05)

    def test_authored_source_and_bom_match_candidate(self):
        self.assertEqual(check_project(self.project), [])

    def retained_fixture(self):
        import xml.etree.ElementTree as ET
        from pcbtools.rules.adc import ad7606c_api
        candidate = self.project.parameters['component_ecos']['L1']
        old, new = {}, {}
        for target, fields in ((old, {'value': '68uH', 'footprint': 'old:land'}), (new, candidate)):
            for ref in ('L1', 'R1'):
                comp = ET.Element('comp', ref=ref)
                values = fields if ref == 'L1' else {'value': '10k', 'footprint': 'old:R'}
                ET.SubElement(comp, 'value').text = values['value']
                ET.SubElement(comp, 'footprint').text = values['footprint']
                node = ET.SubElement(comp, 'fields')
                for key in ('Manufacturer', 'MPN', 'LCSC'):
                    ET.SubElement(node, 'field', name=key).text = values.get(key, '')
                target[ref] = comp
        pins = {('L1', '1'): 'SW', ('L1', '2'): '12V', ('R1', '1'): 'SW', ('R1', '2'): 'GND'}
        return ad7606c_api(self.project), old, new, pins

    def test_authorized_identity_eco_does_not_allow_rewire(self):
        api, old, new, pins = self.retained_fixture()
        self.assertEqual(api.inherited_errors((old, pins), (new, pins)), [])
        changed = dict(pins); changed[('L1', '1')] = 'WRONG'
        self.assertTrue(api.inherited_errors((old, pins), (new, changed)))

    def test_authorized_eco_does_not_allow_another_mpn(self):
        api, old, new, pins = self.retained_fixture()
        new['L1'].find("fields/field[@name='MPN']").text = 'OTHER'
        self.assertTrue(any('MPN' in e for e in api.inherited_errors((old, pins), (new, pins))))

    def test_previous_68uh_cannot_meet_worst_corner(self):
        self.profile['inductor']['nominal_uh'] = 68
        errors, result = evaluate(self.profile)
        self.assertTrue(any('peak' in e for e in errors))
        self.assertGreater(result['peak_a'], 1.25)

    def test_original_ripple_network_rejected_at_24v(self):
        self.profile['feedback']['ripple_resistance_ohm'] = 453000
        self.assertTrue(any('ripple' in e for e in evaluate(self.profile)[0]))

    def test_original_feedback_precision_not_accepted(self):
        self.profile['feedback']['upper_ohm'] = 453000
        self.profile['feedback']['resistance_total_fraction'] = 0.02
        self.assertTrue(any('output envelope' in e for e in evaluate(self.profile)[0]))

    def test_requirement_cannot_drop_to_half_amp(self):
        self.profile['requirement']['continuous_total_a'] = 0.5
        self.assertTrue(any('1 A' in e for e in evaluate(self.profile)[0]))

    def test_calculated_l_must_match_installed_value(self):
        self.profile['inductor']['nominal_uh'] = 220
        self.assertTrue(any('actual component' in e for e in evaluate(self.profile)[0]))

    def test_ron_programmed_frequency_cannot_be_invented(self):
        self.profile['controller']['frequency_nominal_khz'] = 400
        self.assertTrue(any('RON' in e for e in evaluate(self.profile)[0]))

    def test_inadequate_rms_rating_rejected(self):
        self.profile['inductor']['rated_rms_a'] = 0.9
        self.assertTrue(any('RMS' in e for e in evaluate(self.profile)[0]))

    def test_fault_peak_not_compared_to_typical_load_current(self):
        self.profile['inductor']['saturation_10pct_typical_a'] = 1.5
        self.assertTrue(any('fault' in e for e in evaluate(self.profile)[0]))

    def test_calculation_cannot_claim_bench_pass(self):
        self.profile['qualification_status'] = 'PASS'
        self.assertTrue(any('bench' in e for e in evaluate(self.profile)[0]))


if __name__ == '__main__':
    unittest.main()
