from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.schematic import implicit_wire_widths


class WireWidthTests(unittest.TestCase):
    def test_default_zero_width_rejected(self):
        self.assertEqual(len(implicit_wire_widths('(wire (stroke (width 0)))')), 1)

    def test_missing_width_rejected(self):
        self.assertEqual(len(implicit_wire_widths('(wire (pts (xy 0 0) (xy 1 0)))')), 1)

    def test_explicit_old_default_width_accepted(self):
        self.assertEqual(implicit_wire_widths('(wire (stroke (width 0.1524)))'), [])

    def test_only_wire_strokes_checked(self):
        self.assertEqual(implicit_wire_widths('(polyline (stroke (width 0)))'), [])


if __name__ == '__main__':
    unittest.main()
