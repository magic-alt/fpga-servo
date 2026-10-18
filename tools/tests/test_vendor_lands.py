import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Regressions for local rules that must never change external routing clearance."""

from pathlib import Path
import unittest
import json
from pcbtools.rules.power_layout import vendor_api
from pcbtools.rules.adc_layout import classify_native_body_rules
from pcbtools.rules.adc_layout import classify_native_body_rules
_family = vendor_api()
check = _family.check
check_internal_pad_rules = _family.check_internal_pad_rules

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / resolve_project("ads8588s").parameters["archived_pcb_dir"]


class VendorLandsTests(unittest.TestCase):
    def setUp(self):
        self.actual_rules = (ARCHIVE / "ax7010_servo_reva.kicad_dru").read_text(encoding="utf-8")
        self.expected = json.loads((ARCHIVE / "pcb_ci_baseline.json").read_text(encoding="utf-8"))["snapshot"]
        # Valid fixture prevents mutation tests passing merely because the old board is already blocked.
        gaps = {**{f"Q{i}": .60 for i in range(1, 9)},
                **{f"U{i}": .65 for i in (2, 3, 4, 5)},
                "U1": .25, "U6": .20, "U18": .20, "U15": .20}
        self.rules = "(version 1)\n" + "\n".join(
            f'(rule "{ref} internal lands" '
            f'(condition "A.Type == \'Pad\' && B.Type == \'Pad\' && A.Reference == \'{ref}\' && B.Reference == \'{ref}\'") '
            f'(constraint clearance (min {gap}mm)))'
            for ref, gap in gaps.items())

    def test_valid_reviewed_rule_fixture(self):
        self.assertEqual(check_internal_pad_rules(self.rules), [])

    def body_rule(self):
        return '''(rule "ADS8588S U6 no digital under body"
  (condition "A.intersectsArea('ADS8588S U6 body signal exclusion') && !(A.NetName == '/GND' || A.NetName == '/VA_5V' || A.NetName == '/VIO_3V3' || A.NetName == '/VBUS_ADC' || A.NetName == 'Net-(U4-OUT)')")
  (constraint disallow track via))'''

    def test_exact_native_adc_body_guard_is_additive(self):
        self.assertEqual(check_internal_pad_rules(self.rules+self.body_rule()), [])
        self.assertEqual(check_internal_pad_rules(self.rules+self.u12_rule()+self.body_rule()), [])

    def test_native_adc_body_guard_cannot_be_weakened_or_duplicated(self):
        rule = self.body_rule()
        mutations = [
            rule.replace("A.NetName == '/GND'", "A.NetName == '/ADC_CS_N' || A.NetName == '/GND'"),
            rule.replace('disallow track via', 'disallow track'),
            rule.replace('disallow track via', 'clearance (min 0.2mm)'),
            rule[:-1] + ' (severity warning))',
            rule[:-1] + ' (layer F.Cu))',
            rule[:-1] + ' (constraint clearance (min 0mm)))',
            rule.replace('body signal exclusion', 'smaller body signal exclusion'),
            rule.replace('no digital under body', 'no digital under body copy'),
            rule + rule,
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(check_internal_pad_rules(self.rules+mutation))

    def test_unknown_additional_rules_still_fail(self):
        self.assertTrue(check_internal_pad_rules(self.rules+self.body_rule()+'(rule "unreviewed" (constraint disallow track via))'))

    def test_body_classifier_only_returns_exact_unique_rule(self):
        valid, errors = classify_native_body_rules(self.rules+self.body_rule())
        self.assertEqual(errors, [])
        self.assertEqual([r.text for r in valid], [self.body_rule()])
        self.assertEqual(classify_native_body_rules(self.rules), ([], []))
        for bad in [self.body_rule()+self.body_rule(), self.body_rule().replace('track via', 'track')]:
            accepted, errors = classify_native_body_rules(self.rules+bad)
            self.assertEqual(accepted, [])
            self.assertTrue(errors)

    def test_native_body_rule_indentation_is_not_semantic(self):
        rule = self.body_rule().replace('\n  ', '\n\t    ')
        self.assertEqual(check_internal_pad_rules(self.rules+rule), [])

    def test_body_classifier_only_returns_exact_unique_rule(self):
        valid, errors = classify_native_body_rules(self.rules+self.body_rule())
        self.assertEqual(errors, [])
        self.assertEqual([r.text for r in valid], [self.body_rule()])
        self.assertEqual(classify_native_body_rules(self.rules), ([], []))
        for bad in [self.body_rule()+self.body_rule(), self.body_rule().replace('track via', 'track')]:
            accepted, errors = classify_native_body_rules(self.rules+bad)
            self.assertEqual(accepted, [])
            self.assertTrue(errors)

    def test_native_body_rule_indentation_is_not_semantic(self):
        rule = self.body_rule().replace('\n  ', '\n\t    ')
        self.assertEqual(check_internal_pad_rules(self.rules+rule), [])

    def u12_rule(self):
        return '(rule "U12 internal lands" (condition "A.Type == \'Pad\' && B.Type == \'Pad\' && A.Reference == \'U12\' && B.Reference == \'U12\'") (constraint clearance (min 0.45mm)))'

    def test_optional_reviewed_u12_does_not_change_archived_required_sixteen(self):
        self.assertEqual(check_internal_pad_rules(self.rules+self.u12_rule()),[])
        self.assertEqual(check_internal_pad_rules(self.rules),[])

    def test_u12_scope_and_lower_minimum_are_rejected(self):
        rule=self.u12_rule()
        for bad in [rule.replace("B.Type == 'Pad'","B.Type == 'Via'"),rule.replace("B.Reference == 'U12'","B.Reference == 'U13'"),rule.replace('0.45mm','0.2mm')]:
            self.assertTrue(check_internal_pad_rules(self.rules+bad))

    def test_archived_rule_blockers_are_exact(self):
        self.assertEqual(sorted(check_internal_pad_rules(self.actual_rules)), self.expected["internal_pad_rules"])

    def test_scope_cannot_include_tracks(self):
        mutated = self.rules.replace("A.Type == 'Pad'", "A.Type == 'Track'", 1)
        self.assertTrue(check_internal_pad_rules(mutated))

    def test_scope_cannot_cross_component_instances(self):
        mutated = self.rules.replace("B.Reference == 'Q1'", "B.Reference == 'Q2'", 1)
        self.assertTrue(check_internal_pad_rules(mutated))

    def test_minimum_cannot_be_reduced(self):
        self.assertTrue(
            check_internal_pad_rules(self.rules.replace("0.6mm", "0.01mm", 1))
        )

    def test_missing_rules_are_rejected(self):
        self.assertTrue(check_internal_pad_rules("(version 1)"))

    def test_archived_land_blockers_are_exact(self):
        board = (ARCHIVE / "ax7010_servo_reva.kicad_pcb").read_text(
            encoding="utf-8"
        )
        self.assertEqual(sorted(check(board)), self.expected["vendor_lands"])


if __name__ == "__main__":
    unittest.main()
