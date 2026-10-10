"""Native regression tests for four-terminal shunt topology protection.

Run with KiCad's pcbnew-capable Python. Tests never save or modify design files.
"""

import unittest
from pathlib import Path
import pcbnew as p
from check_pcb_kelvin import audit, check_internal_groups

ROOT = Path(__file__).resolve().parents[1]


class KelvinRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.board = p.LoadBoard(str(ROOT / "hardware/ax7010_servo_reva.kicad_pcb"))
        cls.footprints = {f.GetReference(): f for f in cls.board.GetFootprints()}
        cls.sources = [
            (ROOT / "hardware" / name).read_text(encoding="utf-8")
            for name in [
                "ax7010_servo_reva.kicad_pcb",
                "ax7010_servo_reva.kicad_sym",
                "gate_inverter.kicad_sch",
                "fpga-servo.pretty/Ohmite_650_4T_P25.40x6.35mm.kicad_mod",
            ]
        ]

    def test_all_sense_branches_are_isolated(self):
        rows, errors = audit(self.board)
        self.assertFalse(errors, errors)
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["passed"] for row in rows))

    def test_each_external_force_sense_bridge_is_detected(self):
        for ref in ["RSH1", "RSH2", "RSH3"]:
            for force, sense in [("1", "3"), ("2", "4")]:
                with self.subTest(shunt=ref, force=force, sense=sense):
                    pads = {v.GetNumber(): v for v in self.footprints[ref].Pads()}
                    bridge = p.PCB_TRACK(self.board)
                    bridge.SetLayer(p.F_Cu)
                    bridge.SetStart(pads[force].GetPosition())
                    bridge.SetEnd(pads[sense].GetPosition())
                    bridge.SetWidth(p.FromMM(0.2))
                    bridge.SetNetCode(pads[sense].GetNetCode())
                    self.board.Add(bridge)
                    try:
                        rows, errors = audit(self.board)
                        self.assertTrue(errors)
                        failed = [row for row in rows if not row["passed"]]
                        self.assertEqual(len(failed), 1)
                        self.assertIn(ref + "." + sense, failed[0]["expected_pads"])
                        self.assertIn(ref + "." + force, failed[0]["actual_pads"])
                    finally:
                        self.board.Remove(bridge)

    def test_manufacturer_internal_pairs(self):
        self.assertEqual(check_internal_groups(*self.sources), [])

    def test_crossed_or_missing_internal_pairs_are_rejected(self):
        import re

        for index in range(4):
            with self.subTest(source=index):
                sources = list(self.sources)
                key = "jumper_pad_groups" if index in [0, 3] else "jumper_pin_groups"
                sources[index], count = re.subn(
                    r"\(" + key + r'\s+\("1" "3"\)\s+\("2" "4"\)\s*\)',
                    "(" + key + ' ("1" "4") ("2" "3"))',
                    sources[index],
                )
                self.assertGreater(count, 0)
                self.assertTrue(check_internal_groups(*sources))


if __name__ == "__main__":
    unittest.main()
