"""Native tools are untrusted until their reports establish complete evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
from pcbtools.kicad import run_native
from pcbtools.verification import verify, native_summary
from pcbtools.report import exit_code
from pcbtools.export import export_project
class WorkflowTests(unittest.TestCase):
    def test_missing_executable(self):
        r=run_native(["nonexistent-pcb-tool-20261017"],Path.cwd(),1)
        self.assertNotEqual(r["exit_code"],0)
        self.assertEqual(r["status"],"NOT_RUN")
    def test_timeout(self):
        r=run_native([sys.executable,"-c","import time; time.sleep(2)"],Path.cwd(),.05)
        self.assertNotEqual(r["exit_code"],0)
        self.assertIn("Timeout",r["error"])
    def test_incomplete_erc_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"erc.json"
            path.write_text(json.dumps({"sheets":[{}]}))
            self.assertEqual(native_summary("erc",path,0).status,"FAIL")
    def test_complete_empty_erc_passes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"erc.json"
            path.write_text(json.dumps({"sheets":[{"violations":[]}]}))
            self.assertEqual(native_summary("erc",path,0).status,"PASS")
    def test_erc_exclusion_is_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"erc.json"
            path.write_text(json.dumps({"sheets":[{"violations":[{"severity":"error","excluded":True}]}]}))
            r=native_summary("erc",path,0)
            self.assertEqual(r.status,"FAIL")
            self.assertEqual(r.details["exclusions"],1)
    def test_repeat_isolation_and_stale_netlist(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            (out/"netlist.xml").write_text("historical")
            for _ in range(2):
                r=verify(resolve_project("ads8588s"),"schematic",out,{"kicad-cli":"nonexistent-pcb-tool-20261017"})
                self.assertEqual(exit_code(r),1)
            self.assertEqual(len(list(out.glob("*/manifest.json"))),2)
            self.assertEqual((out/"netlist.xml").read_text(),"historical")
            for m in out.glob("*/manifest.json"):
                d=json.loads(m.read_text())
                self.assertEqual(d["evidence"]["pcb_release"],"BLOCKED")
                self.assertEqual(d["evidence"]["source_hashes_before"],d["evidence"]["source_hashes_after"])
    def test_space_in_executable_path(self):
        # subprocess argument lists preserve spaces without invoking a shell.
        r=run_native([sys.executable,"-c","import sys; print(sys.argv[1])","a b c"],Path.cwd(),2)
        self.assertEqual(r["stdout"].strip(),"a b c")
    def test_export_cannot_overwrite_sources(self):
        p=resolve_project("ads8588s")
        with self.assertRaises(ValueError): export_project(p,"bom",p.schematic.parent,{})
if __name__=="__main__":unittest.main()
