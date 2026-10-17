"""Development workflows must preserve sources and isolate historical tools."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.development import develop
from pcbtools.report import exit_code
class DevelopmentTests(unittest.TestCase):
    def setUp(self): self.p=resolve_project("ads8588s")
    def digest(self):return hashlib.sha256(self.p.board.read_bytes()).hexdigest()
    def test_preview_changes_no_source_bytes(self):
        before=self.digest()
        with tempfile.TemporaryDirectory() as folder:
            r=develop(self.p,"snapshot",False,Path(folder))
            self.assertEqual(exit_code(r),0)
            self.assertFalse(list(Path(folder).rglob("*.kicad_pcb")))
        self.assertEqual(before,self.digest())
    def test_snapshot_is_non_overwriting(self):
        before=self.digest()
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(2): self.assertEqual(exit_code(develop(self.p,"snapshot",True,Path(folder))),0)
            self.assertEqual(len(list(Path(folder).rglob("snapshot.json"))),2)
            for p in Path(folder).rglob("*.kicad_pcb"):self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),before)
        self.assertEqual(before,self.digest())
    def test_snapshot_includes_local_library_dependencies(self):
        from pcbtools.project import load_project
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"top.kicad_sch").write_text('(kicad_sch (version 20250114) (paper "A4") (lib_symbols))')
            (root/"sym-lib-table").write_text('(sym_lib_table)')
            (root/"fp-lib-table").write_text('(fp_lib_table (lib (name "Local") (uri "${KIPRJMOD}/Local.pretty")))')
            (root/"Local.pretty").mkdir()
            (root/"Local.pretty/Land.kicad_mod").write_text('(footprint "Land")')
            (root/"config.json").write_text(json.dumps({"schema_version":1,"id":"local","root":".","schematic":"top.kicad_sch","output":"evidence","rule_sets":[]}))
            p=load_project(root/"config.json")
            r=develop(p,"snapshot",True,p.output)
            self.assertEqual(exit_code(r),0)
            plan=json.loads(next(p.output.glob("*/snapshot.json")).read_text())
            names={x["source"] for x in plan}
            self.assertTrue({"sym-lib-table","fp-lib-table","Local.pretty/Land.kicad_mod"}<=names,names)
    def test_sync_apply_rejected(self):
        before=self.digest()
        with tempfile.TemporaryDirectory() as folder:
            r=develop(self.p,"sync",True,Path(folder))
            self.assertNotEqual(exit_code(r),0)
        self.assertEqual(before,self.digest())
    def test_check_does_not_import_pcbnew_or_archive(self):
        code="from pcbtools.schematic import check_schematic; import sys; assert 'pcbnew' not in sys.modules; assert not any('archive' in p for p in sys.modules)"
        result=subprocess.run([sys.executable,"-c",code],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
if __name__=="__main__":unittest.main()
