"""Regressions for digital copper against the complete OEM ADC body."""
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from pcbtools.rules import adc_layout
except ImportError:
    adc_layout = None
try:
    import pcbnew as p
except ImportError:
    p = None


def profile():
    return {
        "reference": "U6",
        "mpn": "AD7606C-16BSTZ",
        "package": "ADI_ST-64-2",
        "body_size_mm": [10.2, 10.2],
        "digital_nets": ["/ADC5_CS_N", "Net-(U6B-SCLK)"],
        "forbidden_routing_layers": ["In1.Cu"],
        "minimum_track_width_mm": 0.2,
    }


class ADCBodyConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(adc_layout, "ADC complete-body guard is missing")

    def test_reviewed_oem_maximum_body(self):
        self.assertEqual(adc_layout.validate_config(profile()), [])

    def test_missing_configuration_fails_closed(self):
        self.assertTrue(adc_layout.validate_config(None))

    def test_body_shrink_cannot_restore_the_old_inset(self):
        for size in ([9, 9], [10, 10], [10.2, 9]):
            config = profile()
            config["body_size_mm"] = size
            self.assertTrue(adc_layout.validate_config(config), size)

    def test_missing_or_wildcard_net_selection_fails(self):
        for nets in (None, [], ["/ADC5_*"], ["/ADC5_CS_N", "/ADC5_CS_N"]):
            config = profile()
            config["digital_nets"] = nets
            self.assertTrue(adc_layout.validate_config(config), nets)

    def test_width_or_ground_plane_policy_cannot_be_reduced(self):
        config = profile()
        config["minimum_track_width_mm"] = 0.19
        self.assertTrue(adc_layout.validate_config(config))
        config = profile()
        config["forbidden_routing_layers"] = []
        self.assertTrue(adc_layout.validate_config(config))

    def test_package_and_exact_mpn_must_agree(self):
        config = profile()
        config["package"] = "TI_PM0064A"
        self.assertTrue(adc_layout.validate_config(config))

    def test_both_projects_explicitly_select_the_complete_policy(self):
        from pcbtools.project import resolve_project
        for name in ["ads8588s", "ad7606c"]:
            with self.subTest(project=name):
                config = resolve_project(name).parameters.get("adc_body_digital_exclusion")
                self.assertEqual(adc_layout.validate_config(config), [])


