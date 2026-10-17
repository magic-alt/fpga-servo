import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Regression and deliberate-error tests for proposed AD7606C profile."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pcbtools.rules.adc import fast_api
contract = fast_api(resolve_project("ads8588s"))


class AD7606CFastCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in (
            contract.PROFILE,
            contract.CANDIDATES,
            contract.SOURCE_BOM,
            contract.SCHEMATIC,
            contract.XDC,
        ):
            src = contract.ROOT / rel
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def edit(self, callback):
        target = self.root / contract.PROFILE
        p = json.loads(target.read_text(encoding="utf-8"))
        callback(p)
        target.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")

    def test_candidate_is_valid_but_not_implemented(self):
        self.assertEqual(contract.check(self.root), [])

    def test_no_undocumented_mode_strap(self):
        self.edit(lambda d: d["mode_straps"].update({"OS0": 0}))
        self.assertTrue(any("software mode" in e for e in contract.check(self.root)))

    def test_lane_configuration_must_match_four_douts(self):
        self.edit(lambda d: d["configuration"]["0x02"].update({"value": "0x08"}))
        self.assertTrue(any("0x02" in e or "4 physical" in e for e in contract.check(self.root)))

    def test_parallel_pin_collision_rejected(self):
        self.edit(lambda d: d["external_pins"][-1].update({"fpga_pin": "U12"}))
        self.assertTrue(any("duplicate Xilinx" in e or "ADC_SDI" in e for e in contract.check(self.root)))

    def test_source_status_cannot_be_marked_production_released(self):
        self.edit(lambda d: d.update({"status": "PRODUCTION_FREEZE_APPROVED"}))
        self.assertTrue(any("wrongly claims" in e for e in contract.check(self.root)))

    def test_bandwidth_of_unipolar_range_is_not_220khz(self):
        self.edit(lambda d: d["timing"].update({"analog_3db_bandwidth_khz": 220}))
        self.assertTrue(any("150kHz" in e for e in contract.check(self.root)))

    def test_new_adc_not_falsely_wired_into_old_xdc(self):
        xdc = self.root / contract.XDC
        xdc.write_text(xdc.read_text(encoding="utf-8")
                       + "\nset_property PACKAGE_PIN U12 [get_ports ADC_DOUTC]\n",
                       encoding="utf-8")
        self.assertTrue(any("erroneously enabled" in e for e in contract.check(self.root)))


if __name__ == "__main__":
    unittest.main()
