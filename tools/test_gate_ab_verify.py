#!/usr/bin/env python3
"""Regression tests for Gate A/B physical-pin and passive calculation contracts."""
from __future__ import annotations

import math
import os
from pathlib import Path
import shutil
import tempfile
import unittest

import gate_ab_verify as qa


class PassiveTests(unittest.TestCase):
    def test_exact_unit_parser(self):
        for source, expected in (("5mR", .005), ("47R", 47),
                                 ("160k", 160000), ("1nF", 1e-9),
                                 ("100uF", 100e-6)):
            self.assertAlmostEqual(qa.passive(source), expected)

    def test_bad_value_is_rejected(self):
        for source in ("", "foo", "22 k", "100Rsomething", "1/0"):
            with self.assertRaises(qa.TopologyError):
                qa.passive(source)

    def test_corner_sweep_is_symmetric_for_real_dividers(self):
        values = {"R50": 10e3, "R51": 160e3, "R52": 160e3,
                  "R53": 10e3, "RSH1": .005}
        out = qa.corner_current_limits(values)
        self.assertAlmostEqual(out["positive_trip_nominal_A"], 22.0588235294, places=7)
        self.assertAlmostEqual(out["reference_high_nominal_V"], 4.7058823529, places=7)
        self.assertAlmostEqual(out["reference_low_nominal_V"], .2941176471, places=7)
        self.assertAlmostEqual(out["positive_passive_corner_A"][0],
                               out["negative_abs_passive_corner_A"][0], places=10)
        self.assertAlmostEqual(out["positive_passive_corner_A"][1],
                               out["negative_abs_passive_corner_A"][1], places=10)

    def test_supervisor_falling_threshold_cannot_guarantee_adc_min(self):
        maximum_trip = qa.G50_THRESHOLD_V * (1+qa.G50_THRESHOLD_TOL)
        self.assertLess(maximum_trip, qa.ADC_AVDD_MIN_V)
        self.assertAlmostEqual(qa.ADC_AVDD_MIN_V-maximum_trip, .007, places=7)

    def test_charge_time_is_only_an_illustrative_ratio(self):
        self.assertAlmostEqual(qa.MOSFET_QG_MAX_C/qa.FD6288_SOURCE_PEAK_A, 48e-9)
        self.assertAlmostEqual(qa.MOSFET_QG_MAX_C/qa.FD6288_SINK_PEAK_A, 40e-9)


@unittest.skipUnless(os.environ.get("GATE_AB_NETLIST"), "Set GATE_AB_NETLIST to fresh KiCad XML")
class RealNetlistMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.netlist = Path(os.environ["GATE_AB_NETLIST"])

    def setUp(self):
        self.components, self.pins = qa.read_netlist(self.netlist)
        self.assertGreater(len(self.components), 150)
        self.assertGreater(len(self.pins), 300)

    def test_real_graph_and_evidence(self):
        values = qa.require_graph(self.components, self.pins)
        self.assertAlmostEqual(values["RSH1"], .005)
        out = qa.gate_report(self.netlist)
        self.assertEqual(out["gate_a"]["status"], "BLOCKED")
        self.assertEqual(out["gate_b"]["status"], "BLOCKED")
        self.assertGreater(out["numerics"]["adc_supply_vs_supervisor"]["blind_window_at_least_V"], 0)
        self.assertEqual(len(out["source_netlist_sha256"]), 64)

    def test_adc_strap_mutation_detected(self):
        self.pins[("U6", "33")] = "/FLOATING"
        with self.assertRaisesRegex(qa.TopologyError, "U6.33"):
            qa.require_graph(self.components, self.pins)

    def test_bootstrap_diode_reversal_detected(self):
        self.pins[("D2", "1")] = "/VDRV_12V"
        with self.assertRaises(qa.TopologyError):
            qa.require_graph(self.components, self.pins)

    def test_comparator_reference_fault_detected(self):
        self.pins[("U15", "5")] = "/WRONG"
        with self.assertRaises(qa.TopologyError):
            qa.require_graph(self.components, self.pins)

    def test_supervisor_input_fault_detected(self):
        self.pins[("U25", "5")] = "/VIO_3V3"
        with self.assertRaisesRegex(qa.TopologyError, "U25.5"):
            qa.require_graph(self.components, self.pins)

    def test_shunt_value_mutation_detected(self):
        self.components["RSH1"] = "50mR"
        with self.assertRaises(qa.TopologyError):
            qa.require_graph(self.components, self.pins)

    def test_regeneration_model_matches_capacitor_law(self):
        self.assertAlmostEqual(qa.gate_report(self.netlist)["numerics"]["regeneration"]
                               ["ideal_no_sink_1A_time_48_to_55_s"], .0014)
        self.assertAlmostEqual(qa.gate_report(self.netlist)["numerics"]
                               ["shunt_loss_each_W_at_10A_RMS"][0], .5)

    @unittest.skipUnless(shutil.which("ngspice"), "ngspice CLI not available")
    def test_ngspice_regen_and_ideal_rc_crossing(self):
        vals = {ref: qa.passive(self.components[ref]) for ref in (
            "C1", "C2", "R50", "R51", "R40", "C40")}
        with tempfile.TemporaryDirectory() as folder:
            result = qa.run_spice(vals, Path(folder), "ngspice")
            self.assertEqual(result["status"], "PASS_ONLY_IDEAL_PASSIVE")
            self.assertAlmostEqual(result["regeneration_final_V"], 55, delta=.05)


if __name__ == "__main__":
    unittest.main()
