"""Grouped rule families; explicit contexts and no import-time checks."""
from types import SimpleNamespace

def serial_api(project):
    """Static source-level Rev.A dual-serial ADC contract and timing-budget guard.

    This is deliberately NOT a replacement for a fresh KiCad pin-level XML netlist,
    native ERC, FPGA STA or scope-verified sampling performance. It catches
    reintroduction of unfitted parallel XDC, missing dual-DOUT ports and confusing
    a board-mounted NTC with an external motor sensor.

    TI ADS8588S SBAS642A: serial tSCLK>=50 ns; 2*4*16-bit -> 64 clocks, both
    DOUTs. Conversion max 3.9 us, no oversampling. Post-conversion dual-DOUT
    minimum tCYC=9.7 us; overlapped previous-frame read tCYC=5 us.
    """
    import csv
    import re
    import sys
    from pathlib import Path

    ROOT = project.root
    ADC_SIGNAL_NAMES = (
        "ADC_CONVST", "ADC_RESET", "ADC_SCLK", "ADC_CS_N",
        "ADC_DOUTA", "ADC_DOUTB", "ADC_BUSY", "ADC_FRSTDATA",
    )
    FPGA_PINS = {
        "ADC_CONVST": "Y14", "ADC_RESET": "N17", "ADC_SCLK": "W14",
        "ADC_CS_N": "P18", "ADC_DOUTA": "U15", "ADC_DOUTB": "U14",
        "ADC_BUSY": "P16", "ADC_FRSTDATA": "P15",
    }
    SCLK_MHZ_MAX = 20.0
    PWM_KHZ = 20.0
    BITS_PER_CHANNEL = 16
    CHANNELS = 8
    DOUT_LANES = 2
    SAMPLE_CYCLE_MIN_US = 5.0
    POST_CONVERSION_MIN_CYCLE_US = 9.7
    MAX_CONVERSION_US = 3.9


    def get_pin_lines(xdc: str) -> dict[str, list[str]]:
        seen: dict[str, list[str]] = {}
        for line in xdc.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.search(
                r"set_property\s+PACKAGE_PIN\s+(\w+)\s+\[get_ports\s+([A-Z0-9_]+)\]",
                line,
            )
            if m:
                seen.setdefault(m.group(2), []).append(m.group(1))
        return seen


    def timing():
        """Calculated serialization time (not full conversion-to-current-loop latency)."""
        clocks_dual = CHANNELS // DOUT_LANES * BITS_PER_CHANNEL
        clocks_single = CHANNELS * BITS_PER_CHANNEL
        return {
            "dual_sclk_cycles": clocks_dual,
            "single_sclk_cycles": clocks_single,
            "dual_20mhz_us": clocks_dual / SCLK_MHZ_MAX,
            "dual_10mhz_us": clocks_dual / 10,
            "one_20mhz_us": clocks_single / SCLK_MHZ_MAX,
            "pwm_cycle_us": 1000 / PWM_KHZ,
        }


    def check(root: Path = ROOT) -> list[str]:
        errors: list[str] = []
        sch = (root / "hardware/ads8588s_servo/current_adc.kicad_sch").read_text(encoding="utf-8")
        interface = (root / "hardware/ads8588s_servo/ax7010_interface.kicad_sch").read_text(encoding="utf-8")
        xdc = (root / "hardware/ads8588s_servo/ax7010_servo_reva.xdc").read_text(encoding="utf-8")
        with (root / "hardware/ads8588s_servo/bom.csv").open(encoding="utf-8", newline="") as fd:
            bom = {r["Ref"]: r for r in csv.DictReader(fd)}

        for name in ADC_SIGNAL_NAMES:
            token = '(hierarchical_label "' + name + '"'
            if token not in sch:
                errors.append(f"current_adc lacks actual hierarchy signal {name}")
            if token not in interface:
                errors.append(f"J10 interface lacks actual hierarchy signal {name}")

        if 'ADS8588S_SERIAL' not in sch or 'ADS8588SIPM' not in sch:
            errors.append("U6 must be the current ADS8588S serial 64-LQFP selection")
        if sch.count('(label "NTC_BOARD_AUX"') != 2 or 'NTC_MOTOR' in sch:
            errors.append("NTC2 must be identified as a local board sensor at both endpoints")
        if bom.get("NTC2", {}).get("Function") != "10k_B3950_BOARD_AUX":
            errors.append("NTC2 BOM must not claim motor-winding temperature")
        if bom.get("C3", {}).get("Function") != "1uF_250V_FILM":
            errors.append("C3 selected 250V film capacitor BOM metadata is stale")
        if 'aux_power' in project.rule_sets:
            import json
            profile = json.loads((project.root / project.parameters['aux_power_profile']).read_text(encoding='utf-8'))
            expected_l1 = profile['inductor']['value'] + '_12V_BUCK_1A_BENCH_OPEN'
        else:
            expected_l1 = "68uH_12V_BUCK_L1_IRMS_ISAT_OPEN"
        if bom.get("L1", {}).get("Function") != expected_l1:
            errors.append("L1 qualification state must match the reviewed design and retain the open bench gate")

        # Vivado indexed buses use [get_ports {ADC_DB[0]}], not a scalar.
        # Reject accidental live J11 constraints in both syntaxes.
        for raw_line in xdc.splitlines():
            line = raw_line.strip()
            if line.startswith("set_property") and "[get_ports {ADC_DB[" in line:
                errors.append("unfitted J11/PL_B parallel ADC_DB bus pin constraint")

        pins = get_pin_lines(xdc)
        for name, expected_pin in FPGA_PINS.items():
            actual = pins.get(name, [])
            if actual != [expected_pin]:
                errors.append(f"J10 XDC {name} must map once to {expected_pin}: {actual}")
        for name in pins:
            if name.startswith("ADC_DB") or name in {
                "ADC_RD_N", "ADC_BYTE_SEL", "ADC_RANGE",
                "ADC_OS0", "ADC_OS1", "ADC_OS2",
                "ADC_STBY", "ADC_PAR_SER", "BRAKE_OUT",
                "HALL_U", "HALL_V", "HALL_W",
            }:
                errors.append(f"unfitted J11/PL_B placeholder is an active XDC assignment: {name}")

        t = timing()
        if t["dual_sclk_cycles"] != 64 or t["single_sclk_cycles"] != 128:
            errors.append("dual/one lane ADS8588S bit frame regression")
        if abs(t["dual_20mhz_us"] - 3.2) > 1e-9:
            errors.append("incorrect two-lane 20MHz serial timing")
        if t["pwm_cycle_us"] < POST_CONVERSION_MIN_CYCLE_US:
            errors.append("20kHz PWM budget cannot include post-conversion dual-DOUT read")
        if t["dual_20mhz_us"] >= t["pwm_cycle_us"]:
            errors.append("dual-serial frame exceeds 20kHz PWM period")
        return errors
    return SimpleNamespace(**locals())

