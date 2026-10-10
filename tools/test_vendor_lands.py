"""Regressions for local rules that must never change external routing clearance."""

from pathlib import Path
import unittest
from check_vendor_lands import check, check_internal_pad_rules

ROOT = Path(__file__).resolve().parents[1]


class VendorLandsTests(unittest.TestCase):
    def setUp(self):
        self.rules = (ROOT / "hardware/ax7010_servo_reva.kicad_dru").read_text(
            encoding="utf-8"
        )

    def test_actual_reviewed_rules(self):
        self.assertEqual(check_internal_pad_rules(self.rules), [])

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

    def test_actual_ti_lands(self):
        board = (ROOT / "hardware/ax7010_servo_reva.kicad_pcb").read_text(
            encoding="utf-8"
        )
        self.assertEqual(check(board), [])


if __name__ == "__main__":
    unittest.main()
