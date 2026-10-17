"""Generic hierarchy, geometry and visible wiring without servo assumptions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pcbtools.project import load_project
from pcbtools.schematic import discover_sheets, check_schematic

class SchematicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("top.kicad_sch")
        cfg={"schema_version":1,"id":"generic","root":".","schematic":"top.kicad_sch","output":"evidence","rule_sets":[],"parameters":{}}
        (self.root/"project.json").write_text(json.dumps(cfg))
        self.p=load_project(self.root/"project.json")
    def write(self, name, body=""):
        (self.root/name).write_text('(kicad_sch (version 20250114) (uuid "root") (paper "A4") (lib_symbols) '+body+')')
    def sheet(self,name,uuid):
        return f'(sheet (uuid "{uuid}") (property "Sheetfile" "{name}"))'
    def errors(self): return [f for f in check_schematic(self.p) if f.status=="FAIL"]
    def test_nested_hierarchy(self):
        self.write("leaf.kicad_sch")
        self.write("child.kicad_sch",self.sheet("leaf.kicad_sch","leaf"))
        self.write("top.kicad_sch",self.sheet("child.kicad_sch","child"))
        self.assertEqual(len(discover_sheets(self.p)),3)
    def test_missing_child_fails(self):
        self.write("top.kicad_sch",self.sheet("absent.kicad_sch","x"))
        self.assertTrue(self.errors())
    def test_cycle_fails(self):
        self.write("top.kicad_sch",self.sheet("top.kicad_sch","x"))
        self.assertTrue(self.errors())
    def test_repeated_source_instance_allowed(self):
        self.write("leaf.kicad_sch")
        self.write("top.kicad_sch",self.sheet("leaf.kicad_sch","x")+self.sheet("leaf.kicad_sch","y"))
        self.assertEqual(len(discover_sheets(self.p)),2)
    def test_duplicate_instance_path_fails(self):
        self.write("leaf.kicad_sch")
        self.write("top.kicad_sch",self.sheet("leaf.kicad_sch","x")+self.sheet("leaf.kicad_sch","x"))
        self.assertTrue(self.errors())
    def test_bad_parentheses(self):
        (self.root/"top.kicad_sch").write_text('(kicad_sch (version 1)')
        self.assertTrue(self.errors())
    def test_off_grid(self):
        self.write("top.kicad_sch",'(label "N" (at 10 10))')
        self.assertTrue(any(f.rule_id=="schematic.grid" for f in self.errors()))
    def test_floating_power_port(self):
        self.write("top.kicad_sch",'(hierarchical_label "VCC" (at 25.4 25.4))')
        self.assertTrue(any(f.rule_id=="schematic.power" for f in self.errors()))
    def test_generic_project_has_no_servo_rules(self):
        self.assertEqual(self.errors(),[])

if __name__=="__main__": unittest.main()
