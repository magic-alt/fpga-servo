"""Manufactured copper and via treatments must match the actual selected process."""
from pathlib import Path
import re
import sys
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.rules.fabrication_intent import board_errors, rpj_errors, check_project
from pcbtools.project import resolve_project
from pcbtools.kicad import extract_forms, direct_child_forms, head_string, property_value


class FabricationIntentTests(unittest.TestCase):
    def test_both_actual_boards_specify_full_fill_and_copper_cap(self):
        for name in ('ads8588s', 'ad7606c'):
            project = resolve_project(name)
            setup = extract_forms(project.board.read_text(), 'setup')[0].text
            with self.subTest(project=name):
                self.assertEqual([f.text for f in direct_child_forms(setup, 'filling')], ['(filling yes)'])
                self.assertEqual([f.text for f in direct_child_forms(setup, 'capping')], ['(capping yes)'])

    def test_both_u13_lands_are_not_below_fab_minimum(self):
        for name in ('ads8588s', 'ad7606c'):
            project = resolve_project(name)
            footprint = next(f.text for f in extract_forms(project.board.read_text(), 'footprint')
                             if property_value(f.text, 'Reference') == 'U13')
            for pad in extract_forms(footprint, 'pad'):
                if head_string(pad.text, 'pad'):
                    size = re.search(r'\(size ([\d.]+) ([\d.]+)\)', pad.text)
                    with self.subTest(project=name, pad=head_string(pad.text, 'pad')):
                        self.assertGreaterEqual(min(float(size[1]), float(size[2])), .25)

    def test_original_stencil_is_separate_from_enlarged_copper(self):
        for name in ('ads8588s', 'ad7606c'):
            project = resolve_project(name)
            footprint = next(f.text for f in extract_forms(project.board.read_text(), 'footprint')
                             if property_value(f.text, 'Reference') == 'U13')
            paste_only = [p for p in extract_forms(footprint, 'pad')
                          if head_string(p.text, 'pad') == '' and '"F.Paste"' in p.text]
            with self.subTest(project=name):
                self.assertEqual(len(paste_only), 6)
                self.assertTrue(all(re.search(r'\(size (?:0.65|1) 0.2\)', p.text) for p in paste_only))

class FabricationIntentNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = resolve_project('ads8588s')
        cls.board = cls.project.board.read_text()
        cls.rpj = next(f.text for f in extract_forms(cls.board, 'footprint')
                       if property_value(f.text, 'Reference') == 'U13')

    def test_both_current_projects_pass_the_integrated_guard(self):
        for name in ('ads8588s', 'ad7606c'):
            with self.subTest(project=name):
                self.assertEqual(check_project(resolve_project(name)), [])

    def test_global_tenting_cannot_replace_filling_or_capping(self):
        for key in ('filling', 'capping'):
            bad = self.board.replace(f'({key} yes)', f'({key} no)', 1)
            with self.subTest(key=key):
                self.assertTrue(any(key in e for e in board_errors(bad)))

    def test_per_via_no_override_cannot_hide_behind_global_yes(self):
        via = extract_forms(self.board, 'via')[0].text
        for key in ('filling', 'capping'):
            replacement = via[:-1] + f'\n({key} no))'
            bad = self.board.replace(via, replacement, 1)
            with self.subTest(key=key):
                self.assertTrue(any('override' in e for e in board_errors(bad)))

    def test_small_generic_copper_is_not_exempted(self):
        bad = self.board.replace('(size 0.65 0.25)', '(size 0.65 0.2)', 1)
        self.assertTrue(any('below' in e for e in board_errors(bad)))

    def test_enlarging_stencil_with_copper_is_rejected(self):
        bad = self.rpj.replace('(size 0.65 0.2)', '(size 0.65 0.25)', 1)
        self.assertTrue(any('stencil' in e for e in rpj_errors(bad)))

    def test_displacing_copper_from_oem_terminal_center_is_rejected(self):
        copper = next(p.text for p in extract_forms(self.rpj, 'pad') if head_string(p.text, 'pad') == '1')
        bad = self.rpj.replace(copper, copper.replace('(at -0.625 -0.25)', '(at -0.525 -0.25)', 1), 1)
        self.assertTrue(any('centers' in e for e in rpj_errors(bad)))

    def test_paste_apertures_cannot_acquire_electrical_pin_numbers(self):
        bad = self.rpj.replace('(pad "" smd', '(pad "10" smd', 1)
        self.assertTrue(any('unnumbered' in e for e in rpj_errors(bad)))

    def test_missing_paste_aperture_is_rejected(self):
        pad = next(p.text for p in extract_forms(self.rpj, 'pad')
                   if head_string(p.text, 'pad') == '')
        self.assertTrue(any('stencil' in e for e in rpj_errors(self.rpj.replace(pad, '', 1))))


