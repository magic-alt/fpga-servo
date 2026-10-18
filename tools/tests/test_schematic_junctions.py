from pathlib import Path
import sys
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.schematic import missing_wire_junctions


def wire(a, b):
    return f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})))'


class ExplicitJunctionTests(unittest.TestCase):
    def test_split_t_without_dot_is_rejected(self):
        text = wire((0, 0), (5, 0)) + wire((5, 0), (10, 0)) + wire((5, 0), (5, 5))
        self.assertEqual(missing_wire_junctions(text), [(5.0, 0.0)])

    def test_junction_at_t_passes(self):
        text = wire((0, 0), (5, 0)) + wire((5, 0), (10, 0)) + wire((5, 0), (5, 5))
        self.assertEqual(missing_wire_junctions(text + '(junction (at 5 0))'), [])

    def test_unconnected_four_way_crossing_not_joined(self):
        self.assertEqual(missing_wire_junctions(wire((0, 5), (10, 5)) + wire((5, 0), (5, 10))), [])

    def test_unsplit_wire_t_still_requires_dot(self):
        text = wire((0, 0), (10, 0)) + wire((5, 0), (5, 5))
        self.assertEqual(missing_wire_junctions(text), [(5.0, 0.0)])

    def test_corner_does_not_require_dot(self):
        self.assertEqual(missing_wire_junctions(wire((0, 0), (5, 0)) + wire((5, 0), (5, 5))), [])


if __name__ == '__main__': unittest.main()
