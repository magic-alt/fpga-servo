"""TI SLLS849E p3: PW16 pin numbering must not be inferred from drawing order."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.kicad import extract_forms, head_string

PINOUT = {'1A+': '2', '1A-': '1', '1Y': '3', '2A+': '6', '2A-': '7',
          '2Y': '5', '3A+': '10', '3A-': '9', '3Y': '11', '4A+': '14',
          '4A-': '15', '4Y': '13', 'G': '4', 'G_N': '12', 'GND': '8', 'VCC': '16'}

def actual(text, alias):
    symbol = next(f.text for f in extract_forms(text, 'symbol') if head_string(f.text, 'symbol') == alias)
    return {head_string(extract_forms(p.text, 'name')[0].text, 'name'):
            head_string(extract_forms(p.text, 'number')[0].text, 'number')
            for p in extract_forms(symbol, 'pin')}

class EncoderPinTests(unittest.TestCase):
    def test_daily_rule_rejects_old_symbol_even_with_matching_pin_count(self):
        from pcbtools.rules.encoder import pinout_errors
        text = resolve_project('ads8588s').libraries[0].read_text(encoding='utf-8')
        self.assertEqual(pinout_errors(text, 'AM26LV32E'), [])
        symbol = next(f.text for f in extract_forms(text, 'symbol') if head_string(f.text, 'symbol') == 'AM26LV32E')
        pin = next(p.text for p in extract_forms(symbol, 'pin')
                   if head_string(extract_forms(p.text, 'name')[0].text, 'name') == 'G')
        self.assertTrue(pinout_errors(text.replace(pin, pin.replace('(number "4"', '(number "7"'), 1), 'AM26LV32E'))

    def test_library_and_embedded_pin_names_match_ti_pw16(self):
        for name in ('ads8588s', 'ad7606c'):
            project = resolve_project(name)
            for path, alias in ((project.libraries[0], 'AM26LV32E'),
                                (project.schematic.parent/'encoder.kicad_sch', 'ax7010_servo_reva:AM26LV32E')):
                with self.subTest(project=name, source=path.name):
                    self.assertEqual(actual(path.read_text(encoding='utf-8'), alias), PINOUT)

if __name__ == '__main__':
    unittest.main()