def fast_api(project):
    """Check proposed AD7606C-16 high-bandwidth ADC ECO without pretending it is wired.

    The existing Rev.A hardware/BOM still uses ADS8588S; this guard validates
    the prospective FPGA pin/register contract and stops a candidate from being
    mistaken for a committed production schematic. It is not KiCad ERC or STA.
    """

    import csv
    import json
    import re
    from pathlib import Path

    ROOT = project.root
    PROFILE = Path("hardware/ad7606c_servo/ad7606c_fast_candidate_profile_2026-10-12.json")
    CANDIDATES = Path("hardware/ad7606c_servo/adc_fast_candidates_2026-10-12.csv")
    SOURCE_BOM = Path("hardware/ads8588s_servo/bom.csv")
    XDC = Path("hardware/ads8588s_servo/ax7010_servo_reva.xdc")
    SCHEMATIC = Path("hardware/ads8588s_servo/current_adc.kicad_sch")

    LEGACY = {
        "ADC_CONVST": (11, "Y14"),
        "ADC_SCLK": (12, "W14"),
        "ADC_CS_N": (13, "P18"),
        "ADC_RESET": (14, "N17"),
        "ADC_DOUTA": (15, "U15"),
        "ADC_DOUTB": (16, "U14"),
        "ADC_BUSY": (17, "P16"),
        "ADC_FRSTDATA": (18, "P15"),
    }
    NEW = {
        "ADC_DOUTC": (29, "U12", "SPARE_A0"),
        "ADC_DOUTD": (30, "T12", "SPARE_A1"),
        "ADC_SDI": (31, "T10", "SPARE_A2"),
    }
    EXPECTED_REGISTERS = {
        "0x02": 0x10,
        "0x03": 0x55,
        "0x04": 0x65,
        "0x05": 0x66,
        "0x06": 0x66,
        "0x07": 0x0F,
        "0x08": 0x00,
    }


    def check(root: Path = ROOT) -> list[str]:
        e: list[str] = []
        d = json.loads((root / PROFILE).read_text(encoding="utf-8"))
        adc = d["selection"]
        if d.get("status") != "ECO_CANDIDATE_NOT_PRESENT_IN_WORKING_SCHEMATIC":
            e.append("candidate wrongly claims finished KiCad schematic or release")
        if adc.get("mpn") != "AD7606C-16BSTZ" or adc.get("lcsc") != "C5371769":
            e.append("selected performance ADC MPN / LCSC changed without review")
        if adc.get("packaging_alternate") != "AD7606C-16BSTZ-RL":
            e.append("unqualified ADC packing alternate")
        with (root / CANDIDATES).open(encoding="utf-8", newline="") as fd:
            candidates = {x["MPN"]: x for x in csv.DictReader(fd)}
        if candidates.get("AD7606C-16BSTZ", {}).get("Recommendation") != "PERFORMANCE_PRIMARY":
            e.append("performance sourcing candidate missing or switched")
        if candidates.get("AD7606C-16BSTZ", {}).get("Quote_currency") != "USD":
            e.append("web dollar quotation must not be mislabeled as yuan")
        with (root / SOURCE_BOM).open(encoding="utf-8", newline="") as fd:
            bom = {x["Ref"]: x for x in csv.DictReader(fd)}
        if bom.get("U6", {}).get("MPN") != "ADS8588SIPM":
            e.append("old vs candidate hardware status out of date: U6 BOM MPN differs")
        sch = (root / SCHEMATIC).read_text(encoding="utf-8")
        if '(property "Value" "ADS8588SIPM"' not in sch:
            e.append("old vs candidate hardware status out of date: schematic U6 changed")
        if d.get("mode_straps", {}).get("OS0") != 1 or d["mode_straps"].get("OS1") != 1 or d["mode_straps"].get("OS2") != 1:
            e.append("AD7606C software mode requires OS0=OS1=OS2=1")
        if d["mode_straps"].get("PAR_SER_SEL") != 1:
            e.append("AD7606C parallel-serial selection must be serial for J10")

        for addr, expected in EXPECTED_REGISTERS.items():
            try:
                actual = int(d["configuration"][addr]["value"], 16)
            except (KeyError, TypeError, ValueError):
                actual = None
            if actual != expected:
                e.append(f"AD7606C candidate register {addr} != expected 0x{expected:02x}")
        config = int(d["configuration"]["0x02"]["value"], 16)
        lanes = 1 << ((config >> 3) & 0b11)
        t = d["timing"]
        if lanes != 4 or t.get("serial_lanes") != 4:
            e.append("candidate must use 4 physical DOUT lanes")
        if t.get("adc_channels") != 8 or t.get("resolution_bits") != 16:
            e.append("candidate must carry eight simultaneously sampled 16-bit channels")
        expected_clocks = t["adc_channels"] * t["resolution_bits"] // t["serial_lanes"]
        if t.get("frame_sclk_edges") != expected_clocks or expected_clocks != 32:
            e.append("four-lane frame must use 32 20MHz SCLK periods")
        expected_us = expected_clocks / (t["initial_sclk_hz"] / 1_000_000)
        if abs(t.get("initial_frame_time_us", -1) - expected_us) > 1e-9:
            e.append("initial serial timing doesn't match lane count and SCLK")
        if t.get("analog_3db_bandwidth_khz") != 150:
            e.append("0-5V high-bandwidth option is 150kHz, not 220kHz")

        pins = d.get("external_pins", [])
        if len(pins) != 11:
            e.append("ADC candidate must map 8 existing + 3 new J10 signals")
        refs = {(x["signal"]): x for x in pins}
        if len(refs) != len(pins) or len({x["header_pin"] for x in pins}) != len(pins):
            e.append("duplicate candidate J10 net or header pin")
        if len({x["fpga_pin"] for x in pins}) != len(pins):
            e.append("duplicate Xilinx candidate PACKAGE_PIN")
        for name, (pin, pkg) in LEGACY.items():
            p = refs.get(name, {})
            if p.get("header_pin") != pin or p.get("fpga_pin") != pkg:
                e.append(f"{name}: don't change real J10 mapping silently")
        for name, (pin, pkg, old) in NEW.items():
            p = refs.get(name, {})
            if p.get("header_pin") != pin or p.get("fpga_pin") != pkg or p.get("legacy_signal") != old:
                e.append(f"{name}: future J10 spare allocation incorrect")

        # This is a candidate: new ADC signals MUST NOT already be active in the
        # old XDC until the new physical PCB copper and latest schematic exist.
        xdc = (root / XDC).read_text(encoding="utf-8")
        active = "\n".join(line for line in xdc.splitlines() if line.strip().startswith("set_property"))
        for name in NEW:
            if re.search(r"\[get_ports\s+" + name + r"\]", active):
                e.append(f"{name} erroneously enabled on current unmigrated XDC")

        lanes_expected = {
            "DOUTA": ["IU_ADC", "IV_ADC"],
            "DOUTB": ["IW_ADC", "VBUS_ADC"],
            "DOUTC": ["NTC_BOARD", "NTC_BOARD_AUX"],
            "DOUTD": ["UNUSED_CH7", "UNUSED_CH8"],
        }
        if d.get("data_lanes") != lanes_expected:
            e.append("AD7606C lane/channel order not aligned to FIG 106")
        # Current signal envelope is 2.55 +/- 2.0 V in the stated rated peak.
        if not (0 < (5.1 / 2 - 20 * 0.1) and (5.1 / 2 + 20 * 0.1) < 5.0):
            e.append("phase current amp nominal output overflows 0-5V")
        return e
    return SimpleNamespace(**locals())

