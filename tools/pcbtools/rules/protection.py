"""Grouped rule families; explicit contexts and no import-time checks."""
from types import SimpleNamespace

def electrical_api():
    #!/usr/bin/env python3
    """Gate A/B netlist-backed electrical audit and deliberately bounded ngspice checks.

    This is NOT vendor-device simulation, a certified shutdown-time bound, or a
    fabrication approval. A passing execution means only the automated evidence ran.
    Use a freshly exported KiCad XML netlist (never the tracked historical XML).
    """

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
        text = value.strip().replace("Ohm", "R").replace("惟", "R")
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
        bank_caps = ['C1', 'C2', *[f'C{i}' for i in range(120, 128)]]
        if any(ref in components for ref in ['R120', *bank_caps[2:]]):
            for index, cap_ref in enumerate(bank_caps):
                resistor = f'R{120+index}'
                value(cap_ref, 100e-6)
                value(resistor, .33)
                rail(resistor, 1, 'VBUS_PROT')
                rail(cap_ref, 2, 'GND')
                same((resistor, 2), (cap_ref, 1))
                branch = net(cap_ref, 1)
                nodes = {node for node, name in pins.items() if name == branch}
                if nodes != {(resistor, '2'), (cap_ref, '1')}:
                    raise TopologyError(f'{cap_ref}: damped branch has unexpected physical pins')
            result['DC_LINK_TOTAL_F'] = sum(passive(components[ref]) for ref in bank_caps)
            result['DC_LINK_R_EQ_OHM'] = 1 / sum(1 / passive(components[f'R{120+i}'])
                                                for i in range(len(bank_caps)))
        else:
            for cap_ref in ('C1', 'C2'):
                rail(cap_ref, 1, 'VBUS_PROT')
                rail(cap_ref, 2, 'GND')
        return result


    def bulk_model(values):
        """Nominal equal-branch passive equivalent; excludes ESL/tolerance/source dynamics."""
        cap = values.get('DC_LINK_TOTAL_F', values['C1'] + values['C2'])
        resistance = values.get('DC_LINK_R_EQ_OHM', 0.)
        if not math.isfinite(cap) or cap <= 0 or not math.isfinite(resistance) or resistance < 0:
            raise TopologyError('Invalid nominal DC-link equivalent')
        return cap, resistance


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
        cap, bank_resistance = bulk_model(v)
        shunt_powers = [PHASE_RMS_A**2 * v[ref] for ref in ("RSH1", "RSH2", "RSH3")]
        tau = v["R40"] * v["C40"]
        from pcbtools.rules.adc import validity_api
        _family_check_adc_validity = validity_api()
        verify_adc = _family_check_adc_validity.verify
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
                    "series_damping_nominal_equivalent_ohm": bank_resistance,
                    "energy_48_to_55_J": 0.5*cap*(55**2-48**2),
                    "ideal_no_sink_1A_time_48_to_55_s": max(0., 55-48-bank_resistance)*cap,
                    "illustrative_1A_no_sink_after_1ms_V": 48 + bank_resistance + 0.001/cap,
                    "warning": "55V is NOT an approved voltage; isolated bulk-bank model excludes C3/C4, source/load, distributed ESL and actual PWM spectrum",
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
        cap, bank_resistance = bulk_model(values)
        capacitor_node = 'capnode' if bank_resistance else 'bus'
        damping = f'Rbank bus capnode {bank_resistance:.12g}\n' if bank_resistance else ''
        regen = output_dir / "regeneration.cir"
        regen.write_text(f"""* Ideal unsunk DC-link regeneration. Not a clamp qualification.
    * Isolated bulk bank only; excludes C3/C4, source/cable impedance and distributed ESL.
    Iregen 0 bus DC 1
    {damping}Cbulk {capacitor_node} 0 {cap:.12g} IC=48
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
        cap, bank_resistance = bulk_model(values)
        if regen[0][0] > 2e-6 or abs(regen[0][1] - (48 + bank_resistance)) > 0.025:
            raise RuntimeError("Invalid regeneration initial conditions")
        expected = 48 + bank_resistance + last_t / cap
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
    return SimpleNamespace(**locals())

def ocp_behavior(pins):
    from itertools import permutations, product
    class Circuit:
        def __init__(self):
            self.q = 0
            self.clock = 0
            self.inputs = {"GATE_EN": 0, "FAULT_CLEAR": 0, "OCP_N": 1,
                           "PWR_GOOD": 1, "vio_ok": 1, "va_ok": 1}

        def step(self, **changes):
            self.inputs.update(changes)
            levels = {"/GND": 0, "/VIO_3V3": 1}
            def put(ref, pin, value):
                levels[pins[(ref, pin)]] = int(bool(value))
            def get(ref, pin):
                return levels[pins[(ref, pin)]]
            for name in ["GATE_EN", "FAULT_CLEAR", "OCP_N", "PWR_GOOD"]:
                levels["/" + name] = self.inputs[name]
            # Qualified supervisor RESET outputs, after timeout; not an analog model.
            put("U24", "1", self.inputs["vio_ok"] and self.inputs["va_ok"])
            for a, y in [("1", "7"), ("3", "5"), ("6", "2")]:
                put("U26", y, get("U26", a))
            put("R88", "2", get("R88", "1"))  # DC state after RC settles
            put("U21", "4", get("U21", "2"))
            put("U22", "4", not get("U22", "2"))
            put("U23", "4", all(get("U23", p) for p in ["1", "3", "6"]))
            clock = get("U20", "1")
            if not get("U20", "6"):
                self.q = 0  # asynchronous clear dominates a simultaneous clear edge
            elif not get("U20", "7"):
                raise AssertionError("preset must remain inactive")
            elif clock and not self.clock:
                self.q = get("U20", "2")
            self.clock = clock
            put("U20", "5", self.q)
            put("U11", "4", all(get("U11", p) for p in ["1", "3", "6"]))
            return self.q, get("U11", "4"), levels

        def arm(self):
            assert self.step(GATE_EN=0, FAULT_CLEAR=0)[:2] == (0, 0)
            assert self.step(FAULT_CLEAR=1)[:2] == (1, 0)
            assert self.step(FAULT_CLEAR=0)[:2] == (1, 0)
            assert self.step(GATE_EN=1)[:2] == (1, 1)

    checks = 0
    for fault in ["OCP_N", "PWR_GOOD", "vio_ok", "va_ok"]:
        c = Circuit()
        c.arm()
        assert c.step(**{fault: 0})[:2] == (0, 0)
        assert c.step(**{fault: 1})[:2] == (0, 0)  # no automatic restart
        assert c.step(FAULT_CLEAR=1)[:2] == (0, 0)  # EN high cannot re-arm
        c.step(GATE_EN=0, FAULT_CLEAR=0)
        assert c.step(FAULT_CLEAR=1)[:2] == (1, 0)
        checks += 1

    for fault in ["OCP_N", "PWR_GOOD", "vio_ok", "va_ok"]:
        c = Circuit()
        c.step(FAULT_CLEAR=1)
        assert c.step(**{fault: 0})[:2] == (0, 0)
        assert c.step(**{fault: 1})[:2] == (0, 0)  # clear held high
        c.step(FAULT_CLEAR=0)
        assert c.step(FAULT_CLEAR=1)[:2] == (1, 0)
        c = Circuit()
        c.step(**{fault: 0})
        assert c.step(FAULT_CLEAR=1)[:2] == (0, 0)  # clear during fault
        assert c.step(**{fault: 1})[:2] == (0, 0)
        checks += 2

    # Every ordering of qualified power domains rising/falling, then recovery.
    for order in permutations(["vio_ok", "va_ok", "PWR_GOOD"]):
        c = Circuit()
        c.step(vio_ok=0, va_ok=0, PWR_GOOD=0)
        for rail in order:
            assert c.step(**{rail: 1})[:2] == (0, 0)
        c.arm()
        for rail in reversed(order):
            assert c.step(**{rail: 0})[:2] == (0, 0)
        for rail in order:
            assert c.step(**{rail: 1})[:2] == (0, 0)
        checks += 1

    c = Circuit()
    c.arm()
    assert c.step(OCP_N=0, FAULT_CLEAR=1)[:2] == (0, 0)
    assert c.step(OCP_N=1)[:2] == (0, 0)
    checks += 1

    # Enumerate all six PWM states; each actual AND output must obey RUN_OK.
    for q, en, pg in product([0, 1], repeat=3):
        c = Circuit()
        c.q = q
        armed, run, levels = c.step(GATE_EN=en, PWR_GOOD=pg)
        for mask in range(64):
            for index, gate in enumerate(["U8", "U9", "U10"]):
                for channel, (a, b, out) in enumerate([("1", "2", "3"), ("5", "6", "7")]):
                    raw = (mask >> (index * 2 + channel)) & 1
                    levels[pins[(gate, a)]] = raw
                    output = pins[(gate, out)]
                    levels[output] = int(levels[pins[(gate, a)]] and levels[pins[(gate, b)]])
                    driver_pin = str(index + 4 if channel == 0 else index + 1)
                    assert levels[pins[("U1", driver_pin)]] == (raw and run), (gate, out, mask)
            checks += 1
    return checks

def gate_resistor_errors(parts, selection):
    errors = []
    for i in range(1, 7):
        ref = f'RG{i}'
        expected = {'MPN': selection['mpn'], 'Value': '33R', 'Footprint': selection['footprint']}
        if parts.get(ref) != expected:
            errors.append(f'{ref}: retain reviewed pulse-proof 33R identity and OEM land')
    return errors


def check_gate_resistors(project, xml=None):
    import csv
    import xml.etree.ElementTree as ET
    from pcbtools.schematic import discover_sheets
    from pcbtools.kicad import extract_forms, property_value
    selection = project.parameters['gate_resistor_selection']
    parts = {}
    for path in discover_sheets(project):
        for form in extract_forms(path.read_text(encoding='utf-8'), 'symbol'):
            if '(lib_id ' in form.text:
                parts[property_value(form.text, 'Reference')] = {
                    k: property_value(form.text,k) for k in ['MPN','Value','Footprint']}
    errors = gate_resistor_errors(parts, selection)
    with project.bom.open(encoding='utf-8-sig', newline='') as stream:
        rows = {r['Ref']: r for r in csv.DictReader(stream)}
    for i in range(1,7):
        row = rows.get(f'RG{i}', {})
        if row.get('MPN') != selection['mpn'] or row.get('Package') != selection['footprint']:
            errors.append(f'RG{i}: BOM pulse-proof selection differs from schematic')
    if xml:
        root = ET.parse(xml).getroot()
        native = {c.get('ref'): {'Value':c.findtext('value'), 'Footprint':c.findtext('footprint'),
                  'MPN':c.findtext('fields/field[@name="MPN"]')}
                  for c in root.findall('components/comp')}
        errors += gate_resistor_errors(native, selection)
    return errors


def check_safety(project, path):
    """Check exported KiCad netlist for critical safety and acquisition paths."""
    from pathlib import Path
    import sys
    from pcbtools.kicad import extract_forms, head_string


    text = path.read_text(encoding="utf-8")
    errors = []
    pin_nets = {}
    net_nodes = {}
    values = {}

    def field(text, key):
        forms = extract_forms(text, key)
        return head_string(forms[0].text, key) if forms else None

    for comp in extract_forms(text, "comp"):
        values[field(comp.text, "ref")] = field(comp.text, "value")
    for net in extract_forms(text, "net"):
        name = field(net.text, "name")
        nodes = set()
        for node in extract_forms(net.text, "node"):
            key = (field(node.text, "ref"), field(node.text, "pin"))
            pin_nets[key] = name
            nodes.add(key)
        net_nodes[name] = nodes

    def same(*pins):
        nets = [pin_nets.get(pin) for pin in pins]
        if None in nets or len(set(nets)) != 1 or nets[0].startswith("unconnected-"):
            errors.append(f"required connection missing: {pins}: {nets}")

    def rail(ref, pin, name):
        if pin_nets.get((ref, pin)) != "/" + name:
            errors.append(f"{ref}.{pin} must connect to {name}")

    # Exact fresh-export counts are recorded in the evidence; physical contracts fail closed.
    if len(values) < 150 or len(net_nodes) < 100:
        errors.append(f"incomplete native board export: {len(values)} components / {len(net_nodes)} nets")
    if "J2" in values:
        errors.append("Unused J2 must be removed")
    for i, phase in enumerate("UVW", 1):
        ref = f"RSH{i}"
        if {pin for component, pin in pin_nets if component == ref} != {"1", "2"}:
            errors.append(f"{ref}: exactly two physical SMD terminals required")
        rail(ref, "1", f"SW_{phase}")
        rail(ref, "2", f"PH_{phase}")
    # Official D_SMA/D_SMC pad 1 is cathode; never infer polarity from drawing alone.
    rail("D1", "1", "VBUS_PROT")
    rail("D1", "2", "GND")
    for obsolete in ("D2", "D3", "D4", "U16", "R51", "R52"):
        if obsolete in values:
            errors.append(f"obsolete phase OCP/bootstrap component remains: {obsolete}")
    # TI ADS8588S SBAS642A section8.4.1.13/.14/.17, serial mode.
    rail("U6", "6", "VIO_3V3")
    for pin in [*range(16, 23), *range(27, 34)]:
        rail("U6", str(pin), "GND")
    if "J6" in values:
        errors.append("J6 alone remains an off-board system interface")
    if values.get("F1") != "25A_0456025.ER":
        errors.append("onboard F1 must be 25A_0456025.ER")
    same(("J3", "1"), ("F1", "1"))
    same(("F1", "2"), ("Q7", "5"), ("U18", "1"), ("U18", "5"))
    # ALINX J10 manufacturer schematic: ground 1/37/38, 3.3V 39/40, 5V 2 NC.
    for pin in ("1", "37", "38"):
        rail("J1", pin, "GND")
    for pin in ("39", "40"):
        rail("J1", pin, "VIO_3V3")
    if not pin_nets.get(("J1", "2"), "").startswith("unconnected-"):
        errors.append("J10 +5V pin2 must stay NC; never tie to local VA_5V")
    active_j10 = {
        "3": "PWM_UH", "4": "PWM_UL", "5": "PWM_VH", "6": "PWM_VL",
        "7": "PWM_WH", "8": "PWM_WL", "9": "GATE_EN", "10": "FAULT_CLEAR",
        "11": "ADC_CONVST", "12": "ADC_SCLK", "13": "ADC_CS_N", "14": "ADC_RESET",
        "15": "ADC_DOUTA", "16": "ADC_DOUTB", "17": "ADC_BUSY", "18": "ADC_FRSTDATA",
        "19": "ENC_A", "20": "ENC_B", "21": "ENC_Z", "23": "OCP_N", "24": "PWR_GOOD",
    }
    for pin, name in active_j10.items():
        rail("J1", pin, name)
    for i, pin in enumerate(["3", "4", "5", "6", "7", "8", "9"]):
        ref = f"R{80 + i}"
        same(("J1", pin), (ref, "1"))
        rail(ref, "2", "GND")
        if values.get(ref) != "10k":
            errors.append(f"{ref}: required 10k reset-state pull-down missing")
    for cap, ic, power, ground, supply in [
        ("C80", "U8", "8", "4", "VIO_3V3"),
        ("C81", "U9", "8", "4", "VIO_3V3"),
        ("C82", "U10", "8", "4", "VIO_3V3"),
        ("C83", "U11", "5", "2", "VIO_3V3"),
        ("C84", "U5", "6", "2", "VA_5V"),
        ("C85", "U15", "8", "4", "VA_5V"),
    ]:
        same((cap, "1"), (ic, power))
        same((cap, "2"), (ic, ground))
        rail(cap, "1", supply)
        rail(cap, "2", "GND")
        if values.get(cap) != "100nF":
            errors.append(f"{ic}: required 100nF local decoupling missing")
    for cap in ["C43", "C44", "C45"]:
        rail(cap, "1", "VA_5V")
        rail(cap, "2", "GND")
    for ref in values:
        if ref.startswith(("C", "R", "L")):
            nets = [net for (component, pin), net in pin_nets.items() if component == ref]
            if len(nets) > 1 and len(set(nets)) == 1:
                errors.append(f"{ref}: all terminals are on the same net")
    for i in range(1, 7):
        same((f"RG{i}", "2"), (f"Q{i}", "4"), (f"RGS{i}", "1"))
    for amp, resistor, adc_pin in [("U2", "R40", "49"), ("U3", "R41", "51"), ("U4", "R42", "53")]:
        # INA240 D-package Table 6-1: pin 4 NC may connect to GND.
        if values.get(amp) != "INA240A1DR":
            errors.append(f"{amp}: INA240A1DR 20V/V part required")
        rail(amp, "4", "GND")
        same((amp, "5"), (resistor, "1"))
        same((resistor, "2"), ("U6", adc_pin))
    rail("U11", "1", "GATE_EN")
    rail("U11", "3", "PWR_READY")
    rail("U11", "6", "ARMED")
    # Physical pins checked against the TI DCU/DBV/DCK package tables.
    for ref, part in [("U20", "SN74LVC1G74"), ("U21", "SN74LVC1G17"),
                      ("U22", "SN74LVC1G14"), ("U23", "SN74LVC1G11"),
                      ("U24", "TPS3808G33"), ("U25", "TPS389001DSER")]:
        if values.get(ref) != part:
            errors.append(f"{ref}: latch function requires {part}")

    same(("U20", "5"), ("U11", "6"), ("R90", "1"), ("TP5", "1"))
    same(("U20", "2"), ("U22", "4"))
    same(("U20", "1"), ("U21", "4"))
    same(("U20", "6"), ("U23", "4"), ("R91", "1"))
    rail("U20", "7", "VIO_3V3")
    rail("U22", "2", "GATE_EN")
    same(("J1", "10"), ("R87", "1"), ("R88", "1"))
    same(("R88", "2"), ("C92", "1"), ("U21", "2"))
    same(("U23", "1"), ("U26", "5"))
    rail("U26", "3", "OCP_N")
    same(("U23", "3"), ("U26", "2"), ("U11", "3"))
    rail("U26", "6", "PWR_GOOD")
    rail("R55", "1", "PWR_GOOD")
    rail("R55", "2", "VIO_3V3")
    rail("R54", "1", "OCP_N")
    rail("R54", "2", "VIO_3V3")
    same(("U26", "1"), ("U24", "1"), ("U25", "6"), ("R89", "2"))
    same(("U26", "7"), ("U23", "6"))
    rail("U26", "8", "VIO_3V3")
    rail("U26", "4", "GND")
    same(("U26", "8"), ("C93", "1"))
    same(("U26", "4"), ("C93", "2"))
    if values.get("U26") != "SN74LVC3G17" or values.get("C93") != "100nF":
        errors.append("supervisor reset release requires U26 Schmitt conditioning and C93")
    rail("R89", "1", "VIO_3V3")
    for ref in ["R87", "R90", "R91", "C92"]:
        rail(ref, "2", "GND")
    for ref, value in [("R87", "10k"), ("R88", "1k"), ("R89", "100k"),
                       ("R90", "10k"), ("R91", "10k"), ("C92", "1nF")]:
        if values.get(ref) != value:
            errors.append(f"{ref}: required latch bias/filter {value} missing")
    for ic, cap, power, ground in [("U20", "C86", "8", "4"),
                                   ("U21", "C87", "5", "3"),
                                   ("U22", "C88", "5", "3"),
                                   ("U23", "C89", "5", "2"),
                                   ("U24", "C90", "6", "2"),
                                   ("U25", "C91", "4", "2")]:
        rail(ic, power, "VIO_3V3")
        rail(ic, ground, "GND")
        same((ic, power), (cap, "1"))
        same((ic, ground), (cap, "2"))
        if values.get(cap) != "100nF":
            errors.append(f"{ic}: required 100nF latch decoupling missing")
    for ic, sense in [("U24", "VIO_3V3")]:
        rail(ic, "5", sense)
        rail(ic, "3", "VIO_3V3")
        if not (pin_nets.get((ic, "4")) or "").startswith("unconnected-"):
            errors.append(f"{ic}.CT must be open for fixed reset timeout")
    rail("U25", "3", "VIO_3V3")
    same(("U25", "1"), ("R92", "2"), ("R93", "1"))
    rail("R92", "1", "VA_5V")
    rail("R93", "2", "GND")
    same(("U25", "5"), ("C94", "1"))
    rail("C94", "2", "GND")
    if not (pin_nets.get(("U20", "3")) or "").startswith("unconnected-"):
        errors.append("U20 inverted Q must remain unconnected")

    for gate, output, driver, pull in [("U8", "7", "1", "R56"), ("U9", "7", "2", "R58"),
                                       ("U10", "7", "3", "R60"), ("U8", "3", "4", "R57"),
                                       ("U9", "3", "5", "R59"), ("U10", "3", "6", "R61")]:
        same((gate, output), ("U1", driver), (pull, "1"))
        rail(pull, "2", "GND")
    for gate in ["U8", "U9", "U10"]:
        same(("U11", "4"), (gate, "2"), (gate, "6"))
    # TI SLLS849E PW16: + / - inputs are 2/1, 6/7, 10/9.
    for esd_pin, receiver_pin in [("14", "2"), ("13", "1"), ("12", "6"), ("11", "7"), ("9", "10"), ("8", "9")]:
        same(("U19", esd_pin), ("U7", receiver_pin))
    for esd_pin in ["5", "10"]:
        rail("U19", esd_pin, "GND")
    for esd_pin in ["1", "2", "3", "4", "6", "7"]:
        if not (pin_nets.get(("U19", esd_pin)) or "").startswith("unconnected-"):
            errors.append(f"U19.{esd_pin}: RVZ NC pin must remain unconnected")
    for phase, amp in [("U", "U2"), ("V", "U3"), ("W", "U4")]:
        rail(amp, "8", f"SW_{phase}")
        rail(amp, "1", f"PH_{phase}")
    # Share the XML auditor's physical-pin contract; this parser supplies the board-only view.
    from pcbtools.rules.protection import electrical_api
    _family_gate_ab_verify = electrical_api()
    require_graph = _family_gate_ab_verify.require_graph
    TopologyError = _family_gate_ab_verify.TopologyError
    try:
        require_graph(values, pin_nets)
    except TopologyError as exc:
        errors.append(str(exc))
    return errors
