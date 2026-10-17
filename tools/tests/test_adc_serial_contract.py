import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from pcbtools.project import resolve_project
"""Static ADS8588S/J10 source-contract regressions, including negative mutations."""
import tempfile
import unittest
from pathlib import Path
import shutil
from pcbtools.rules.adc import serial_api
contract = serial_api(resolve_project("ads8588s"))


class ADCSerialContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for source in (
            "hardware/ads8588s_servo/current_adc.kicad_sch",
            "hardware/ads8588s_servo/ax7010_interface.kicad_sch",
            "hardware/ads8588s_servo/bom.csv",
            "fpga/ax7010_servo_reva.xdc",
        ):
            dst = self.root / source
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(contract.ROOT / source, dst)

    def mutate(self, rel: str, old: str, new: str):
        p = self.root / rel
        s = p.read_text(encoding="utf-8")
        self.assertIn(old, s)
        p.write_text(s.replace(old, new), encoding="utf-8")

    def test_source_contract(self):
        self.assertEqual(contract.check(self.root), [])

    def test_frame_size_and_throughput(self):
        t = contract.timing()
        self.assertEqual(t["dual_sclk_cycles"], 64)
        self.assertEqual(t["single_sclk_cycles"], 128)
        self.assertEqual(t["dual_20mhz_us"], 3.2)
        self.assertEqual(t["dual_10mhz_us"], 6.4)
        self.assertEqual(t["pwm_cycle_us"], 50.0)
        # 10MHz/dual: cannot clock a full frame every 5us (200kSPS).
        self.assertGreater(t["dual_10mhz_us"], contract.SAMPLE_CYCLE_MIN_US)

    def test_unfitted_parallel_port_rejected(self):
        self.mutate("fpga/ax7010_servo_reva.xdc",
                    "# set_property PACKAGE_PIN F17",
                    "set_property PACKAGE_PIN F17")
        errs = contract.check(self.root)
        self.assertTrue(any("unfitted J11" in e for e in errs), errs)

    def test_lost_second_dout_pin_rejected(self):
        self.mutate("fpga/ax7010_servo_reva.xdc",
                    "PACKAGE_PIN U14 [get_ports ADC_DOUTB]",
                    "PACKAGE_PIN U14 [get_ports TEST_ONLY]")
        errs = contract.check(self.root)
        self.assertTrue(any("ADC_DOUTB" in e for e in errs), errs)

    def test_motor_ntc_mislabel_rejected(self):
        self.mutate("hardware/ads8588s_servo/current_adc.kicad_sch",
                    'label "NTC_BOARD_AUX"',
                    'label "NTC_MOTOR"')
        errs = contract.check(self.root)
        self.assertTrue(any("NTC2" in e for e in errs), errs)

    def test_stale_250v_film_metadata_rejected(self):
        self.mutate("hardware/ads8588s_servo/bom.csv", ",1uF_250V_FILM,Fitted",
                    ",1uF_100V_FILM,Fitted")
        errs = contract.check(self.root)
        self.assertTrue(any("C3" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
