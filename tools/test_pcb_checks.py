"""Behavioral regressions for physical-pin PCB parity (stdlib only)."""
import importlib.util
import unittest
from pathlib import Path


class PCBParityTests(unittest.TestCase):
    def test_checker_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("check_pcb_parity"), "physical-pin parity checker is missing")

    def test_wrong_pad_net_and_missing_part_are_rejected(self):
        if importlib.util.find_spec("check_pcb_parity") is None:
            self.skipTest("checker missing; covered by test_checker_exists")
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "Resistor_SMD:R_0603")) (comp (ref "C1") (value "100n") (footprint "Capacitor_SMD:C_0603"))) (nets (net (code "1") (name "GND") (node (ref "R1") (pin "1")) (node (ref "C1") (pin "1")))))'
        pcb = '(kicad_pcb (net 1 "WRONG") (footprint "Resistor_SMD:R_0603" (property "Reference" "R1") (pad "1" smd rect (net 1 "WRONG"))))'
        report = audit_text(net, pcb)
        self.assertEqual(report["missing_on_pcb"], ["C1"])
        self.assertEqual(report["net_mismatches"][0]["schematic_net"], "GND")
        self.assertFalse(report["passed"])

    def test_full_footprint_id_and_each_duplicate_pad_are_checked(self):
        if importlib.util.find_spec("check_pcb_parity") is None:
            self.skipTest("checker missing")
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "Q1") (value "FET") (footprint "Correct:Pkg"))) (nets (net (name "D") (node (ref "Q1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "Wrong:Pkg" (property "Reference" "Q1") (pad "1" smd rect (net 1 "D")) (pad "1" smd rect (net 2 "OTHER"))))'
        report = audit_text(net, pcb)
        self.assertEqual(report["footprint_mismatches"][0]["ref"], "Q1")
        self.assertEqual(len(report["net_mismatches"]), 1)

    def test_only_registered_mechanical_parts_are_allowed(self):
        if importlib.util.find_spec("check_pcb_parity") is None:
            self.skipTest("checker missing")
        from check_pcb_parity import audit_text
        pcb = '(kicad_pcb (footprint "MountingHole:Hole" (property "Reference" "H1") (property "Value" "M3_HOLE") (pad "" np_thru_hole circle)))'
        self.assertTrue(audit_text('(export)', pcb, mechanical_refs={"H1"})["passed"])
        self.assertFalse(audit_text('(export)', pcb)["passed"])

    def test_renamed_ground_and_missing_pad_are_not_normalized(self):
        if importlib.util.find_spec("check_pcb_parity") is None:
            self.skipTest("checker missing")
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "U1") (value "IC") (footprint "L:P"))) (nets (net (name "GND") (node (ref "U1") (pin "1"))) (net (name "/A") (node (ref "U1") (pin "2")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "U1") (pad "1" smd rect (net 1 "PGND"))))'
        r = audit_text(net, pcb)
        self.assertEqual(r["pin_mismatches"][0]["missing_pads"], ["2"])
        self.assertEqual(r["net_mismatches"][0]["pcb_nets"], ["PGND"])

    def test_kicad10_name_only_net_encoding_is_supported(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "L:P"))) (nets (net (name "/GND") (node (ref "R1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "R1") (property "Value" "10k") (pad "1" smd rect (net "/GND"))))'
        self.assertTrue(audit_text(net, pcb)["passed"])

    def test_extra_unconnected_numbered_pad_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "L:P"))) (nets (net (name "GND") (node (ref "R1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "R1") (property "Value" "10k") (pad "1" smd rect (net "GND")) (pad "99" smd rect)))'
        self.assertFalse(audit_text(net, pcb)["passed"])

    def test_dnp_mismatch_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "D1") (value "TVS") (footprint "L:P") (property (name "dnp")))) (nets (net (name "GND") (node (ref "D1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "D1") (property "Value" "TVS") (pad "1" smd rect (net "GND"))))'
        self.assertFalse(audit_text(net, pcb)["passed"])
        self.assertTrue(audit_text(net, pcb.replace('(pad "1"', '(attr smd dnp) (pad "1"'))["passed"])

    def test_missing_value_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "L:P"))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "R1")))'
        self.assertFalse(audit_text(net, pcb)["passed"])

    def test_actual_power_and_bootstrap_nets_require_classes(self):
        from check_pcb_constraints import check
        names = ["VIN_RAW", "VIN_FUSED", "RPP_SRC", "BST_U", "BST_V", "BST_W"]
        net = '(export (nets ' + ' '.join('(net (name "' + n + '"))' for n in names) + '))'
        project = {"net_settings": {"classes": [{"name": x} for x in ["POWER", "GATE", "ANALOG"]], "netclass_patterns": []}}
        errors = check('(kicad_pcb)', project, net)
        for name in names:
            self.assertTrue(any(e.startswith(name + ':') for e in errors), name)

    def test_mechanical_reference_cannot_hide_an_electrical_pad(self):
        if importlib.util.find_spec("check_pcb_parity") is None:
            self.skipTest("checker missing")
        from check_pcb_parity import audit_text
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "H1") (property "Value" "M3_HOLE") (pad "1" thru_hole circle (net 1 "VBUS"))))'
        self.assertFalse(audit_text('(export)', pcb, mechanical_refs={"H1"})["passed"])


    def test_extra_unconnected_numbered_pad_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "L:P"))) (nets (net (name "GND") (node (ref "R1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "R1") (property "Value" "10k") (pad "1" smd rect (net "GND")) (pad "99" smd rect)))'
        self.assertFalse(audit_text(net, pcb)["passed"])

    def test_dnp_mismatch_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "D1") (value "TVS") (footprint "L:P") (property (name "dnp")))) (nets (net (name "GND") (node (ref "D1") (pin "1")))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "D1") (property "Value" "TVS") (pad "1" smd rect (net "GND"))))'
        self.assertFalse(audit_text(net, pcb)["passed"])
        self.assertTrue(audit_text(net, pcb.replace('(pad "1"', '(attr smd dnp) (pad "1"'))["passed"])

    def test_missing_value_is_rejected(self):
        from check_pcb_parity import audit_text
        net = '(export (components (comp (ref "R1") (value "10k") (footprint "L:P"))))'
        pcb = '(kicad_pcb (footprint "L:P" (property "Reference" "R1")))'
        self.assertFalse(audit_text(net, pcb)["passed"])

    def test_actual_power_and_bootstrap_nets_require_classes(self):
        from check_pcb_constraints import check
        names = ["VIN_RAW", "VIN_FUSED", "RPP_SRC", "BST_U", "BST_V", "BST_W"]
        net = '(export (nets ' + ' '.join('(net (name "' + n + '"))' for n in names) + '))'
        project = {"net_settings": {"classes": [{"name": x} for x in ["POWER", "GATE", "ANALOG"]], "netclass_patterns": []}}
        errors = check('(kicad_pcb)', project, net)
        for name in names:
            self.assertTrue(any(e.startswith(name + ':') for e in errors), name)


if __name__ == "__main__":
    unittest.main()
