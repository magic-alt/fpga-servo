#!/usr/bin/env python3
"""Gate A/B netlist-backed electrical audit and deliberately bounded ngspice checks.

This is NOT vendor-device simulation, a certified shutdown-time bound, or a
fabrication approval. A passing execution means only the automated evidence ran.
Use a freshly exported KiCad XML netlist (never the tracked historical XML).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


ADC_AVDD_MIN_V = 4.75                 # TI ADS8588S operating minimum
G50_THRESHOLD_V = 4.65               # TPS3808G50 nominal falling threshold
G50_THRESHOLD_TOL = 0.02             # Datasheet threshold accuracy, conservative
G33_THRESHOLD_V = 3.07               # TPS3808G33 nominal falling threshold
G33_THRESHOLD_TOL = 0.015
SUPERVISOR_HYSTERESIS_MAX = 0.025    # Conservative margin from project review
INA_GAIN_V_PER_V = 20.0              # INA241A2 nominal gain
MOSFET_VDS_MAX_V = 100.0             # BSC040N10NS5 absolute maximum
MOSFET_QG_MAX_C = 72e-9              # At published test conditions, not worst application
FD6288_SOURCE_PEAK_A = 1.5           # Nominal/advertised peak, NOT guaranteed lower bound
FD6288_SINK_PEAK_A = 1.8
PWM_HZ = 20_000
PHASE_RMS_A = 10.0


class TopologyError(ValueError):
    """A critical physical-pin / component-value requirement did not hold."""


def passive(value: str) -> float:
    """Accept project values (5mR, 47R, 160k, 1nF, 100uF)."""
    text = value.strip().replace("Ohm", "R").replace("Ω", "R")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([GMkmunp]?)([RF]?)", text)
    if not match:
        raise TopologyError(f"Unsupported passive value: {value!r}")
    prefix = match.group(2)
    factor = {"": 1.0, "G": 1e9, "M": 1e6, "k": 1e3,
              "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12}[prefix]
    return float(match.group(1)) * factor


def read_netlist(path: Path) -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    root = ET.parse(path).getroot()
    if root.tag != "export":
        raise TopologyError("Expected KiCad XML <export> netlist")
    components = {c.attrib["ref"]: c.findtext("value", "")
                  for c in root.findall("./components/comp")}
    pins: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        for node in net.findall("node"):
            key = (node.attrib["ref"], node.attrib["pin"])
            if key in pins:
                raise TopologyError(f"Duplicate physical pin in XML: {key}")
            pins[key] = net.attrib["name"]
    if len(components) < 150 or len(pins) < 300:
        raise TopologyError("Unexpectedly incomplete KiCad export: fail closed")
    return components, pins


def require_graph(components: dict[str, str],
                  pins: dict[tuple[str, str], str]) -> dict[str, float]:
    """A narrow independent physics-facing contract, not a replacement for ERC."""
    def value(ref: str, expected: str | float) -> float:
        if ref not in components:
            raise TopologyError(f"Required component missing: {ref}")
        raw = components[ref]
        if isinstance(expected, str):
            if raw != expected:
                raise TopologyError(f"{ref}: expected {expected}, got {raw}")
            return math.nan
        parsed = passive(raw)
        if not math.isclose(parsed, expected, rel_tol=1e-8, abs_tol=1e-15):
            raise TopologyError(f"{ref}: expected {expected}, got {raw}")
        return parsed

    def net(ref: str, pin: str | int) -> str:
        key = (ref, str(pin))
        if key not in pins:
            raise TopologyError(f"Pin {ref}.{pin} absent from exported XML")
        name = pins[key]
        if name.startswith("unconnected-"):
            raise TopologyError(f"Required pin disconnected: {ref}.{pin}")
        return name

    def rail(ref: str, pin: str | int, name: str) -> None:
        found = net(ref, pin)
        if found != "/" + name:
            raise TopologyError(f"{ref}.{pin} expected /{name}, got {found}")

    def same(*terminals: tuple[str, int | str]) -> None:
        names = [net(ref, pin) for ref, pin in terminals]
        if len(set(names)) != 1:
            raise TopologyError(f"Disconnected physical topology {terminals}: {names}")

    for ref in ("U2", "U3", "U4"):
        value(ref, "INA241A2ID")
    value("U1", "FD6288T")
    value("U6", "ADS8588SIPM")
    value("U15", "TLV9024PWR")
    value("U16", "TLV9024PWR")
    value("U24", "TPS3808G33")
    value("U25", "TPS3808G50")

    for ref, expected in (("R50", 10e3), ("R51", 160e3),
                          ("R52", 160e3), ("R53", 10e3),
                          ("R1", 280e3), ("R2", 280e3), ("R3", 39e3),
                          ("C5", 10e-9), ("C1", 100e-6), ("C2", 100e-6)):
        value(ref, expected)

    for phase, shunt, amp, filter_r, filter_c, adc_pin, hi_pin, lo_pin in (
        ("U", "RSH1", "U2", "R40", "C40", 49, 4, 5),
        ("V", "RSH2", "U3", "R41", "C41", 51, 6, 7),
        ("W", "RSH3", "U4", "R42", "C42", 53, 8, 9),
    ):
        value(shunt, 0.005)
        value(filter_r, 47)
        value(filter_c, 1e-9)
        same((shunt, 1), (shunt, 3), (amp, 8))
        same((shunt, 2), (shunt, 4), (amp, 1))
        rail(shunt, 1, f"SW_{phase}")
        rail(shunt, 2, f"PH_{phase}")
        rail(amp, 2, "GND")           # REF1
        rail(amp, 3, "GND")           # GND
        rail(amp, 4, "GND")           # reserved NC, vendor requires GND
        rail(amp, 6, "VA_5V")        # VS
        rail(amp, 7, "VA_5V")        # REF2; 0.5 * supply centering
        same((amp, 5), (filter_r, 1))
        same((filter_r, 2), (filter_c, 1), ("U6", adc_pin),
             ("U15", hi_pin), ("U16", lo_pin))
        rail(filter_c, 2, "GND")

    rail("R50", 1, "VA_5V")
    rail("R51", 2, "GND")
    rail("R52", 1, "VA_5V")
    rail("R53", 2, "GND")
    same(("R50", 2), ("R51", 1), ("U15", 5), ("U15", 7), ("U15", 9))
    same(("R52", 2), ("R53", 1), ("U16", 4), ("U16", 6), ("U16", 8))
    for comp in ("U15", "U16"):
        for pin in (1, 2, 14):
            rail(comp, pin, "OCP_N")

    for pin in list(range(16, 23)) + list(range(27, 34)):
        rail("U6", pin, "GND")  # TI serial-mode straps
    for pin in (1, 37, 38, 48):
        rail("U6", pin, "VA_5V")
    rail("U6", 6, "VIO_3V3")

    for phase, diode, cap, bst_pin, vs_pin in (
        ("U", "D2", "CBOOT1", 20, 18),
        ("V", "D3", "CBOOT2", 17, 15),
        ("W", "D4", "CBOOT3", 14, 12),
    ):
        value(cap, 1e-6)
        rail(diode, 2, "VDRV_12V")  # SMA pad 2 is ANODE
        same((diode, 1), (cap, 1), ("U1", bst_pin))  # pad1 CATHODE
        rail(cap, 2, f"SW_{phase}")
        rail("U1", vs_pin, f"SW_{phase}")

    rail("U24", 5, "VIO_3V3")
    rail("U25", 5, "VA_5V")
    rail("U24", 6, "VIO_3V3")
    rail("U25", 6, "VIO_3V3")
    same(("U24", 1), ("U25", 1), ("U26", 1))
    same(("U26", 3), ("U15", 1), ("U16", 1))
    same(("U26", 2), ("U11", 3))
    same(("U20", 5), ("U11", 6))
    rail("U11", 1, "GATE_EN")

    # All values below originate from the current XML, not historical reports.
    result = {ref: passive(components[ref]) for ref in (
        "R1", "R2", "R3", "C5", "C1", "C2", "R50", "R51",
        "R52", "R53", "R40", "C40", "RSH1", "RSH2", "RSH3"
    )}
    return result


def corner_current_limits(values: dict[str, float],
                          rail_range: tuple[float, float] = (4.75, 5.25),
                          resistor_fraction: float = 0.001,
                          shunt_fraction: float = 0.01) -> dict:
    """Exploratory passive-only corner sweep; no IC error or temperature model."""
    high, low = [], []
    for rail, r50, r51, r52, r53, shunt in itertools.product(
        rail_range,
        (values["R50"] * (1-resistor_fraction), values["R50"] * (1+resistor_fraction)),
        (values["R51"] * (1-resistor_fraction), values["R51"] * (1+resistor_fraction)),
        (values["R52"] * (1-resistor_fraction), values["R52"] * (1+resistor_fraction)),
        (values["R53"] * (1-resistor_fraction), values["R53"] * (1+resistor_fraction)),
        (values["RSH1"] * (1-shunt_fraction), values["RSH1"] * (1+shunt_fraction)),
    ):
        center = 0.5 * rail
        high.append(((rail * r51 / (r50+r51)) - center) / (INA_GAIN_V_PER_V * shunt))
        low.append((center - (rail * r53 / (r52+r53))) / (INA_GAIN_V_PER_V * shunt))
    nominal_rail = 5.0
    nominal_high_v = nominal_rail * values["R51"] / (values["R50"] + values["R51"])
    nominal_low_v = nominal_rail * values["R53"] / (values["R52"] + values["R53"])
    nominal_trip = (nominal_high_v - nominal_rail/2) / (INA_GAIN_V_PER_V * values["RSH1"])
    return {
        "reference_high_nominal_V": nominal_high_v,
        "reference_low_nominal_V": nominal_low_v,
        "positive_trip_nominal_A": nominal_trip,
        "positive_passive_corner_A": [min(high), max(high)],
        "negative_abs_passive_corner_A": [min(low), max(low)],
        "corner_basis": "VA5 4.75..5.25V; four resistors +/-0.1%; shunt +/-1%; REF2=VA5; REF1=GND",
        "excluded": [
            "INA241 gain/offset/output swing and PWM common-mode recovery",
            "TLV9024 input offset, propagation delay, output pull-up and overdrive",
            "resistor and shunt temperature drift/assembly thermal",
            "ADC aperture/settling/noise and PCB parasitics",
            "fault current slope and MOSFET actual turn-off time",
        ],
    }


def gate_report(netlist: Path) -> dict:
    components, pins = read_netlist(netlist)
    v = require_graph(components, pins)
    cap = v["C1"] + v["C2"]
    shunt_powers = [PHASE_RMS_A**2 * v[ref] for ref in ("RSH1", "RSH2", "RSH3")]
    tau = v["R40"] * v["C40"]
    g50_max = G50_THRESHOLD_V * (1 + G50_THRESHOLD_TOL)
    g33_release_max = G33_THRESHOLD_V * (1+G33_THRESHOLD_TOL) * (1+SUPERVISOR_HYSTERESIS_MAX)
    return {
        "schema_version": 2,
        "erc": {"status": "NOT_RUN", "reason": "Netlist checks do not execute ERC; use run_gate_ab.py"},
        "scope": "Electrical source checks + nominal/illustrative passive models only",
        "source_netlist_sha256": hashlib.sha256(netlist.read_bytes()).hexdigest(),
        "observed_system_components": len(components),
        "graph_checks": "PASS: pin-mapped current, ADC, bootstrap, OCP comparator/supervisor",
        "target": {"vbus_min_V": 24, "vbus_max_V": 48,
                   "phase_continuous_rms_provisional_A": PHASE_RMS_A, "pwm_Hz": PWM_HZ},
        "numerics": {
            "current_gain_V_per_A": INA_GAIN_V_PER_V * v["RSH1"],
            "shunt_loss_each_W_at_10A_RMS": shunt_powers,
            "bus_divider_48V_output_V": 48*v["R3"]/(v["R1"]+v["R2"]+v["R3"]),
            "bus_monitor_tau_s": ((v["R1"]+v["R2"])*v["R3"]/
                                   (v["R1"]+v["R2"]+v["R3"]))*v["C5"],
            "current_rc_tau_s": tau,
            "current_rc_fc_Hz": 1/(2*math.pi*tau),
            "gate_charge_six_mosfets_nominal_upper_test_condition_W": (
                6*MOSFET_QG_MAX_C*12*PWM_HZ),
            "ideal_lower_bound_turnon_s_at_advertised_peak_current": MOSFET_QG_MAX_C/FD6288_SOURCE_PEAK_A,
            "ideal_lower_bound_turnoff_s_at_advertised_peak_current": MOSFET_QG_MAX_C/FD6288_SINK_PEAK_A,
            "regeneration": {
                "bulk_nominal_F": cap,
                "energy_48_to_55_J": 0.5*cap*(55**2-48**2),
                "ideal_no_sink_1A_time_48_to_55_s": (55-48)*cap,
                "illustrative_1A_no_sink_after_1ms_V": 48 + 0.001/cap,
                "warning": "55V is NOT an approved voltage; ignores source/load and parasitics",
            },
            "adc_supply_vs_supervisor": {
                "ADS8588S_AVDD_min_V": ADC_AVDD_MIN_V,
                "TPS3808G50_falling_max_V": g50_max,
                "blind_window_at_least_V": ADC_AVDD_MIN_V-g50_max,
                "G33_worst_recovery_threshold_V": g33_release_max,
                "G50_worst_recovery_threshold_V": g50_max*(1+SUPERVISOR_HYSTERESIS_MAX),
                "conclusion": "G50 falling threshold cannot guarantee ADC AVDD remains valid",
            },
            "ocp": corner_current_limits(v),
        },
        "gate_a": {
            "status": "BLOCKED",
            "passed_checks": ["physical netlist contract"],
            "blocking_ids": ["A-ADC-UNDERVOLTAGE", "A-PEAK-THERMAL-SPEC",
                             "A-VENDOR-FOOTPRINT-MPN", "A-POWER-SEQUENCING"],
        },
        "gate_b": {
            "status": "BLOCKED",
            "blocking_ids": ["B-IC-TRANSIENT-MODELS", "B-TOTAL-OCP-DELAY",
                             "B-REGENERATION-SINK", "B-SWITCHING-SOA",
                             "B-BENCH-EVIDENCE"],
        },
        "interpretation": (
            "PASS of graph and SPICE checks is not Gate A/B closure, STO, "
            "PCB fabrication release or qualification of any active device"
        ),
    }


def generate_spice(values: dict[str, float], output_dir: Path) -> dict[str, Path]:
    """Explicit ideal-source/passive decks; no hidden vendor-model claim."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cap = values["C1"] + values["C2"]
    regen = output_dir / "regeneration.cir"
    regen.write_text(f"""* Ideal unsunk DC-link regeneration. Not a clamp qualification.
Iregen 0 bus DC 1
Cbulk bus 0 {cap:.12g} IC=48
.tran 1u 1.4m uic
.control
set wr_singlescale
set wr_vecnames
run
wrdata regeneration.dat v(bus)
quit
.endc
.end
""", encoding="utf-8")
    filter_deck = output_dir / "ocp_filter.cir"
    filter_deck.write_text(f"""* Ideal voltage step representing a current-amplifier output.
* No INA, comparator, latch, driver or MOSFET models present.
Vrail rail 0 5
R50 rail hi {values['R50']:.12g}
R51 hi 0 {values['R51']:.12g}
Vmeas source 0 PWL(0 2.5 1u 2.5 1.001u 4.9 1.4u 4.9)
R40 source filtered {values['R40']:.12g}
C40 filtered 0 {values['C40']:.12g} IC=2.5
.tran 1n 1.35u uic
.control
set wr_singlescale
set wr_vecnames
run
wrdata ocp_filter.dat v(filtered)
quit
.endc
.end
""", encoding="utf-8")
    return {"regeneration": regen, "ocp_filter": filter_deck}


