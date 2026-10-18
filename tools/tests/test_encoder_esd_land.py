import unittest
from pcbtools.rules.encoder import esd_land_errors


class EncoderEsdLandTests(unittest.TestCase):
    def setUp(self):
        self.raw = '(footprint "reviewed"\n' + '\n'.join(
            f'(pad "{i}" smd rect (at {x} {y}) (size .75 .25) (layers "F.Cu" "F.Paste" "F.Mask"))'
            for i,x,y in [(i+1,-.675,-1.5+.5*i) for i in range(7)]
                         + [(14-i,.675,-1.5+.5*i) for i in range(7)]) + ')'

    def test_reviewed_land(self):
        self.assertEqual([], esd_land_errors(self.raw))

    def test_reverting_to_020_width_fails_manufacturing_contract(self):
        self.assertTrue(esd_land_errors(self.raw.replace('(size .75 .25)', '(size .75 .20)')))

    def test_reversing_physical_pad_numbers_fails(self):
        self.assertTrue(esd_land_errors(self.raw.replace('(pad "1"', '(pad "14"', 1)))
