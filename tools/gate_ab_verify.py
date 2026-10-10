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
G33_THRESHOLD_V = 3.07               # TPS3808G33 nominal falling threshold
G33_THRESHOLD_TOL = 0.015
SUPERVISOR_HYSTERESIS_MAX = 0.025    # Conservative margin from project review
INA_GAIN_V_PER_V = 20.0              # INA240A1 nominal gain
MOSFET_VDS_MAX_V = 100.0             # BSC040N10NS5 absolute maximum
MOSFET_QG_MAX_C = 72e-9              # At published test conditions, not worst application
DRV8300_SOURCE_PEAK_A = .75           # Nominal/advertised peak, NOT guaranteed lower bound
DRV8300_SINK_PEAK_A = 1.5
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
        value(ref, "INA240A1DR")
    value("U1", "DRV8300DPWR")  # D non-inverted; DI is unsafe with the all-low inhibit.
    value("U6", "ADS8588SIPM")
    value("U15", "LM393LVDDFR")
    value("U5", "INA240A1DR")
    value("F1", "25A_0456025.ER")
    for obsolete in ("U16", "R51", "R52", "D2", "D3", "D4", "J2"):
        if obsolete in components:
            raise TopologyError(f"Obsolete phase OCP/bootstrap component present: {obsolete}")
    value("U24", "TPS3808G33")
    value("U25", "TPS389001DSER")
    value("U13", "TPS62901RPJR")
    for ref, expected in (("R92", 3240.), ("R93", 1000.),
                          ("R94", 75000.), ("R95", 10000.), ("C94", 100e-9)):
        value(ref, expected)

    for ref, expected in (("R50", 8200.), ("R53", 2000.),
                          ("R1", 280e3), ("R2", 280e3), ("R3", 39e3),
                          ("C5", 10e-9), ("C1", 100e-6), ("C2", 100e-6)):
        value(ref, expected)

    for phase, shunt, amp, filter_r, filter_c, adc_pin in (
        ("U", "RSH1", "U2", "R40", "C40", 49),
        ("V", "RSH2", "U3", "R41", "C41", 51),
        ("W", "RSH3", "U4", "R42", "C42", 53),
    ):
        value(shunt, 0.005)
        value(filter_r, 47)
        value(filter_c, 1e-9)
        same((shunt, 1), (amp, 8))
        same((shunt, 2), (amp, 1))
        rail(shunt, 1, f"SW_{phase}")
        rail(shunt, 2, f"PH_{phase}")
        rail(amp, 2, "GND")           # GND
        rail(amp, 3, "GND")           # REF2
        rail(amp, 4, "GND")           # NC: INA240 D permits GND or floating; design grounds it
        rail(amp, 6, "VA_5V")        # VS
        rail(amp, 7, "VA_5V")        # REF1; 0.5 * supply centering
        same((amp, 5), (filter_r, 1))
        same((filter_r, 2), (filter_c, 1), ("U6", adc_pin))
        phase_nets = {net(amp, 5), net(filter_r, 2)}
        if any(name in phase_nets for (ref, _), name in pins.items() if ref in ("U15", "U16")):
            raise TopologyError(f"Phase {phase} OCP tap resurrected")
        rail(filter_c, 2, "GND")

    value("RSH4", .002)
    rail("RSH4", 1, "VBUS_PROT")
    rail("RSH4", 2, "VBUS_BRIDGE")
    same(("U5", 8), ("RSH4", 1))
    same(("U5", 1), ("RSH4", 2))
    for pin in (2, 3, 4, 7):
        rail("U5", pin, "GND")
    rail("U5", 6, "VA_5V")
    same(("U5", 5), ("U15", 2))  # Positive bus current pulls OCP_N low.
    # Native Infineon PG-TDSON footprint numbers all drain lands 5;
    # there are no separate schematic pins 6..8. PCB parity checks every land.
    for ref in ("Q1", "Q3", "Q5"):
        rail(ref, 5, "VBUS_BRIDGE")
    rail("R50", 1, "VA_5V")
    rail("R53", 2, "GND")
    same(("R50", 2), ("R53", 1), ("U15", 3), ("U15", 6))
    for pin in (4, 5):
        rail("U15", pin, "GND")
    rail("U15", 8, "VA_5V")
    rail("U15", 1, "OCP_N")
    if not pins.get(("U15", "7"), "").startswith("unconnected-"):
        raise TopologyError("Unused U15.7 output must remain NC")
    for cap, ic, power, ground in (("C84", "U5", 6, 2), ("C85", "U15", 8, 4)):
        value(cap, 100e-9)
        same((cap, 1), (ic, power))
        same((cap, 2), (ic, ground))
    same(("J3", 1), ("F1", 1))
    same(("F1", 2), ("Q7", 5), ("U18", 1), ("U18", 5))
    if net("F1", 1).rsplit("/", 1)[-1] != "VIN_RAW" or net("F1", 2).rsplit("/", 1)[-1] != "VIN_FUSED":
        raise TopologyError("Onboard F1 must separate VIN_RAW from VIN_FUSED")
    if "J6" in components:  # System XML retains the off-board source interface.
        same(("J6", 1), ("J3", 1))

    for pin in list(range(16, 23)) + list(range(27, 34)):
        rail("U6", pin, "GND")  # TI serial-mode straps
    for pin in (1, 37, 38, 48):
        rail("U6", pin, "VA_5V")
    rail("U6", 6, "VIO_3V3")

    rail("U1", 7, "VDRV_12V")
    rail("U1", 8, "GND")
    for phase, cap, bst_pin, vs_pin in (
        ("U", "CBOOT1", 20, 18), ("V", "CBOOT2", 17, 15),
        ("W", "CBOOT3", 14, 12),
    ):
        value(cap, 470e-9)
        same((cap, 1), ("U1", bst_pin))
        rail(cap, 2, f"SW_{phase}")
        rail("U1", vs_pin, f"SW_{phase}")
    for index, output in enumerate((19, 11, 16, 10, 13, 9), 1):
        value(f"RG{index}", 33.)
        same(("U1", output), (f"RG{index}", 1))
        same((f"RG{index}", 2), (f"Q{index}", 4))
    for gate, output, driver in (("U8", 7, 1), ("U9", 7, 2), ("U10", 7, 3),
                                  ("U8", 3, 4), ("U9", 3, 5), ("U10", 3, 6)):
        same((gate, output), ("U1", driver))

    rail("U24", 5, "VIO_3V3")
    same(("U25", 1), ("R92", 2), ("R93", 1))
    rail("R92", 1, "VA_5V")
    rail("R93", 2, "GND")
    rail("U25", 2, "GND")
    rail("U25", 3, "VIO_3V3")
    same(("U25", 5), ("C94", 1))
    rail("C94", 2, "GND")
    rail("U24", 6, "VIO_3V3")
    rail("U25", 4, "VIO_3V3")
    same(("U24", 1), ("U25", 6), ("U26", 1))
    same(("U26", 3), ("U15", 1))
    same(("U26", 2), ("U11", 3))
    same(("U20", 5), ("U11", 6))
    rail("U11", 1, "GATE_EN")

    # All values below originate from the current XML, not historical reports.
    result = {ref: passive(components[ref]) for ref in (
        "R1", "R2", "R3", "C5", "C1", "C2", "R50", "R53", "R40", "C40", "RSH1", "RSH2", "RSH3", "RSH4"
    )}
    return result


