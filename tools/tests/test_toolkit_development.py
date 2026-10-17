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
