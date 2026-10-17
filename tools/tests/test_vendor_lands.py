import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Regressions for local rules that must never change external routing clearance."""

from pathlib import Path
import unittest
import json
from pcbtools.rules.power_layout import vendor_api
_family = vendor_api()
check = _family.check
check_internal_pad_rules = _family.check_internal_pad_rules

ROOT = Path(__file__).resolve().parents[2]


class VendorLandsTests(unittest.TestCase):
    def setUp(self):
        self.actual_rules = (ROOT / "hardware/ads8588s_servo/ax7010_servo_reva.kicad_dru").read_text(encoding="utf-8")
        self.expected = json.loads((ROOT / "hardware/ads8588s_servo/evidence/pcb_ci_baseline.json").read_text(encoding="utf-8"))["snapshot"]
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
        board = (ROOT / "hardware/ads8588s_servo/ax7010_servo_reva.kicad_pcb").read_text(
            encoding="utf-8"
        )
        self.assertEqual(sorted(check(board)), self.expected["vendor_lands"])


if __name__ == "__main__":
    unittest.main()