def corner_current_limits(values: dict[str, float],
                          rail_range: tuple[float, float] = (4.75, 5.25),
                          resistor_fraction: float = 0.001,
                          shunt_fraction: float = 0.01,
                          nominal_rail: float = 5.1) -> dict:
    """Positive bus-only passive corners; caller supplies actual regulated rail bounds."""
    trips = []
    for rail, top, bottom, shunt in itertools.product(
        rail_range,
        (values["R50"] * (1-resistor_fraction), values["R50"] * (1+resistor_fraction)),
        (values["R53"] * (1-resistor_fraction), values["R53"] * (1+resistor_fraction)),
        (values["RSH4"] * (1-shunt_fraction), values["RSH4"] * (1+shunt_fraction)),
    ):
        trips.append(rail * bottom / (top + bottom) / (INA_GAIN_V_PER_V * shunt))
    threshold = nominal_rail * values["R53"] / (values["R50"] + values["R53"])
    return {
        "reference_nominal_V": threshold,
        "positive_trip_nominal_A": threshold / (INA_GAIN_V_PER_V * values["RSH4"]),
        "positive_passive_corner_A": [min(trips), max(trips)],
        "reverse_current_protection": False,
        "rail_range_V": list(rail_range),
        "corner_basis": "Supplied VA5 bounds; R50/R53 +/-0.1%; RSH4 +/-1%; both INA references grounded",
        "excluded": ["INA240 gain/offset/output swing and PWM common-mode recovery",
                     "LM393LV offset, propagation, overdrive and open-drain pull-up",
                     "Temperature drift/assembly thermal, layout parasitics",
                     "Fault current slope and complete MOSFET turn-off timing"],
    }



