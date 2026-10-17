"""Rule family registration must not leak board-specific requirements."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pcbtools.project import load_project, resolve_project
from pcbtools.rules import run_rules
from pcbtools.board import check_board
class RuleTests(unittest.TestCase):
    def test_generic_project_has_no_servo_rules(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            (p/"top.kicad_sch").write_text('(kicad_sch (version 20250114) (paper "A4") (lib_symbols))')
            (p/"config.json").write_text(json.dumps({"schema_version":1,"id":"other","root":".","schematic":"top.kicad_sch","output":"evidence","rule_sets":[]}))
            self.assertEqual(run_rules(load_project(p/"config.json"),"schematic",{}),[])
    def test_explicit_adc_profiles_do_not_leak(self):
        ads=run_rules(resolve_project("ads8588s"),"schematic",{})
        ad=run_rules(resolve_project("ad7606c"),"schematic",{})
        self.assertIn("adc.serial",[f.rule_id for f in ads])
        self.assertNotIn("adc.serial",[f.rule_id for f in ad])
        self.assertNotIn("adc.ad7606c",[f.rule_id for f in ads])
    def test_missing_netlist_not_pass(self):
        result=check_board(resolve_project("ads8588s"),None)
        self.assertTrue(any(f.status=="NOT_RUN" for f in result))
if __name__=="__main__":unittest.main()
