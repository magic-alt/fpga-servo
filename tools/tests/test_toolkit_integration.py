"""Delivery contract: one entry, usable docs/CI and no lost regressions."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
ROOT=Path(__file__).resolve().parents[2]
class IntegrationTests(unittest.TestCase):
    def test_single_daily_entry(self):
        self.assertEqual([p.name for p in (ROOT/"tools").glob("*.py")],["pcb.py"])
    def test_ci_uses_shared_entry(self):
        for name in ("hardware-sanity.yml","kicad-erc.yml","gate-ab-electrical.yml"):
            t=(ROOT/".github/workflows"/name).read_text()
            self.assertIn("tools/pcb.py",t)
            self.assertNotRegex(t,r"tools/(?:check_|test_|run_gate_ab)")
    def test_docs_have_current_and_archive_indexes(self):
        for rel in ("docs/README.md","docs/archive/README.md","docs/pcb_toolkit.md","docs/pcb_toolkit_extension.md"):
            self.assertTrue((ROOT/rel).is_file(),rel)
    def test_external_project_cli_without_servo_rules(self):
        with tempfile.TemporaryDirectory(prefix="external board ") as folder:
            p=Path(folder)
            (p/"top.kicad_sch").write_text('(kicad_sch (version 20250114) (uuid "root") (paper "A4") (lib_symbols))')
            (p/"config.json").write_text(json.dumps({"schema_version":1,"id":"sensor","root":".","schematic":"top.kicad_sch","output":"evidence","rule_sets":[]}))
            r=subprocess.run([sys.executable,str(ROOT/"tools/pcb.py"),"check","--config",str(p/"config.json"),"--scope","schematic"],cwd=p,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertNotIn("servo.",r.stdout)
    def test_active_docs_local_links(self):
        paths=[ROOT/"README.md",ROOT/"AGENTS.md",*(ROOT/"docs").glob("*.md"),*(ROOT/"hardware").glob("*/README.md")]
        failures=[]
        for path in paths:
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding="utf-8-sig")):
                link=link.strip("<>").split("#",1)[0]
                if not link or re.match(r"[a-zA-Z]+://",link):continue
                target=(path.parent/link).resolve()
                if not target.exists():failures.append(f"{path.relative_to(ROOT)}: {link}")
        self.assertEqual(failures,[])
    def test_check_fails_for_missing_board(self):
        r=subprocess.run([sys.executable,str(ROOT/"tools/pcb.py"),"check","--project","ad7606c","--scope","pcb"],capture_output=True,text=True)
        self.assertEqual(r.returncode,64)
    def test_static_lane_needs_no_native_tool(self):
        r=subprocess.run([sys.executable,str(ROOT/"tools/pcb.py"),"test","--lane","static","--pattern","test_toolkit_core.py","--kicad-cli","absent-kicad"],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_explicit_native_interpreter_missing_pcbnew_fails(self):
        import importlib.util
        if importlib.util.find_spec("pcbnew") is not None: self.skipTest("Current interpreter has native bindings")
        r=subprocess.run([sys.executable,str(ROOT/"tools/pcb.py"),"test","--pattern","test_toolkit_core.py","--pcb-python",sys.executable],capture_output=True,text=True)
        self.assertEqual(r.returncode,1,r.stdout+r.stderr)
    def test_profiles_distinct(self):
        a,b=resolve_project("ads8588s"),resolve_project("ad7606c")
        self.assertNotEqual(a.schematic,b.schematic)
        self.assertNotEqual(a.rule_sets,b.rule_sets)
if __name__=="__main__":unittest.main()