def bus_static_error_budget(values: dict[str, float], rail_range: tuple[float, float]) -> dict:
    """Conditional engineering budget for selected BOM, not guaranteed protection.

    INA240 SBOS662C p5; LM393LV SNOSDA4D p10; RESI PTFR C16003 V8
    ordering code P; FH TD code G; HoYLR HoS20260514-73 pp3/5.
    Shunt TCR is specified only +25..+125C, hence no cold-range claim.
    """
    resistor_fraction = .001 + 25e-6 * 105  # worst difference from +20C reference
    shunt_fraction = .01 + 50e-6 * 100
    gain_fraction = .002 + 2.5e-6 * 100
    rail_deviation = max(abs(rail - 5.) for rail in rail_range)
    # INA: VOS + temperature + DC common-mode change 12V -> 48V + PSRR.
    ina_offset = 25e-6 + 250e-9 * 100 + 36 * 10**(-120/20) + 10e-6 * rail_deviation
    # Comparator full-temperature VOS already includes drift; add CMRR and PSRR.
    # 1.1V bounds both comparator input voltages around the 1V crossing.
    comparator_offset = .003 + 1.1 * 10**(-60/20) + rail_deviation * 10**(-70/20)
    trips = []
    for rail, top, bottom, shunt, gain, ina_vos, comp_vos in itertools.product(
        rail_range,
        (values["R50"]*(1-resistor_fraction), values["R50"]*(1+resistor_fraction)),
        (values["R53"]*(1-resistor_fraction), values["R53"]*(1+resistor_fraction)),
        (values["RSH4"]*(1-shunt_fraction), values["RSH4"]*(1+shunt_fraction)),
        (20*(1-gain_fraction), 20*(1+gain_fraction)),
        (-ina_offset, ina_offset), (-comparator_offset, comparator_offset),
    ):
        trips.append(((rail*bottom/(top+bottom)+comp_vos)/gain-ina_vos)/shunt)
    return {
        "nominal_trip_A": 25,
        "positive_static_engineering_corner_A": [min(trips), max(trips)],
        "guaranteed_trip_interval": False,
        "component_temperature_scope_C": [25, 125],
        "temperature_scope_note": "Calculation envelope only; board target and each component's lower temperature limit still apply. Cold shunt TCR not qualified.",
        "bus_common_mode_scope_V": [24, 48],
        "fractions": {"R50_R53_initial_plus_TCR": resistor_fraction,
                      "RSH4_initial_plus_TCR": shunt_fraction,
                      "INA_gain_initial_plus_drift": gain_fraction},
        "INA_input_offset_total_V": ina_offset,
        "LM393_input_offset_total_V": comparator_offset,
        "oem_sources": [
            {"url": "https://www.ti.com/lit/ds/symlink/ina240.pdf", "document": "SBOS662C", "section": "7.5, page5: gain/offset/drift, CMRR, PSRR and reference rejection"},
            {"url": "https://www.ti.com/lit/ds/symlink/lm393lv.pdf", "document": "SNOSDA4D", "section": "5.9, page10: LM393LV offset, CMRR, PSRR and table conditions"},
            {"url": "https://atta.szlcsc.com/upload/public/pdf/source/20250401/FF0B2EF5B31106388F28E532ECCD4B84.pdf", "document": "RESI PTFR C16003 V8", "section": "printedpage2 orderingcode P=25ppm/C; printedpage3 TCR reference20C"},
            {"url": "https://atta.szlcsc.com/upload/public/pdf/source/20200616/C657321_2CFA27FA726BC0D0F6223AF922169515.pdf", "document": "FH TD thin-film specification", "section": "orderingcode G=25ppm/C"},
            {"url": "https://atta.szlcsc.com/upload/public/pdf/source/20260807/2744A3B9486B05923CE3C700940B3DAC.pdf", "document": "HoS20260514-73 A0, HoYLR2512-3W-2mR-1%", "section": "page3 TCR50ppm/C; page5 test temperature25..125C and separate reliability allowances"}],
        "selected_parts": {"R50": "PTFR0603B8K20P9", "R53": "TD03G2001BT",
                           "RSH4": "HoYLR2512-3W-2mR-1%"},
        "limits": ["Not a guaranteed interval: LM393 offset/CMRR/PSRR table conditions are at/up to 5V; applying at actual 5.026..5.174V needs validation.",
                   "INA reference rejection and bias-current mismatch lack guaranteed maxima; grounded-reference application needs validation.",
                   "No assembly/reflow, long-term/load-life/humidity drift, thermoelectric or Kelvin copper error allocation.",
                   "No PWM common-mode transient, ripple, propagation delay, fault slope or MOSFET turn-off model."]}


