"""OEM identity and physical pin mapping must survive library updates."""
import sys
import unittest
from dataclasses import replace
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.rules.protection import gate_driver_symbol_errors


class GateDriverSymbolTests(unittest.TestCase):
    def test_both_projects_use_actual_driver_definition(self):
        for name in ('ads8588s', 'ad7606c'):
            with self.subTest(project=name):
                self.assertEqual(gate_driver_symbol_errors(resolve_project(name)), [])

    def test_old_device_identity_is_rejected(self):
        from pcbtools.kicad import direct_child_forms
        project = resolve_project('ads8588s')
        text = (project.schematic.parent / 'gate_inverter.kicad_sch').read_text(encoding='utf-8')
        self.assertTrue(any('DRV8300D' in f.text for f in direct_child_forms(text, 'symbol')))
        self.assertTrue(gate_driver_symbol_errors(project, source_text=text.replace('DRV8300D', 'FD6288T')))

    def test_plausible_swapped_phase_pins_are_rejected(self):
        project = resolve_project('ads8588s')
        text = (project.schematic.parent / 'gate_inverter.kicad_sch').read_text(encoding='utf-8')
        swapped = text.replace('(name "INHA"', '(name "INHB"', 1)
        self.assertTrue(text != swapped, 'Expected INHA pin definition for mutation')
        self.assertTrue(gate_driver_symbol_errors(project, source_text=swapped))

    def test_legal_lib_id_whitespace_is_accepted(self):
        project = resolve_project('ads8588s')
        text = (project.schematic.parent / 'gate_inverter.kicad_sch').read_text(encoding='utf-8')
        text = text.replace('(lib_id "ax7010_servo_reva:DRV8300D")',
                            '(lib_id\n "ax7010_servo_reva:DRV8300D"\n)')
        self.assertEqual(gate_driver_symbol_errors(project, source_text=text), [])

    def test_library_only_pin_swap_is_rejected(self):
        project = resolve_project('ads8588s')
        text = project.libraries[0].read_text(encoding='utf-8')
        swapped = text.replace('(name "INHA"', '(name "INHB"', 1)
        self.assertTrue(text != swapped)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as folder:
            library = Path(folder) / 'changed.kicad_sym'
            library.write_text(swapped, encoding='utf-8')
            errors = gate_driver_symbol_errors(replace(project, libraries=(library,)))
        self.assertTrue(any('library' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
