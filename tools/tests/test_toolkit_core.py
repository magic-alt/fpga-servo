"""Public configuration and failure semantics for reusable PCB projects."""
import json
import re
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import load_project, resolve_project, ProjectError
from pcbtools.report import Finding, RunReport, exit_code

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pcb project ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / "board").mkdir()
        (self.base / "board/top.kicad_sch").write_text('(kicad_sch (version 20250114) (paper "A4") (lib_symbols))')
        self.data = {"schema_version": 1, "id": "third", "root": "board", "schematic": "top.kicad_sch", "output": "evidence", "rule_sets": [], "parameters": {}}
    def load(self):
        p = self.base / "project.json"
        p.write_text(json.dumps(self.data))
        return load_project(p)
    def test_config_relative_to_file(self):
        p = self.load()
        self.assertEqual(p.schematic, self.base / "board/top.kicad_sch")
    def test_unknown_key_rejected(self):
        self.data["typo"] = True
        with self.assertRaises(ProjectError): self.load()
    def test_space_and_external_root(self):
        self.data["root"] = str(self.base / "board")
        self.assertEqual(self.load().root, self.base / "board")
    def test_missing_board_requested(self):
        with self.assertRaises(ProjectError): self.load().require_board()
    def test_required_not_run_is_failure(self):
        r = RunReport("third", [Finding("erc", "NOT_RUN", "missing tool", {})], {}, "BLOCKED")
        self.assertEqual(exit_code(r), 1)
    def test_blocked_and_failed_precedence(self):
        r = RunReport("third", [Finding("erc", "PASS", "", {})], {}, "BLOCKED")
        self.assertEqual(exit_code(r), 2)
        r.findings.append(Finding("drc", "FAIL", "", {}))
        self.assertEqual(exit_code(r), 1)
    def test_output_cannot_overlap_source(self):
        self.data["output"] = "."
        with self.assertRaises(ProjectError): self.load()
    def test_missing_schematic_rejected(self):
        self.data["schematic"] = "absent.kicad_sch"
        with self.assertRaises(ProjectError): self.load()
    def test_config_profiles(self):
        self.assertIsNotNone(resolve_project("ads8588s").board)
        target = resolve_project("ad7606c")
        self.assertTrue(target.require_board().is_file())
        self.assertNotEqual(target.board, resolve_project("ads8588s").board)
        self.assertEqual(set(target.parameters["mechanical_refs"]), {"H1", "H2", "H3", "H4"})
    def test_ad7606c_project_metadata_matches_native_root(self):
        target = resolve_project("ad7606c")
        data = json.loads(target.schematic.with_suffix(".kicad_pro").read_text(encoding="utf-8"))
        root_uuid = re.search(r'\(uuid "([^"]+)"', target.schematic.read_text(encoding="utf-8"))[1]
        self.assertEqual(data["schematic"]["top_level_sheets"], [{
            "filename": target.schematic.name, "name": target.schematic.stem, "uuid": root_uuid,
        }])
    def test_unknown_rules_fail(self):
        self.data["rule_sets"] = ["execute-shell"]
        with self.assertRaises(ProjectError): self.load()

if __name__ == "__main__": unittest.main()