def validity_api():
    """Physical-pin and static-corner contract for the ADC supply inhibit.

    This is not an analog transient model or a guarantee of gate-off timing.
    TPS3890 SLVSD65A: 1.15 V +/-1%, hysteresis <=0.825%, ISENSE <=100 nA.
    TPS62901 SLVSFS7A: external FB 0.6 V +/-0.9%, IFB <=70 nA.
    R93..R95: 0.05% initial, 10 ppm/C *100 C, 0.1% drift allocation.
    R92: 0.1% /25ppm primary or 0.1% /10ppm alternate, common0.702% bound
    covering reviewed individual qualification-test drift. This is not a lifetime guarantee.
    """
    from pathlib import Path
    import argparse
    import itertools
    import json
    import xml.etree.ElementTree as ET


    def verify(path):
        root = ET.parse(path).getroot()
        comps = {c.attrib['ref']: c for c in root.findall('./components/comp')}
        pins = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                for net in root.findall('./nets/net') for n in net.findall('node')}
        errors = []
        for ref, value in {'U13': 'TPS62901RPJR', 'U25': 'TPS389001DSER',
                           'R92': '3.24k', 'R93': '1k', 'R94': '75k',
                           'R95': '10k', 'C94': '100nF', 'C133': '10nF'}.items():
            if ref not in comps or comps[ref].findtext('value') != value:
                errors.append(f'{ref}: ADC validity requires {value}')

        def same(*terms):
            nets = [pins.get((r, str(p))) for r, p in terms]
            if None in nets or len(set(nets)) != 1 or any(n and n.startswith('unconnected-') for n in nets):
                errors.append(f'ADC validity connection {terms}: {nets}')

        def rail(ref, pin, name):
            if pins.get((ref, str(pin))) != '/' + name:
                errors.append(f'{ref}.{pin}: ADC validity requires /{name}')

        for ref in ('R92', 'R93', 'R94', 'R95'):
            fields = {f.attrib['name']: f.text for f in comps.get(ref, ET.Element('comp')).findall('./fields/field')}
            tolerance, tcr = ('0.1%', '25ppm/C') if ref == 'R92' else ('0.05%', '10ppm/C')
            if fields.get('Tolerance') != tolerance or fields.get('TCR') != tcr:
                errors.append(f'{ref}: controlled {tolerance}, {tcr} resistor specification missing')
        # Actual TPS3890 DSE package numbering; not TPS3808-compatible.
        rail('U25', 4, 'VIO_3V3')
        rail('U25', 2, 'GND')
        rail('U25', 3, 'VIO_3V3')
        same(('U25', 6), ('U24', 1), ('U26', 1))
        same(('U25', 4), ('C91', 1))
        same(('U25', 2), ('C91', 2), ('C94', 2), ('R93', 2))
        same(('U25', 1), ('R92', 2), ('R93', 1))
        same(('U25', 5), ('C94', 1))
        rail('R92', 1, 'VA_5V')
        # External FB, forced PWM, 2.5 MHz; external 10nF soft-start capacitor.
        for pin, name in ((6, 'VDRV_12V'), (5, 'VDRV_12V'), (7, 'VDRV_12V'),
                          (4, 'GND'), (1, 'PWR_GOOD'), (3, 'VA_5V')):
            rail('U13', pin, name)
        same(('U13', 2), ('L2', 1))
        same(('U13', 9), ('R94', 2), ('R95', 1))
        rail('R94', 1, 'VA_5V')
        rail('R95', 2, 'GND')
        same(('U13', 8), ('C133', 1))
        rail('C133', 2, 'GND')
        if pins.get(('U13', '8')) in ('/GND', '/VA_5V', '/VDRV_12V'):
            errors.append('U13.SS/TR requires a dedicated soft-start capacitor node')
        same(('U26', 7), ('U23', 6))
        same(('U23', 4), ('U20', 6))
        same(('U20', 5), ('U11', 6))

        tol = .0025  # R93..95 initial + temperature + allocated application drift
        r92_tol = .00702  # conservative common envelope; see sourcing qualification notes
        def bounds(ref, top, bottom, accuracy, leakage, top_tol=tol):
            values = [v * (1 + a / b) + current * a
                      for v, a, b, current in itertools.product(
                          (ref*(1-accuracy), ref*(1+accuracy)),
                          (top*(1-top_tol), top*(1+top_tol)),
                          (bottom*(1-tol), bottom*(1+tol)), (-leakage, leakage))]
            return min(values), max(values)
        fall = bounds(1.15, 3240, 1000, .01, 100e-9, r92_tol)
        recovery_max = fall[1] * 1.00825
        supply = bounds(.6, 75000, 10000, .009, 70e-9)
        if fall[0] <= 4.75 or recovery_max >= supply[0] - .01 or supply[1] + .01 >= 5.25:
            errors.append('static ADC inhibit/recovery margin insufficient')
        numeric = {'resistor_fractional_bounds': {'R92': r92_tol, 'R93_R94_R95': tol},
                   'drift_scope': 'Prototype budget based on separate qualification tests/allocations; combined aging/environment and dynamic shutdown remain unqualified.',
                   'falling_threshold_V': fall, 'rising_threshold_max_V': recovery_max,
                   'regulated_static_V': supply, 'normal_negative_ripple_budget_V': .01,
                   'adc_min_V': 4.75, 'adc_max_V': 5.25,
                   'static_shutdown_headroom_V': fall[0] - 4.75,
                   'transient_gate_off_qualified': False,
                   'delay_note': '18us TPS3890 typical at 5% overdrive is NOT a guaranteed maximum; rapid droop and full-chain delay remain open.'}
        return errors, numeric
    return SimpleNamespace(**locals())