@unittest.skipIf(p is None, "pcbnew required for native ADC copper geometry")
class NativeADCBodyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(adc_layout, "ADC complete-body guard is missing")
        self.board = p.BOARD()
        self.board.SetCopperLayerCount(4)
        self.config = profile()
        for name in self.config["digital_nets"] + ["/VA_5V"]:
            self.board.Add(p.NETINFO_ITEM(self.board, name))
        self.adc = p.FOOTPRINT(self.board)
        self.adc.SetReference("U6")
        self.adc.SetValue("AD7606C-16BSTZ")
        self.adc.SetFPID(p.LIB_ID("Package_QFP", "LQFP-64_10x10mm_P0.5mm"))
        self.adc.SetPosition(self.point(46, 74))
        self.board.Add(self.adc)

    @staticmethod
    def point(x, y):
        return p.VECTOR2I(p.FromMM(x), p.FromMM(y))

    def track(self, start, end, width=0.25, layer=None, net="/ADC5_CS_N"):
        item = p.PCB_TRACK(self.board)
        item.SetStart(self.point(*start))
        item.SetEnd(self.point(*end))
        item.SetWidth(p.FromMM(width))
        item.SetLayer(p.F_Cu if layer is None else layer)
        self.board.Add(item)
        item.SetNet(self.board.FindNet(net))
        return item

    def via(self, x, y, diameter=0.5):
        item = p.PCB_VIA(self.board)
        item.SetPosition(self.point(x, y))
        item.SetWidth(p.FromMM(diameter))
        item.SetDrill(p.FromMM(0.3))
        item.SetLayerPair(p.F_Cu, p.B_Cu)
        item.SetViaType(p.VIATYPE_THROUGH)
        self.board.Add(item)
        item.SetNet(self.board.FindNet("/ADC5_CS_N"))
        return item

    def audit(self):
        return adc_layout.audit(self.board, self.config)

    def test_original_four_cs_segments_are_all_rejected(self):
        # Exact reviewed 729dea CS_N centreline geometry; old inset missed it.
        segments = [
            ((40.325, 76.25), (41.1812, 76.25)),
            ((41.4561, 78.0129), (39.219, 80.25)),
            ((41.4561, 76.5249), (41.4561, 78.0129)),
            ((41.1812, 76.25), (41.4561, 76.5249)),
        ]
        for start, end in segments:
            self.track(start, end)
        report, errors = self.audit()
        self.assertEqual(len(errors), 4, errors)
        self.assertEqual(len(report["violations"]), 4)
        self.assertTrue(all("body_intrusion" in r["reasons"] for r in report["violations"]))

    def test_centreline_outside_but_track_copper_inside_is_rejected(self):
        self.track((40.85, 73), (40.85, 75), width=0.2)
        self.assertTrue(self.audit()[1])

    def test_rounded_track_end_cap_is_checked(self):
        self.track((39, 74), (40.81, 74), width=0.2)
        self.assertTrue(self.audit()[1])

    def test_via_disk_outside_centre_can_overlap_body(self):
        self.via(40.7, 74, diameter=0.5)
        report, errors = self.audit()
        self.assertEqual(len(errors), 1, errors)
        self.assertEqual(report["violations"][0]["kind"], "via")

    def test_outer_and_both_internal_copper_layers_are_checked(self):
        for layer in [p.F_Cu, p.In1_Cu, p.In2_Cu, p.B_Cu]:
            self.track((44, 74), (48, 74), layer=layer)
        report, errors = self.audit()
        self.assertEqual(len(report["violations"]), 4, errors)

    def test_in1_signal_outside_body_is_still_rejected(self):
        self.track((20, 20), (21, 20), layer=p.In1_Cu)
        self.assertIn("forbidden_layer", self.audit()[0]["violations"][0]["reasons"])

    def test_sub_02_digital_track_outside_body_is_rejected(self):
        self.track((20, 20), (21, 20), width=0.19)
        self.assertIn("undersized_width", self.audit()[0]["violations"][0]["reasons"])

    def test_analog_rail_is_not_misclassified_as_digital(self):
        self.track((44, 74), (48, 74), net="/VA_5V")
        self.assertEqual(self.audit()[1], [])

    def test_omitting_an_actual_adc_digital_net_fails_closed(self):
        self.board.Add(p.NETINFO_ITEM(self.board, "/ADC5_DOUTA"))
        report, errors = self.audit()
        self.assertTrue(errors)
        self.assertIn("/ADC5_DOUTA", "; ".join(errors))

    def test_internal_sclk_is_explicitly_selected(self):
        self.track((44, 74), (48, 74), net="Net-(U6B-SCLK)")
        self.assertTrue(self.audit()[1])
        self.config["digital_nets"].remove("Net-(U6B-SCLK)")
        self.assertIn("Net-(U6B-SCLK)", "; ".join(self.audit()[1]))

    def test_small_fab_graphic_cannot_shrink_oem_body(self):
        graphic = p.PCB_SHAPE(self.adc)
        graphic.SetShape(p.SHAPE_T_RECT)
        graphic.SetStart(self.point(45, 73))
        graphic.SetEnd(self.point(47, 75))
        graphic.SetLayer(p.F_Fab)
        self.adc.Add(graphic)
        self.track((41, 73), (41, 75))
        self.assertTrue(self.audit()[1])

    def test_rotation_translation_and_rotated_bounding_box_false_positive(self):
        for angle, centre in [(0, (46, 74)), (45, (103, 52)), (90, (30, 30)), (137, (91, 63))]:
            with self.subTest(angle=angle, centre=centre):
                for item in list(self.board.GetTracks()):
                    self.board.RemoveNative(item)
                self.adc.SetPosition(self.point(*centre))
                self.adc.SetOrientationDegrees(angle)
                def world(x, y):
                    rad = math.radians(angle)
                    return (centre[0] + x * math.cos(rad) + y * math.sin(rad),
                            centre[1] - x * math.sin(rad) + y * math.cos(rad))
                self.track(world(5.4, -0.4), world(5.4, 0.4), width=0.2)
                self.assertEqual(self.audit()[1], [])
                self.track(world(4.9, -0.4), world(4.9, 0.4), width=0.2)
                self.assertEqual(len(self.audit()[1]), 1)

    def test_selected_package_value_mismatch_is_rejected(self):
        self.adc.SetValue("A_DIFFERENT_ADC")
        self.assertTrue(self.audit()[1])

    def test_native_rule_dispatch_runs_guard_and_propagates_missing_policy(self):
        from pcbtools.rules import run_rules
        self.track((44, 74), (48, 74))
        vendor = SimpleNamespace(check=lambda text: [], check_internal_pad_rules=lambda text: [])
        native = SimpleNamespace(audit=lambda board: ([], []))
        corners = SimpleNamespace(audit=lambda board: [])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.kicad_pcb"
            path.write_text("", encoding="utf-8")
            path.with_suffix(".kicad_dru").write_text("(version 1)", encoding="utf-8")
            for parameters in ({"adc_body_digital_exclusion": self.config}, {}):
                project = SimpleNamespace(rule_sets=["power_layout"], board=path, parameters=parameters)
                with (patch("pcbnew.LoadBoard", return_value=self.board),
                      patch("pcbtools.rules.power_layout.vendor_api", return_value=vendor),
                      patch("pcbtools.rules.power_layout.kelvin_api", return_value=native),
                      patch("pcbtools.rules.power_layout.escape_api", return_value=native),
                      patch("pcbtools.board.corners_api", return_value=corners)):
                    findings = run_rules(project, "pcb", {})
                result = next((f for f in findings if f.rule_id == "pcb.adc_body_digital_exclusion"), None)
                self.assertIsNotNone(result, "Native rule dispatch omitted ADC body guard")
                self.assertEqual(result.status, "FAIL")


if __name__ == "__main__":
    unittest.main()