def require_bus_budget_parts(netlist: Path) -> None:
    root = ET.parse(netlist).getroot()
    expected = {"R50": "PTFR0603B8K20P9", "R53": "TD03G2001BT",
                "RSH4": "HoYLR2512-3W-2mR-1%"}
    for ref, mpn in expected.items():
        comp = root.find(f'./components/comp[@ref="{ref}"]')
        actual = comp.findtext('./fields/field[@name="MPN"]') if comp is not None else None
        if actual != mpn:
            raise TopologyError(f"{ref}: static thermal budget requires reviewed MPN {mpn}; got {actual}")


def gate_report(netlist: Path) -> dict:
    components, pins = read_netlist(netlist)
    v = require_graph(components, pins)
    require_bus_budget_parts(netlist)
    cap = v["C1"] + v["C2"]
    shunt_powers = [PHASE_RMS_A**2 * v[ref] for ref in ("RSH1", "RSH2", "RSH3")]
    tau = v["R40"] * v["C40"]
    from check_adc_validity import verify as verify_adc
    adc_errors, adc_numerics = verify_adc(netlist)
    if adc_errors:
        raise TopologyError("; ".join(adc_errors))
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
            "six_mosfet_gate_charge_ideal_energy_rate_W_not_device_power": (
                6*MOSFET_QG_MAX_C*12*PWM_HZ),
            "illustrative_qg_div_peak_source_s_NOT_a_bound": MOSFET_QG_MAX_C/DRV8300_SOURCE_PEAK_A,
            "illustrative_qg_div_peak_sink_s_NOT_a_bound": MOSFET_QG_MAX_C/DRV8300_SINK_PEAK_A,
            "regeneration": {
                "bulk_nominal_F": cap,
                "energy_48_to_55_J": 0.5*cap*(55**2-48**2),
                "ideal_no_sink_1A_time_48_to_55_s": (55-48)*cap,
                "illustrative_1A_no_sink_after_1ms_V": 48 + 0.001/cap,
                "warning": "55V is NOT an approved voltage; ignores source/load and parasitics",
            },
            "adc_supply_vs_supervisor": {
                "ADS8588S_AVDD_min_V": ADC_AVDD_MIN_V,
                "G33_worst_recovery_threshold_V": g33_release_max,
                **adc_numerics,
                "conclusion": "Static threshold gap repaired; rapid droop/full-chain shutdown timing remains unqualified",
            },
            "bus_ocp_static_budget": bus_static_error_budget(v, tuple(adc_numerics["regulated_static_V"])),
            "ocp": corner_current_limits(v, rail_range=tuple(adc_numerics["regulated_static_V"]), nominal_rail=.6*(1+passive(components['R94'])/passive(components['R95']))),
        },
        "gate_a": {
            "status": "BLOCKED",
            "passed_checks": ["physical netlist contract", "ADC static threshold/recovery corners"],
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
    filter_deck = output_dir / "phase_current_filter.cir"
    filter_deck.write_text(f"""* Ideal voltage step representing a current-amplifier output.
* No INA, comparator, latch, driver or MOSFET models present.
Vmeas source 0 PWL(0 2.5 1u 2.5 1.001u 4.9 1.4u 4.9)
R40 source filtered {values['R40']:.12g}
C40 filtered 0 {values['C40']:.12g} IC=2.5
.tran 1n 1.35u uic
.control
set wr_singlescale
set wr_vecnames
run
wrdata phase_current_filter.dat v(filtered)
quit
.endc
.end
""", encoding="utf-8")
    return {"regeneration": regen, "phase_current_filter": filter_deck}


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
    trace = _rows(output_dir / "phase_current_filter.dat")
    if trace[0][0] > 1e-9 or trace[-1][0] < 1.34e-6:
        raise RuntimeError("Incomplete phase-current-filter waveform time range")
    if abs(trace[0][1] - 2.5) > 0.01:
        raise RuntimeError("Invalid phase-current-filter initial voltage")
    vth = 3.7  # Mid-step voltage of the phase ADC filter; NOT a bus OCP threshold.
    crosses = [t for t, v in trace if t >= 1e-6 and v >= vth]
    if not crosses:
        raise AssertionError("Ideal phase ADC filter never reached its mid-step voltage")
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
        "phase_current_filter_midstep_3p7V_s": crossing,
        "phase_current_filter_analytical_midstep_s": analytical,
        "excluded": "INA, LM393LV, digital latch, DRV8300, MOSFET, layout parasitics and tolerances",
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
                "C1", "C2", "R40", "C40")}
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