def ad7606c_api(project):
    """Independent native XML acceptance for AD7606C-16 and retained servo circuits.

    Use a fresh KiCad kicadxml export, not a fabricated or hand-edited netlist.
    Digital/physical connectivity only; not an analog, RTL, PCB or bench test.
    """
    from pathlib import Path
    from collections import Counter
    import argparse
    import copy
    import csv
    import hashlib
    import json
    import re
    import sys
    import xml.etree.ElementTree as ET

    HERE = project.schematic.parent
    ROOT = project.root
    from pcbtools.kicad import assert_balanced, extract_forms, head_string, property_value, strip_form
    from pcbtools.schematic import check_power


    def load_xml(path):
        root=ET.parse(path).getroot()
        components={c.get("ref"):c for c in root.findall("components/comp")}
        pins={}
        for net in root.findall("nets/net"):
            for node in net.findall("node"):
                key=(node.get("ref"),node.get("pin"))
                assert key not in pins, f"Physical pin listed twice: {key}"
                pins[key]=net.get("name")
        return components,pins


    def electrical_errors(components,pins):
        errors=[]

        def rail(ref,pin,net):
            if pins.get((ref,str(pin)))!="/"+net:
                errors.append(f"{ref}.{pin}: expected /{net}, got {pins.get((ref,str(pin)))}")

        def same(*nodes):
            nets=[pins.get((r,str(p))) for r,p in nodes]
            if None in nets or len(set(nets))!=1 or any(n.startswith("unconnected-") for n in nets if n):
                errors.append(f"Required physical connection {nodes}: {nets}")

        if len(components)<160 or len(pins)<400:
            errors.append("Incomplete native design export")
        if components.get("U6") is None or components["U6"].findtext("value")!="AD7606C-16BSTZ":
            errors.append("U6 must be exact AD7606C-16BSTZ")
        if {p for r,p in pins if r=="U6"}!={str(n) for n in range(1,65)}:
            errors.append("U6 must export all 64 distinct physical pins")
        for n in [1,23,37,38,48,3,4,5,6,7,10,34]:
            rail("U6",n,"VA_5V")
        for n in [2,26,35,40,41,47,43,46,8,16,17,18,30,31,32,33,50,52,54,56,58,60,61,62,63,64]:
            rail("U6",n,"GND")
        for n in [19,20,21,22]:
            net=pins.get(("U6",str(n)),"")
            if not net.startswith("unconnected-"):
                errors.append(f"Unused DOUT pin{n} must be unconnected in four-lane design")
        # Every ADC digital signal passes through fixed-direction dual-rail isolation.
        for adc,ref,pin in [(9,"U27",13),(11,"U27",12),(13,"U28",12),(29,"U29",13),(14,"U29",11),(15,"U29",10)]:
            same(("U6",adc),(ref,pin))
        for j,ref,pin in [(11,"U27",2),(14,"U27",3),(12,"U28",2),(13,"U28",3),(31,"U29",2),(17,"U29",4),(18,"U29",5)]:
            same(("J1",j),(ref,pin))
        same(("U28",13),("R104",1));same(("R104",2),("U6",12))
        for adc,ref,bpin,apin,res,j in [(24,"U27",11,4,"R100",15),(25,"U27",10,5,"R101",16),(27,"U28",11,4,"R102",29),(28,"U28",10,5,"R103",30)]:
            same(("U6",adc),(ref,bpin));same((ref,apin),(res,2));same((res,1),("J1",j))
        for i,ref in enumerate(["U27","U28","U29"]):
            rail(ref,1,"VIO_3V3");rail(ref,14,"VA_5V");rail(ref,7,"GND");rail(ref,8,"PWR_READY")
            if components.get(ref) is None or components[ref].findtext("value")!="TXU0204PWR":
                errors.append(f"{ref}: fixed-direction TXU0204PWR isolation required")
            if {p for r,p in pins if r==ref}!={str(n) for n in range(1,15)}:
                errors.append(f"{ref}: all 14 physical pins required")
            for n in [6,9]:
                if not pins.get((ref,str(n)),"").startswith("unconnected-"):
                    errors.append(f"{ref}.{n}: actual PW package NC must stay NC")
            for cap,net in [(f"C{101+i*2}","VIO_3V3"),(f"C{102+i*2}","VA_5V")]:
                rail(cap,1,net);rail(cap,2,"GND")
                if components.get(cap) is None or components[cap].findtext("value")!="100nF":
                    errors.append(f"{cap}: 100nF translator bypass required")
        rail("U29",3,"GND")
        if not pins.get(("U29","12"),"").startswith("unconnected-"):
            errors.append("Unused U29 B2Y must stay unconnected")
        for n in range(100,112):
            ref=f"R{n}";val="47R" if n<105 else "10k"
            if components.get(ref) is None or components[ref].findtext("value")!=val:
                errors.append(f"{ref}: expected fitted {val}")
            elif components[ref].find("property[@name='dnp']") is not None:
                errors.append(f"{ref}: required resistor must be fitted")
        for n in [11,12,13,14,15,16,17,18,29,30,31]:
            if pins.get(("J1",str(n))) is None:
                errors.append(f"Active J10 signal missing: {n}")
        # ADC-side bias while OE low, plus host-side pulls to keep RESET/CS high
        # when OE rises with an unconfigured FPGA. Dynamic sequencing is a bench gate.
        for ref,pin,up in [("R105",9,False),("R106",11,True),("R108",13,True),("R109",29,False)]:
            same((ref,1 if up else 2),("U6",pin))
            rail(ref,2 if up else 1,"VA_5V" if up else "GND")
        same(("R107",2),("R104",1));rail("R107",1,"GND")
        for ref,j in [("R110",14),("R111",13)]:
            same((ref,1),("J1",j));rail(ref,2,"VIO_3V3")
        for ref in ["U6","U27","U28","U29",*[f"C{n}" for n in range(60,69)],*[f"C{n}" for n in range(100,107)]]:
            if components.get(ref) is not None and components[ref].find("property[@name='dnp']") is not None:
                errors.append(f"{ref}: functional ADC/interface component must be fitted")
        for pin,other in [(49,("R40",2)),(51,("R41",2)),(53,("R42",2)),(55,("R13",2)),(57,("R70",2)),(59,("R71",2))]:
            # VBUS's exact divider reference is checked below against the named net.
            if pin!=55:
                same(("U6",pin),other)
        rail("U6",55,"VBUS_ADC")
        same(("U6",44),("U6",45),("C60",1))
        same(("U6",42),("C61",1));same(("U6",36),("C62",1));same(("U6",39),("C63",1))
        if pins.get(("U6","36"))==pins.get(("U6","39")):
            errors.append("Analog and digital REGCAP outputs must stay separate")
        expected={"C60":"10uF","C61":"100nF","C62":"1uF","C63":"1uF",
                  "C64":"100nF","C65":"100nF","C66":"100nF","C67":"100nF","C68":"100nF","C100":"10uF"}
        for ref,val in expected.items():
            if ref not in components or components[ref].findtext("value")!=val:
                errors.append(f"{ref}: expected {val}")
            rail(ref,2,"GND")
        for ref in ["C64","C65","C66","C67","C100"]:
            rail(ref,1,"VA_5V")
        rail("C68",1,"VA_5V")
        return errors


    def inherited_errors(old,new):
        oldc,oldp=old;newc,newp=new
        errors=[]
        changed={"U6",*(f"C{n}" for n in range(60,69))}
        # This exact, user-authorized AD7606C ECO removes only the onboard bank.
        # Its replacement interface and absence are independently checked by dc_link.
        dc_profile = project.parameters.get("dc_link_profile")
        if dc_profile:
            profile = json.loads((project.root / dc_profile).read_text(encoding="utf-8"))
            if profile.get("mode") == "EXTERNAL_CAPACITOR_BLEEDER":
                from .dc_link import EXTERNAL_REMOVED_REFS
                changed.update(EXTERNAL_REMOVED_REFS)
        retained=set(oldc)-changed
        for ref in sorted(retained):
            if ref not in newc:
                errors.append(f"Retained component removed: {ref}")
                continue
            for field in ["value","footprint"]:
                if project.parameters.get("component_ecos", {}).get(ref, {}).get(field, oldc[ref].findtext(field)) != newc[ref].findtext(field):
                    errors.append(f"Unexpected retained {field} change: {ref}")
            a={f.get("name"):f.text for f in oldc[ref].findall("fields/field")}
            b={f.get("name"):f.text for f in newc[ref].findall("fields/field")}
            for field in ["Manufacturer","MPN","LCSC"]:
                if project.parameters.get("component_ecos", {}).get(ref, {}).get(field, a.get(field) or "") != (b.get(field) or ""):
                    errors.append(f"Unexpected retained {field} change: {ref}")
        projected={p for p in oldp if p[0] in retained and p not in {("J1","29"),("J1","30"),("J1","31")}}
        missing=projected-set(newp)
        if missing:
            errors.append(f"Retained physical pins missing: {sorted(missing)}")
        # Compare electrical equivalence classes, independent of renamed sheet paths
        # and automatic net names. Every retained physical pin must keep its peers.
        for node in sorted(projected-set(missing)):
            a={p for p in projected if oldp[p]==oldp[node]}
            b={p for p in projected if newp.get(p)==newp[node]}
            if a!=b:
                errors.append(f"Retained connectivity changed at {node}: missing={sorted(a-b)} extra={sorted(b-a)}")
        return errors




    def source_errors(root=ROOT):
        errors=[]
        manifest=json.loads((HERE/"source_manifest.json").read_text(encoding="utf-8"))
        if set(manifest["text_sha256_lf"]) != set(manifest["files"]):
            return ["Original source hash coverage differs"]
        for name,digest in manifest["text_sha256_lf"].items():
            data=(root/name).read_text(encoding="utf-8").encode("utf-8")
            if hashlib.sha256(data).hexdigest()!=digest:
                errors.append(f"Original file changed: {name}")
        return errors


    def source_checks():
        errors=source_errors()
        top=(HERE/"ax7010_servo_ad7606c.kicad_sch").read_text(encoding="utf-8")
        declared={property_value(f.text,"Sheetfile"):{head_string(p.text,"pin") for p in extract_forms(f.text,"pin")}
                  for f in extract_forms(top,"sheet")}
        references=[]
        definitions=[]
        for path in sorted(HERE.glob("*.kicad_sch")):
            raw=path.read_text(encoding="utf-8");assert_balanced(raw)
            lib=extract_forms(raw,"lib_symbols")[0].text
            defs={head_string(f.text,"symbol"):f.text for f in extract_forms(lib,"symbol")}
            authored=strip_form(raw,"lib_symbols")
            for f in extract_forms(authored,"symbol"):
                if "(lib_id " not in f.text:
                    continue
                ref=property_value(f.text,"Reference")
                if ref:
                    references.append((ref,re.search(r'\(unit (\d+)\)',f.text)[1]))
                alias=extract_forms(f.text,"lib_name")
                key=head_string(alias[0].text,"lib_name") if alias else re.search(r'\(lib_id "([^"]+)"',f.text)[1]
                if key not in defs:
                    errors.append(f"Missing embedded symbol {key} in {path.name}")
            if path.name in declared:
                ports={head_string(f.text,"hierarchical_label") for f in extract_forms(authored,"hierarchical_label")}
                if ports!=declared[path.name]:
                    errors.append(f"Hierarchy mismatch: {path.name}")
                errors.extend(check_power(path))
            for key,value in defs.items():
                if key.endswith(":AD7606C_16_SERIAL"):
                    definitions.append(value)
        if any(n>1 for n in Counter(references).values()):
            errors.append("Duplicate reference/unit or power reference")
        if {u for r,u in references if r=="U6"}!={"1","2","3","4","5"}:
            errors.append("U6 must contain all five drawn units")
        # Independently assert package pin types at risky mode-dependent terminals.
        for definition in definitions:
            p={int(head_string(extract_forms(f.text,"number")[0].text,"number")):f.text.split()[1]
               for f in extract_forms(definition,"pin")}
            if len(p)!=64 or set(p)!=set(range(1,65)):
                errors.append("AD7606C symbol must contain all physical pins once")
            for n in [14,15,19,20,21,22,24,25,27,28]:
                if p[n]!="output":
                    errors.append(f"Serial output pin {n} must stay output")
            for n in [16,17,18,29,30,31,32,33]:
                if p[n]!="input":
                    errors.append(f"Serial input/GND strap pin {n} must stay input")
        return errors


    def profile_errors(profile,xdc):
        errors=[]
        cfg={"0x02":"0x10","0x03":"0x55","0x04":"0x65","0x05":"0x66","0x06":"0x66","0x07":"0x0F","0x08":"0x00"}
        for addr,value in cfg.items():
            if profile.get("configuration",{}).get(addr,{}).get("value")!=value:
                errors.append(f"ADC register configuration mismatch: {addr}")
        if profile.get("timing",{}).get("frame_sclk_edges")!=32 or profile["timing"].get("serial_lanes")!=4:
            errors.append("Four-lane complete frame requires 32 SCLK cycles")
        if profile.get("data_lanes")!={"DOUTA":["IU_ADC","IV_ADC"],"DOUTB":["IW_ADC","VBUS_ADC"],"DOUTC":["NTC_BOARD","NTC_BOARD_AUX"],"DOUTD":["UNUSED_CH7","UNUSED_CH8"]}:
            errors.append("Four-lane channel ordering mismatch")
        if profile.get("startup",{}).get("development_first_reset_wait_ms",0)<=2000:
            errors.append("First-reset setup must respect Rev.A Table3 footnote3")
        expected={"ADC_CONVST":(11,"Y14"),"ADC_SCLK":(12,"W14"),"ADC_CS_N":(13,"P18"),"ADC_RESET":(14,"N17"),
                  "ADC_DOUTA":(15,"U15"),"ADC_DOUTB":(16,"U14"),"ADC_BUSY":(17,"P16"),"ADC_FRSTDATA":(18,"P15"),
                  "ADC_DOUTC":(29,"U12"),"ADC_DOUTD":(30,"T12"),"ADC_SDI":(31,"T10")}
        actual={e["signal"]:(e["header_pin"],e["fpga_pin"]) for e in profile.get("external_pins",[])}
        if actual!=expected:
            errors.append("J10 physical connector/FPGA profile differs from independently reviewed map")
        timing=profile.get("timing",{})
        if timing.get("initial_sclk_hz")!=5000000 or timing.get("initial_frame_time_us")!=6.4:
            errors.append("Bring-up profile must start at 5MHz / 6.4us frame until timing qualification")
        # Fitted path: TXU0204 A=3.3 V / B=5 V, not the bare ADC fSCLK limit.
        # TI SCES936A 7.11 full-temperature bounds; ADI Rev.A Table 5.
        expected_board_timing = {
            "implementation_status": "NOT_RUN",
            "vcca_condition_v": [3.0, 3.6], "vccb_condition_v": [4.5, 5.5],
            "translator_temperature_c": [-40, 125],
            "sclk_translator_max_ns": 9.0, "adc_data_access_max_ns": 15.7,
            "dout_translator_max_ns": 10.0, "raw_round_trip_max_ns": 34.7,
            "translator_test_load_pf": 5.0, "translator_test_load_ohm": 10000,
            "adc_data_launch_edge": "SCLK_RISING",
            "fpga_reference_capture_edge": "SCLK_FALLING",
            "reference_clock_duty_ratio": 0.5,
            "initial_raw_half_cycle_residual_ns": 65.3,
            "target_raw_half_cycle_residual_ns": -9.7,
            "opposite_edge_20mhz_qualified": False,
            "board_flight_load_fpga_budget_ns": None,
            "load_edge_duty_hold_sta_status": "OPEN",
        }
        board_timing = timing.get("board_timing")
        if not isinstance(board_timing, dict) or any(
                key not in board_timing or board_timing[key] != value
                for key, value in expected_board_timing.items()):
            errors.append("ADC board timing: fitted translator bounds and unqualified capture contract must be retained until RTL/STA evidence is reviewed")
        if timing.get("conversion_time_max_us") != 0.65:
            errors.append("AD7606C no-oversampling conversion maximum is 0.65us, not the typical value")
        if timing.get("analog_3db_bandwidth_khz") != 150 or timing.get("analog_phase_delay_typ_us") != 1.7:
            errors.append("AD7606C 0-5V high-BW uses typical 150kHz / 1.7us, not a worst-case loop guarantee")
        active="\n".join(line for line in xdc.splitlines() if not line.lstrip().startswith("#"))
        pairs=re.findall(r"set_property PACKAGE_PIN (\w+) \[get_ports (\w+)\]",active)
        if len(pairs)!=len({pad for pad,sig in pairs}) or len(pairs)!=len({sig for pad,sig in pairs}):
            errors.append("Duplicate active FPGA pad or signal in XDC")
        ports={sig:pad for pad,sig in pairs}
        for entry in profile.get("external_pins",[]):
            sig=entry["signal"]
            if ports.get(sig)!=entry["fpga_pin"]:
                errors.append(f"Profile/XDC pin mismatch: {sig}")
            if f"set_property IOSTANDARD LVCMOS33 [get_ports {sig}]" not in active:
                errors.append(f"XDC I/O standard missing: {sig}")
        return errors






    def self_tests(components,pins,old):
        cases={"OS0 low":(("U6","3"),"/GND"),"DOUTC grounded":(("U6","27"),"/GND"),
               "REGCAP outputs shorted":(("U6","39"),pins[("U6","36")]),
               "REFCAPB disconnected":(("U6","45"),"broken-reference"),
               "SDI wrong J10 pin":(("J1","31"),"unconnected-J1-P31"),
               "VDRIVE independent of AVCC":(("U6","23"),"/VIO_3V3"),
               "Translator OE bypasses supervisor":(("U27","8"),"/VIO_3V3"),
               "OCP pull-up supply missing":(("R54","1"),"floating-OCP-rail")}
        for name,(node,net) in cases.items():
            broken=dict(pins);broken[node]=net
            if not electrical_errors(components,broken)+inherited_errors(old,(components,broken)):
                raise AssertionError(f"Fault injection was not rejected: {name}")
        extra=0
        for ref in ["R106","R108","R110","R111"]:
            bad=copy.deepcopy(components);bad[ref].find("value").text="0R"
            if not electrical_errors(bad,pins):
                raise AssertionError(f"Zero-ohm startup bias was not rejected: {ref}")
            bad=copy.deepcopy(components);ET.SubElement(bad[ref],"property",{"name":"dnp"})
            if not electrical_errors(bad,pins):
                raise AssertionError(f"DNP startup bias was not rejected: {ref}")
            extra+=2
        profile=json.loads((HERE/"adc_profile.json").read_text(encoding="utf-8"));xdc=(HERE/"ax7010_servo_ad7606c.xdc").read_text(encoding="utf-8")
        bad=copy.deepcopy(profile);bad["configuration"]["0x02"]["value"]="0x00"
        if not profile_errors(bad,xdc):
            raise AssertionError("Incorrect lane configuration was not rejected")
        badxdc=xdc.replace("PACKAGE_PIN U12 [get_ports ADC_DOUTC]","PACKAGE_PIN T10 [get_ports ADC_DOUTC]")
        if not profile_errors(profile,badxdc):
            raise AssertionError("Conflicting FPGA package assignment was not rejected")
        extra+=2
        total=len(cases)+extra
        print(f"FAULT INJECTION PASSED: {total} wiring, fitted-value and profile errors rejected")
        return total
    return SimpleNamespace(**locals())