def _rows(path: Path) -> list[tuple[float, float]]:
    result = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        cols = line.split()
        if not cols:
            continue
        if not result and index == 0 and cols[0].lower() == "time":
            continue
        if len(cols) != 2:
            raise RuntimeError(f"Malformed waveform row: {path}:{index+1}")
        try:
            t, value = map(float, cols)
        except ValueError as exc:
            raise RuntimeError(f"Malformed waveform row: {path}:{index+1}") from exc
        if not (math.isfinite(t) and math.isfinite(value)) or t < 0:
            raise RuntimeError(f"Nonfinite/negative waveform data: {path}:{index+1}")
        if result and t <= result[-1][0]:
            raise RuntimeError(f"Nonmonotonic waveform time: {path}:{index+1}")
        result.append((t, value))
    if len(result) < 2:
        raise RuntimeError(f"Incomplete ngspice waveform: {path}")
    return result


def run_spice(values: dict[str, float], output_dir: Path, executable: str) -> dict:
    output_dir = output_dir.resolve()
    decks = generate_spice(values, output_dir)
    # Remove only this runner's expected outputs, never unrelated evidence.
    for name in decks:
        (output_dir / f"{name}.dat").unlink(missing_ok=True)
        (output_dir / f"{name}.log").unlink(missing_ok=True)
    if not shutil.which(executable):
        raise RuntimeError(f"ngspice executable unavailable: {executable}")
    logs = []
    for name, deck in decks.items():
        completed = subprocess.run([executable, "-b", deck.name], cwd=output_dir,
                                   text=True, capture_output=True, check=False, timeout=60)
        (output_dir / f"{name}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(f"{name} ngspice failed: exit {completed.returncode}")
        logs.append(name)
    regen = _rows(output_dir / "regeneration.dat")
    last_t, last_v = regen[-1]
    if regen[0][0] > 2e-6 or abs(regen[0][1] - 48) > 0.025:
        raise RuntimeError("Invalid regeneration initial conditions")
    expected = 48 + last_t / (values["C1"] + values["C2"])
    if abs(last_v-expected) > 0.025 or not 0.00139 <= last_t <= 0.00141:
        raise AssertionError(f"Regeneration SPICE != analytical capacitor law: {last_v} vs {expected}")
    trace = _rows(output_dir / "ocp_filter.dat")
    if trace[0][0] > 1e-9 or trace[-1][0] < 1.34e-6:
        raise RuntimeError("Incomplete OCP waveform time range")
    if abs(trace[0][1] - 2.5) > 0.01:
        raise RuntimeError("Invalid OCP initial voltage")
    vth = 5 * values["R51"]/(values["R50"]+values["R51"])
    crosses = [t for t, v in trace if t >= 1e-6 and v >= vth]
    if not crosses:
        raise AssertionError("Ideal OCP analog voltage never crossed the computed upper threshold")
    crossing = crosses[0]
    tau = values["R40"] * values["C40"]
    analytical = 1.001e-6 - tau * math.log((4.9-vth)/(4.9-2.5))
    if abs(crossing - analytical) > 15e-9:
        raise AssertionError(f"RC step crossing {crossing} != ideal calculation {analytical}")
    return {
        "status": "PASS_ONLY_IDEAL_PASSIVE",
        "ngspice_decks": logs,
        "regeneration_final_s": last_t,
        "regeneration_final_V": last_v,
        "ocp_filter_ideal_threshold_crossing_s": crossing,
        "ocp_filter_analytical_crossing_s": analytical,
        "excluded": "INA, TLV9024, digital latch, FD6288, MOSFET, layout parasitics and tolerances",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--netlist", type=Path, required=True, help="Fresh KiCad XML export")
    p.add_argument("--output", type=Path, required=True, help="JSON audit evidence")
    p.add_argument("--spice-output", type=Path, help="Run two ideal passive ngspice decks")
    p.add_argument("--ngspice", default="ngspice")
    p.add_argument("--strict-gates", action="store_true",
                   help="Return nonzero if Gate A/B are not actually qualified")
    a = p.parse_args()
    try:
        report = gate_report(a.netlist)
        if a.spice_output:
            components, _ = read_netlist(a.netlist)
            values = {ref: passive(components[ref]) for ref in (
                "C1", "C2", "R50", "R51", "R40", "C40")}
            report["spice"] = run_spice(values, a.spice_output, a.ngspice)
        else:
            report["spice"] = {"status": "NOT_RUN"}
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Graph: {report['graph_checks']}; SPICE: {report['spice']['status']}")
        print(f"Gate A={report['gate_a']['status']}, Gate B={report['gate_b']['status']}")
        print(f"Evidence: {a.output}")
        return 2 if a.strict_gates else 0
    except (OSError, KeyError, ValueError, RuntimeError, AssertionError, ET.ParseError,
            subprocess.TimeoutExpired) as exc:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        failure = {"schema_version": 2, "status": "FAILED", "error": str(exc),
                   "gate_a": {"status": "BLOCKED"}, "gate_b": {"status": "BLOCKED"}}
        a.output.write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
        print(f"GATE AB CHECK FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