class U13GroundEscapeTests(unittest.TestCase):
    def test_round_trace_end_does_not_reduce_u13_pad5_clearance(self):
        for name in ('ads8588s', 'ad7606c'):
            project = resolve_project(name)
            track = next(f.text for f in extract_forms(project.board.read_text(), 'segment')
                         if '34834ed3-1620-463c-9558-62f367a32011' in f.text)
            start = re.search(r'\(start ([\d.]+) ([\d.]+)\)', track)
            width = float(re.search(r'\(width ([\d.]+)\)', track)[1])
            # Ground pad4 center Y=14.75, height0.25; pad5 ends atY=14.375.
            # Include the round trace endcap, not only its centerline.
            with self.subTest(project=name):
                self.assertGreaterEqual(float(start[2]) - width/2 - 14.375, .25 - 1e-9)
                self.assertLessEqual(abs(float(start[2]) - 14.75), .125)
                self.assertEqual(float(start[1]), 32.45)
                self.assertIn('(end 32.45 15.2)', track)
                self.assertIn('(net "/GND")', track)


class ZoneCacheEquivalenceTests(unittest.TestCase):
    def test_only_native_fill_cache_and_generator_can_change(self):
        from pcbtools.board import non_fill_design_signature
        before = '(kicad_pcb (generator pcbnew) (generator_version "10.0.3") (segment (start 1 2) (end 3 4) (width 0.25)) (zone (net 1) (polygon (pts (xy 0 0) (xy 1 0))) (filled_polygon (layer "F.Cu") (pts (xy 0 0) (xy 1 0)))))'
        after = before.replace('10.0.3', '10.0.7').replace('(filled_polygon (layer "F.Cu") (pts (xy 0 0) (xy 1 0)))', '(filled_polygon (layer "F.Cu") (pts (xy .5 0) (xy 1 0)))')
        self.assertEqual(non_fill_design_signature(before), non_fill_design_signature(after))
        for bad in (after.replace('(width 0.25)', '(width 0.20)'), after.replace('(net 1)', '(net 2)'), after.replace('(polygon (pts (xy 0 0)', '(polygon (pts (xy 0.1 0)')):
            self.assertNotEqual(non_fill_design_signature(before), non_fill_design_signature(bad))

    def test_native_pad_serialization_order_is_not_a_design_change(self):
        from pcbtools.board import non_fill_design_signature as signature
        pad1 = '(pad "1" smd rect (at 1 2) (size .25 .65) (layers "F.Cu") (net "A"))'
        pad2 = '(pad "" smd rect (at 1 2) (size .2 .65) (layers "F.Paste"))'
        first = '(kicad_pcb (footprint "U13" ' + pad1 + ' (embedded_fonts no) ' + pad2 + '))'
        saved = '(kicad_pcb (footprint "U13" ' + pad2 + ' ' + pad1 + ' (embedded_fonts no)))'
        self.assertEqual(signature(first), signature(saved))
        for bad in (saved.replace('(at 1 2)', '(at 1 3)', 1), saved.replace('(net "A")', '(net "B")'), saved.replace(pad2, '')):
            self.assertNotEqual(signature(first), signature(bad))

    def test_invalid_or_empty_board_is_not_equivalent(self):
        from pcbtools.board import non_fill_design_signature
        for value in ('', '(kicad_pcb', '(something_else)', '(kicad_pcb) garbage'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                non_fill_design_signature(value)


if __name__ == "__main__":
    unittest.main()
