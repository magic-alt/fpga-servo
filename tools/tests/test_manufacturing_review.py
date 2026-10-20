"""Review export never grants manufacturing release; reject damaged output files."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))


class ReviewValidationTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('gerbonara'), 'Independent CAM parser required')
    def test_independent_parser_api_reads_copper_without_newer_cli_commands(self):
        source = self.root / 'line.gbr'
        source.write_text('%FSLAX46Y46*%\n%MOMM*%\n%ADD10C,0.100*%\nD10*\nX0Y0D02*\nX10000000Y0D01*\nM02*\n')
        result = self.api().independent_cam_file(source, self.root / 'line.svg')
        self.assertEqual(result['object_count'], 1)
        self.assertAlmostEqual(result['independent_bounds_mm'][0], -.05)
        self.assertAlmostEqual(result['independent_bounds_mm'][2], 10.05)
        self.assertIn('<svg', (self.root / 'line.svg').read_text())

    @unittest.skipUnless(importlib.util.find_spec('gerbonara'), 'Independent CAM parser required')
    def test_independent_drill_parser_matches_metric_coordinates_and_diameter(self):
        source = self.root / 'hole-PTH.drl'
        source.write_text('M48\nMETRIC\nT1C0.300\n%\nG90\nG05\nT1\nX12.5Y-8.25\nM30\n')
        result = self.api().independent_cam_file(source, self.root / 'hole.svg', plated=True)
        self.assertEqual(result['holes'], [(12.5, -8.25, .3, True)])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def api(self):
        from pcbtools import manufacturing_review
        return manufacturing_review

    def test_new_kind_is_distinct_from_approved_fabrication(self):
        from pcbtools.cli import parser
        args = parser().parse_args(['export', '--project', 'ad7606c', '--kind', 'fabrication-review'])
        self.assertEqual(args.kind, 'fabrication-review')
        self.assertEqual(parser().parse_args(['export', '--project', 'ad7606c', '--kind', 'fabrication']).kind, 'fabrication')

    def test_bad_or_truncated_pdf_does_not_pass(self):
        for payload in (b'not a PDF', b'%PDF-1.5\ntruncated', b'%PDF-1.5\n%%EOF'):
            p = self.root / 'bad.pdf';p.write_bytes(payload)
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.api().validate_pdf(p, 1)

    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'pypdf is required in manufacturing-review CI')
    def test_correct_page_count_but_blank_pdf_fails(self):
        from pypdf import PdfWriter
        w = PdfWriter();w.add_blank_page(width=100,height=100)
        p = self.root/'blank.pdf'
        with p.open('wb') as f:w.write(f)
        with self.assertRaises(ValueError):self.api().validate_pdf(p, 1)

    @unittest.skipUnless(importlib.util.find_spec('pypdf'), 'pypdf is required in manufacturing-review CI')
    def test_real_content_pdf_and_page_count(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject
        w=PdfWriter();page=w.add_blank_page(width=100,height=100)
        stream=DecodedStreamObject();stream.set_data(b'0 0 m 90 90 l S')
        page[NameObject('/Contents')]=w._add_object(stream)
        p=self.root/'content.pdf'
        with p.open('wb') as f:w.write(f)
        self.assertEqual(self.api().validate_pdf(p, 1)['pages'],1)
        with self.assertRaises(ValueError):self.api().validate_pdf(p, 2)
        p.write_bytes(p.read_bytes()[:-12])
        with self.assertRaises(ValueError):self.api().validate_pdf(p, 1)

    def test_decimal_excellon_holes_and_termination(self):
        text='M48\n; #@! TF.FileFunction,Plated,1,4,PTH\nMETRIC\nT1C0.300\n%\nG90\nG05\nT1\nX12.500Y-8.250\nX13.0Y-8.250\nT0\nM30\n'
        self.assertEqual(self.api().parse_decimal_drill(text, True),[(12.5,-8.25,.3,True),(13.,-8.25,.3,True)])
        for bad in (text.replace('M30',''),text.replace('METRIC','INCH'),text.replace('T1\nX','T2\nX'),text.replace('X12.500Y-8.250','G85X12.500Y-8.250')):
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.api().parse_decimal_drill(bad, True)

    def test_real_kicad_format2_header_and_empty_npth(self):
        text = 'M48\n; #@! TF.FileFunction,Plated,1,4,PTH\nFMAT,2\nMETRIC\nT1C0.300\n%\nG90\nG05\nT1\nX12.5Y-8.25\nM30\n'
        self.assertEqual(self.api().parse_decimal_drill(text, True), [(12.5, -8.25, .3, True)])
        empty = 'M48\n; #@! TF.FileFunction,NonPlated,1,4,NPTH\nFMAT,2\nMETRIC\n%\nG90\nG05\nM30\n'
        self.assertEqual(self.api().parse_decimal_drill(empty, False), [])
        for bad in (text.replace('FMAT,2', 'FMAT,1'), text.replace('FMAT,2', 'FMAT,2\nFMAT,2'), text.replace('G05', 'G05\nFMAT,2')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.api().parse_decimal_drill(bad, True)

    def test_drill_plating_attribute_cannot_contradict_requested_file(self):
        text = 'M48\n; #@! TF.FileFunction,NonPlated,1,4,NPTH\nMETRIC\n%\nG90\nG05\nM30\n'
        with self.assertRaises(ValueError):self.api().parse_decimal_drill(text, True)

    def test_native_half_grid_rounding_is_not_a_missing_hole(self):
        compare = getattr(self.api(), 'compare_drill_holes', None)
        self.assertTrue(callable(compare))
        native = [(118.0875, -29., .4, True), (36.2886, -40.2015, .3, True)]
        exported = [(118.087, -29., .4, True), (36.289, -40.201, .3, True)]
        result = compare(native, exported)
        self.assertEqual(result['matched_holes'], 2)
        self.assertAlmostEqual(result['maximum_xy_quantization_mm'], .0005)
        for bad in (exported[:1], exported + [exported[0]],
                    [(118.0869, -29., .4, True), exported[1]],
                    [(118.087, -29., .3, True), exported[1]],
                    [(118.087, -29., .4, False), exported[1]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):compare(native, bad)

    def test_ambiguous_overlapping_drill_matches_fail(self):
        compare = getattr(self.api(), 'compare_drill_holes', None)
        self.assertTrue(callable(compare))
        holes = [(1., 2., .3, True)] * 2
        with self.assertRaises(ValueError):compare(holes, holes)

    def test_cam_terminator_is_not_just_a_nonempty_file(self):
        p=self.root/'layer.gbr';p.write_text('G04 test*\nM02*\n')
        self.api().check_cam_terminator(p)
        p.write_text('G04 truncated*\n')
        with self.assertRaises(ValueError):self.api().check_cam_terminator(p)

class ReviewBoundaryTests(unittest.TestCase):
    def test_only_missing_human_reviews_are_reported_not_bypassed_static_errors(self):
        from pcbtools.report import Finding
        from pcbtools.manufacturing import REQUIRED_REVIEWS
        from pcbtools.manufacturing_review import validate_review_conditions
        rows = [Finding('prototype.native_settings','PASS',''), Finding('prototype.stackup','PASS','')]
        rows += [Finding('prototype.review.'+name,'FAIL','Missing human review') for name in REQUIRED_REVIEWS]
        self.assertEqual(len(validate_review_conditions(rows)), len(rows))
        for rule in ('prototype.profile','prototype.stackup','prototype.review.unregistered'):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                validate_review_conditions(rows+[Finding(rule,'FAIL','Actual static failure')])

if __name__=='__main__':unittest.main()
