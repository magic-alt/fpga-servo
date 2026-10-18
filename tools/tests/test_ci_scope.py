import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Regression evidence must never turn a blocked PCB into release approval."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from pcbtools.rules.servo import baseline_api
_family = baseline_api(resolve_project("ads8588s"))
compare_snapshot = _family.compare_snapshot
collect_snapshot = _family.collect_snapshot
BASELINE = _family.BASELINE

ROOT = Path(__file__).resolve().parents[2]


class CIScopeTests(unittest.TestCase):
    def setUp(self):
        self.expected = json.loads(BASELINE.read_text(encoding="utf-8"))["snapshot"]

    def test_preserved_board_matches_recorded_blockers(self):
        self.assertEqual(compare_snapshot(collect_snapshot(), self.expected), [])

    def test_historical_regression_reads_immutable_archive_only(self):
        archive = ROOT / "hardware/ads8588s_servo/evidence/legacy_pcb_before_dual_prototype_2026-10-18"
        self.assertEqual(BASELINE.parent, archive)
        current_board = ROOT / "hardware/ads8588s_servo/ax7010_servo_reva.kicad_pcb"
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            if path == current_board:
                raise AssertionError("Historical regression read mutable active board")
            return original_read(path, *args, **kwargs)
        with patch.object(Path, "read_text", read):
            self.assertEqual(compare_snapshot(collect_snapshot(), self.expected), [])

    def test_active_profile_cannot_accept_known_archived_blockers(self):
        from pcbtools.rules import run_rules
        project = resolve_project("ads8588s")
        self.assertNotIn("archived_pcb", project.rule_sets)
        self.assertTrue({"servo", "protection", "power_layout"}.issubset(project.rule_sets))
        board = project.board
        archived_text = (BASELINE.parent / board.name).read_text(encoding="utf-8")
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            return archived_text if path == board else original_read(path, *args, **kwargs)
        with patch.object(Path, "read_text", read):
            findings = run_rules(project, "pcb", {})
        self.assertFalse(any(f.rule_id == "pcb.archived_regression" for f in findings))
        self.assertTrue(any(f.rule_id == "servo.design" and f.status == "FAIL" for f in findings))

    def test_changed_board_cannot_reuse_known_failures(self):
        changed = copy.deepcopy(self.expected)
        changed["source_sha256"]["board"] = "0" * 64
        self.assertTrue(compare_snapshot(changed, self.expected))

    def test_additional_failure_is_not_waived(self):
        changed = copy.deepcopy(self.expected)
        changed["design_errors"].append("new electrical failure")
        self.assertTrue(compare_snapshot(changed, self.expected))

    def test_parity_details_are_compared_not_only_counts(self):
        changed = copy.deepcopy(self.expected)
        changed["parity"]["net_mismatches"][0]["pin"] = "999"
        self.assertTrue(compare_snapshot(changed, self.expected))

    def test_requested_native_parity_cannot_be_omitted(self):
        changed = copy.deepcopy(self.expected)
        del changed["parity"]
        del changed["constraints"]
        self.assertTrue(compare_snapshot(changed, self.expected, require_parity=True))

    def test_empty_fresh_netlist_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.net"
            path.write_text("(export)", encoding="utf-8")
            with self.assertRaises(ValueError):
                collect_snapshot(path)

    def test_strict_design_default_still_blocks_archived_board(self):
        from pcbtools.rules.servo import check_design
        errors = check_design(resolve_project("ads8588s"), schematic_only=False, board_root=BASELINE.parent)
        self.assertTrue(any("Unused J2 must not be fitted on PCB" in e for e in errors))

    def test_original_source_contract_accepts_lf_but_rejects_content_changes(self):
        import tempfile
        from pcbtools.rules.adc import ad7606c_api
        module = ad7606c_api(resolve_project("ad7606c"))
        manifest = json.loads((module.HERE / "source_manifest.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in manifest["files"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_text(encoding="utf-8").encode("utf-8"))
            self.assertEqual(module.source_errors(root), [])
            path.write_bytes(path.read_bytes() + b"unexpected content")
            self.assertTrue(module.source_errors(root))

    def test_schematic_scope_still_validates_shunt_symbol_pins(self):
        from pcbtools.rules.power_layout import kelvin_api
        _family = kelvin_api()
        check_shunt_contract = _family.check_shunt_contract
        hw = ROOT / "hardware/ads8588s_servo"
        symbol = (hw / "ax7010_servo_reva.kicad_sym").read_text(encoding="utf-8")
        embedded = (hw / "gate_inverter.kicad_sch").read_text(encoding="utf-8")
        land = (hw / "fpga-servo.pretty/HoYLR2512_Kelvin.kicad_mod").read_text(encoding="utf-8")
        self.assertEqual(check_shunt_contract("", symbol, embedded, land, include_board=False), [])
        broken = land.replace('(pad "2"', '(pad "99"', 1)
        self.assertTrue(check_shunt_contract("", symbol, embedded, broken, include_board=False))

    def test_explicit_schematic_scope_passes(self):
        from pcbtools.rules.servo import check_design
        self.assertEqual(check_design(resolve_project("ads8588s"), schematic_only=True), [])


if __name__ == "__main__":
    unittest.main()
