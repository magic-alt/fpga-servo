import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from board_parity_audit import parse_board, parse_netlist, audit

XML = '''<?xml version="1.0" encoding="utf-8"?>
<export version="E"><components>
<comp ref="U1"><value>TEST</value><footprint>Package_SO:SOIC-8</footprint></comp>
<comp ref="R1"><value>5mR</value><footprint></footprint></comp>
</components><nets><net name="GND" code="1"/><net name="TEST" code="2"/></nets></export>'''
PCB = '''(kicad_pcb (version 20221018) (generator pcbnew)
  (net 1 "GND")
  (footprint "fake:footprint" (layer "F.Cu")
    (property "Reference" "U1" (at 0 0) (layer "F.SilkS"))
    (pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND"))
  )
  (footprint "fake:hole" (property "Reference" "H1" (at 0 0) (layer "F.SilkS")))
  (segment (start 0 0) (end 1 1) (width 0.25) (layer "F.Cu") (net 1))
  (gr_rect (start 0 0) (end 10 10) (layer "Edge.Cuts"))
)'''


class StaticBoardAuditTest(unittest.TestCase):
    def test_difference_counts(self):
        with TemporaryDirectory() as temp:
            t = Path(temp)
            (t / 'a.xml').write_text(XML, encoding='utf-8')
            (t / 'a.kicad_pcb').write_text(PCB, encoding='utf-8')
            n = parse_netlist(t / 'a.xml')
            b = parse_board(t / 'a.kicad_pcb')
            x = audit(n, b)
            self.assertEqual(x['missing_pcb_references'], ['R1'])
            self.assertEqual(x['pcb_only_mechanical'], ['H1'])
            self.assertEqual(x['schematic_symbols_missing_footprint'], ['R1'])
            self.assertEqual(x['pcb_tracks'], 1)
            self.assertEqual(x['pcb_vias'], 0)
            self.assertEqual(x['pcb_nets'], 1)
            self.assertIn('TEST', x['schematic_net_names_absent_from_board'])
            self.assertTrue(x['blocking'])

    def test_kicad10_embedded_nets_without_top_level_table(self):
        modern = PCB.replace('(net 1 "GND")', '(net "GND")')
        modern = modern.replace('  (net "GND")\n', '', 1)
        modern = modern.replace('(net 1))', '(net "GND"))')
        modern = modern.replace('(version 20221018)', '(version 20260206)')
        modern = modern.replace('  (segment', '  (zone (net "ZONE_ONLY"))\n  (segment')
        with TemporaryDirectory() as temp:
            p = Path(temp) / 'modern.kicad_pcb'
            p.write_text(modern, encoding='utf-8')
            b = parse_board(p)
            self.assertEqual(set(b['net_names'].values()), {'GND', 'ZONE_ONLY'})
            self.assertEqual(b['net_count'], 2)
            self.assertEqual(b['tracks'], 1)

    def test_kicad_escaped_hierarchy_slash_matches_xml(self):
        with TemporaryDirectory() as temp:
            t = Path(temp)
            (t / 'a.xml').write_text(XML.replace('GND', '/Gate Driver / Inverter/GND'), encoding='utf-8')
            (t / 'a.kicad_pcb').write_text(PCB.replace('GND', '/Gate Driver {slash} Inverter/GND'), encoding='utf-8')
            x = audit(parse_netlist(t / 'a.xml'), parse_board(t / 'a.kicad_pcb'))
            self.assertNotIn('/Gate Driver / Inverter/GND', x['schematic_net_names_absent_from_board'])

    def test_quoted_parentheses_are_safe(self):
        with TemporaryDirectory() as temp:
            t = Path(temp) / 'b.kicad_pcb'
            t.write_text(PCB.replace('"fake:footprint"', '"fake:fp(test)"'), encoding='utf-8')
            b = parse_board(t)
            self.assertEqual(b['footprints']['U1']['lib_id'], 'fake:fp(test)')


if __name__ == '__main__':
    unittest.main()
