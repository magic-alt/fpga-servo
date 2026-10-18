"""Grouped rule families; explicit contexts and no import-time checks."""
from types import SimpleNamespace

def check_design(project, schematic_only=False):
    from pathlib import Path
    import csv, re
    from pcbtools.kicad import extract_forms, property_value, strip_form
    from pcbtools.rules.power_layout import vendor_api, kelvin_api
    check_vendor_lands = vendor_api().check
    check_internal_pad_rules = vendor_api().check_internal_pad_rules
    check_shunt_contract = kelvin_api().check_shunt_contract
    ROOT = project.root
    HW = ROOT / "hardware" / "ads8588s_servo"
    errors: list[str] = []

    schematic_paths = [
        HW / "ax7010_servo_reva.kicad_sch",
        HW / "power_input.kicad_sch",
        HW / "aux_power.kicad_sch",
        HW / "gate_inverter.kicad_sch",
        HW / "current_adc.kicad_sch",
        HW / "encoder.kicad_sch",
        HW / "ocp_latch.kicad_sch",
        HW / "ax7010_interface.kicad_sch",
    ]

    required = [
        *schematic_paths,
        HW / "ax7010_servo_reva.kicad_sym",
        HW / "ax7010_servo_reva.kicad_pro",
        HW / "ax7010_servo_reva.kicad_pcb",
        HW / "bom.csv",
        ROOT / "hardware/ads8588s_servo/ax7010_servo_reva.xdc",
    ]
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing/empty: {path.relative_to(ROOT)}")

    for path in [*HW.glob("*.sch"), *HW.glob("*.lib")]:
        errors.append(f"legacy KiCad source must not be tracked: {path.relative_to(ROOT)}")
    table = HW / "sym-lib-table"
    if not table.exists() or '${KIPRJMOD}/ax7010_servo_reva.kicad_sym' not in table.read_text(encoding="utf-8"):
        errors.append("portable project symbol table missing or invalid")

    schematic_text = ""
    for path in schematic_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        schematic_text += "\n" + text
        if '(paper "A4")' not in text:
            errors.append(f"all schematic pages must use A4: {path.relative_to(ROOT)}")
        authored = strip_form(text, "lib_symbols")
        if extract_forms(authored, "global_label"):
            errors.append(f"Global Label found: {path.relative_to(ROOT)}")

    if schematic_paths[0].exists():
        root_text = strip_form(
            schematic_paths[0].read_text(encoding="utf-8", errors="strict"),
            "lib_symbols",
        )
        children = {
            property_value(sheet.text, "Sheetfile")
            for sheet in extract_forms(root_text, "sheet")
        }
        for child in [
            "power_input.kicad_sch",
            "aux_power.kicad_sch",
            "gate_inverter.kicad_sch",
            "current_adc.kicad_sch",
            "encoder.kicad_sch",
            "ocp_latch.kicad_sch",
            "ax7010_interface.kicad_sch",
        ]:
            if child not in children:
                errors.append(f"top schematic missing hierarchical child: {child}")

    for token in [
        "DRV8300DPWR",
        "ADS8588S",
        "INA240A1",
        "AM26LV32E",
        "BSC040N10NS5",
        "LM5164",
        "TPS62901",
        "TPS389001",
        "LM393LV",
        "LM74502",
        "SN74LVC1G11",
        "SN74LVC2G08",
        "5mR",
    ]:
        if token not in schematic_text:
            errors.append(f"schematic hierarchy missing token: {token}")

    for token in ["U_SH_P", "U_SH_N", "V_SH_P", "V_SH_N", "W_SH_P", "W_SH_N"]:
        if token in schematic_text:
            errors.append(f"obsolete schematic construct remains: {token}")

    # On-board fuse protection is required; J6 is the off-board source interface.
    power_authored = strip_form((HW / "power_input.kicad_sch").read_text(encoding="utf-8"), "lib_symbols")
    fuses = [x.text for x in extract_forms(power_authored, "symbol")
             if property_value(x.text, "Reference") == "F1"]
    if len(fuses) != 1:
        errors.append("exactly one onboard F1 required")
    else:
        fuse = fuses[0]
        if "(on_board yes)" not in fuse or "(in_pos_files no)" in fuse:
            errors.append("F1 must be on board and included in PCB placement")
        for prop, expected in [("MPN", "0456025.ER"),
                               ("Footprint", "fpga-servo:Littelfuse_456_25A_SMD")]:
            if property_value(fuse, prop) != expected:
                errors.append(f"F1: selected onboard {prop} missing")
    gate_authored = strip_form((HW / "gate_inverter.kicad_sch").read_text(encoding="utf-8"), "lib_symbols")
    current_authored = strip_form((HW / "current_adc.kicad_sch").read_text(encoding="utf-8"), "lib_symbols")
    placed = {property_value(x.text, "Reference"): x.text for text in (gate_authored, current_authored)
              for x in extract_forms(text, "symbol")}
    if any(property_value(placed.get("U1", ""), field) != "DRV8300DPWR"
           for field in ("Value", "MPN")):
        errors.append("U1 requires non-inverted DRV8300DPWR; DI variants are prohibited")
    for obsolete in ("D2", "D3", "D4", "U16", "R51", "R52"):
        if obsolete in placed:
            errors.append(f"obsolete phase OCP/bootstrap component remains: {obsolete}")

    interface_authored = strip_form((HW / "ax7010_interface.kicad_sch").read_text(encoding="utf-8"), "lib_symbols")
    j1 = next(x.text for x in extract_forms(interface_authored, "symbol")
              if property_value(x.text, "Reference") == "J1")
    if property_value(j1, "Board_Revision") != "ALINX AX7010 2022" or property_value(j1, "Board_Connector") != "J10":
        errors.append("J1 must identify the confirmed AX7010 2022 / J10 interface")
    j6 = next((x.text for x in extract_forms(power_authored, "symbol")
               if property_value(x.text, "Reference") == "J6"), "")
    if "(on_board no)" not in j6 or property_value(j6, "Footprint"):
        errors.append("J6 must remain an external source wiring terminal without a PCB footprint")

    pcb_path = HW / "ax7010_servo_reva.kicad_pcb"
    if not schematic_only and pcb_path.exists():
        pcb = pcb_path.read_text(errors="ignore")
        if pcb.count("(") != pcb.count(")"):
            errors.append("PCB s-expression parentheses are unbalanced")
        # M3-labelled mechanical holes must admit the screw; the old placeholder
        # used a 1 mm drill despite its 5 mm copper pad and M3_HOLE value.
        # 3.2 mm is the clearance drill used by KiCad's M3 mounting-hole library.
        for footprint in extract_forms(pcb, "footprint"):
            if property_value(footprint.text, "Value") != "M3_HOLE":
                continue
            ref = property_value(footprint.text, "Reference")
            pads = extract_forms(footprint.text, "pad")
            if not pads:
                errors.append(f"PCB {ref}: M3 mounting hole has no drilled pad")
            for pad in pads:
                drill = re.search(r"\(drill\s+(\d+(?:\.\d+)?)\s*\)", pad.text)
                if not drill or float(drill.group(1)) < 3.2:
                    errors.append(f"PCB {ref}: M3 clearance hole requires drill >= 3.2 mm")
        if any(property_value(f.text, "Reference") == "J2" for f in extract_forms(pcb, "footprint")):
            errors.append("Unused J2 must not be fitted on PCB")
        for token in [
            "DRV8300DPWR",
            "ADS8588S",
            "BSC040N10NS5",
            "INA240A1",
            "AX7010_PL_A",
        ]:
            if token not in pcb:
                errors.append(f"PCB baseline missing token: {token}")

    xdc_path = ROOT / "hardware/ads8588s_servo/ax7010_servo_reva.xdc"
    if xdc_path.exists():
        xdc = xdc_path.read_text(errors="ignore")
        for port in [
            "PWM_UH",
            "PWM_UL",
            "PWM_VH",
            "PWM_VL",
            "PWM_WH",
            "PWM_WL",
            "ENC_A",
            "ENC_B",
            "ENC_Z",
            "ADC_BUSY",
        ]:
            if port not in xdc:
                errors.append(f"XDC missing port: {port}")

    bom_path = HW / "bom.csv"
    if bom_path.exists():
        with bom_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        expected_refs = set()
        for path in schematic_paths:
            if not path.exists():
                continue
            authored = strip_form(path.read_text(encoding="utf-8"), "lib_symbols")
            for symbol in extract_forms(authored, "symbol"):
                ref = property_value(symbol.text, "Reference")
                if ref and not ref.startswith("#"):
                    expected_refs.add(ref)
        row_by_ref = {row["Ref"]: row for row in rows}
        for path in schematic_paths:
            if not path.exists():
                continue
            authored = strip_form(path.read_text(encoding="utf-8"), "lib_symbols")
            for symbol in extract_forms(authored, "symbol"):
                ref = property_value(symbol.text, "Reference")
                row = row_by_ref.get(ref)
                if row is None:
                    continue
                for column, prop in [("Value / Part", "Value"), ("Package", "Footprint")]:
                    if row[column] != property_value(symbol.text, prop):
                        errors.append(f"BOM {ref}: {column} differs from schematic")
                if row["MPN"] != (property_value(symbol.text, "MPN") or "TBD"):
                    errors.append(f"BOM {ref}: MPN differs from schematic")
                if row["Status / note"].startswith("DNP") != ("(dnp yes)" in symbol.text):
                    errors.append(f"BOM {ref}: assembly option differs from schematic")
        bom_refs = [row["Ref"] for row in rows]
        if set(bom_refs) != expected_refs or len(bom_refs) != len(set(bom_refs)):
            errors.append("BOM references must match the schematic exactly (one row per component)")
        joined = "\n".join(str(row) for row in rows)
        for part in ["DRV8300DPWR", "BSC040N10NS5", "INA240A1", "ADS8588S", "AM26LV32E"]:
            if part not in joined:
                errors.append(f"BOM missing part: {part}")

    if not schematic_only and (HW / "ax7010_servo_reva.kicad_pcb").exists():
        errors.extend(check_vendor_lands((HW / "ax7010_servo_reva.kicad_pcb").read_text(encoding="utf-8")))

    errors.extend(check_shunt_contract(
        (HW / "ax7010_servo_reva.kicad_pcb").read_text(encoding="utf-8"),
        (HW / "ax7010_servo_reva.kicad_sym").read_text(encoding="utf-8"),
        (HW / "gate_inverter.kicad_sch").read_text(encoding="utf-8"),
        (HW / "fpga-servo.pretty/HoYLR2512_Kelvin.kicad_mod").read_text(encoding="utf-8"),
        include_board=not schematic_only,
    ))

    rules_path = HW / "ax7010_servo_reva.kicad_dru"
    if not schematic_only:
        errors.extend(check_internal_pad_rules(rules_path.read_text(encoding="utf-8") if rules_path.exists() else ""))
    return errors

def baseline_api(project):
    """Detect changes to the preserved, unsynchronized PCB; never certify its release.

    The exact known blockers are checked, not ignored. Fresh native netlists enable
    full parity/constraint comparison. Default strict PCB tools remain unchanged.
    """
    from pathlib import Path
    import argparse
    import hashlib
    import json
    import subprocess
    import sys

    from pcbtools.rules.power_layout import vendor_api
    _family_check_vendor_lands = vendor_api()
    vendor_lands = _family_check_vendor_lands.check
    check_internal_pad_rules = _family_check_vendor_lands.check_internal_pad_rules
    from pcbtools.board import parity_api
    _family_check_pcb_parity = parity_api()
    audit_text = _family_check_pcb_parity.audit_text
    from pcbtools.rules.power_layout import constraints_api
    _family_check_pcb_constraints = constraints_api()
    constraints = _family_check_pcb_constraints.check

    ROOT = project.root
    HW = ROOT / "hardware/ads8588s_servo"
    BASELINE = HW / "evidence/pcb_ci_baseline.json"
    CORE_KEYS = {"source_sha256", "design_errors", "vendor_lands", "internal_pad_rules"}


    def canonical(value):
        if isinstance(value, dict):
            return {key: canonical(item) for key, item in value.items()}
        if isinstance(value, list):
            return sorted((canonical(item) for item in value),
                          key=lambda item: json.dumps(item, sort_keys=True))
        return value


    def collect_snapshot(netlist: Path | None = None) -> dict:
        sources = {name: (HW / ("ax7010_servo_reva" + suffix)).read_text(encoding="utf-8")
                   for name, suffix in [("board", ".kicad_pcb"), ("project", ".kicad_pro"),
                                        ("rules", ".kicad_dru")]}
        snapshot = {"source_sha256": {name: hashlib.sha256(text.encode()).hexdigest()
                                      for name, text in sources.items()},
                    "vendor_lands": vendor_lands(sources["board"]),
                    "internal_pad_rules": check_internal_pad_rules(sources["rules"])}
        if netlist is not None:
            text = netlist.read_text(encoding="utf-8")
            parity = audit_text(text, sources["board"], {"H1", "H2", "H3", "H4"})
            if not parity["schematic_components"] or not parity["schematic_nets"]:
                raise ValueError("Empty netlist cannot establish archived PCB regression")
            if set(parity["mechanical_preserved"]) != {"H1", "H2", "H3", "H4"}:
                raise ValueError("Archived board mechanical features changed")
            snapshot["parity"] = parity
            snapshot["constraints"] = constraints(sources["board"], json.loads(sources["project"]), text)
        errors = check_design(project, schematic_only=False)
        if not errors: raise ValueError("Archived PCB unexpectedly has no strict blockers")
        snapshot["design_errors"] = errors
        return canonical(snapshot)


    def compare_snapshot(actual: dict, expected: dict, *, require_parity: bool = False) -> list[str]:
        required = CORE_KEYS | ({"parity", "constraints"} if require_parity or "parity" in actual or "constraints" in actual else set())
        errors = []
        if set(actual) != required:
            errors.append("Missing or unexpected regression checks")
        for key in required:
            if key not in actual or key not in expected or canonical(actual[key]) != canonical(expected[key]):
                errors.append(key + ": differs from preserved PCB baseline; review required")
        return errors
    return SimpleNamespace(**locals())

def native_contract(project):
    from pathlib import Path
    import re
    from pcbtools.kicad import assert_balanced, extract_forms, head_string, property_value, strip_form
    ROOT = project.root
    HW = ROOT / "hardware" / "ads8588s_servo"
    TOP = HW / "ax7010_servo_reva.kicad_sch"
    CHILD_NAMES = [
        "power_input.kicad_sch",
        "aux_power.kicad_sch",
        "gate_inverter.kicad_sch",
        "ax7010_interface.kicad_sch",
        "current_adc.kicad_sch",
        "encoder.kicad_sch",
        "ocp_latch.kicad_sch",
    ]
    SCHEMATICS = [TOP, *(HW / name for name in CHILD_NAMES)]
    SYMBOL_LIB = HW / "ax7010_servo_reva.kicad_sym"
    errors: list[str] = []


    def check_diode_terminals(text: str, source: str) -> None:
        for form in extract_forms(text, "symbol"):
            name = head_string(form.text, "symbol")
            if name not in {"DIODE", "TVS", "ax7010_servo_reva:DIODE", "ax7010_servo_reva:TVS"}:
                continue
            terminals = {}
            for pin in extract_forms(form.text, "pin"):
                numbers = extract_forms(pin.text, "number")
                names = extract_forms(pin.text, "name")
                if numbers and names:
                    terminals[head_string(numbers[0].text, "number")] = head_string(names[0].text, "name")
            if terminals != {"1": "K", "2": "A"}:
                errors.append(f"{source}: {name} must match D_SMA/D_SMC cathode pad1, anode pad2: {terminals}")


    def check_serial_adc(text: str, source: str, required_name: str) -> None:
        matches = [f.text for f in extract_forms(text, "symbol")
                   if head_string(f.text, "symbol") == required_name]
        if len(matches) != 1:
            errors.append(f"{source}: exactly one {required_name} definition required")
            return
        pins = {}
        for pin in extract_forms(matches[0], "pin"):
            numbers = extract_forms(pin.text, "number")
            if numbers:
                pins[head_string(numbers[0].text, "number")] = pin.text.split()[1]
        for number in [*range(16, 23), *range(27, 34)]:
            if pins.get(str(number)) != "input":
                errors.append(f"{source}: serial ADC pin{number} must be modeled as input")
        for number in [14, 15, 24, 25]:
            if pins.get(str(number)) != "output":
                errors.append(f"{source}: ADC status/DOUT pin{number} must remain output")

    if not SYMBOL_LIB.exists() or SYMBOL_LIB.stat().st_size == 0:
        errors.append("missing/empty native symbol library: hardware/ads8588s_servo/ax7010_servo_reva.kicad_sym")
    else:
        symbol_text = SYMBOL_LIB.read_text(encoding="utf-8", errors="strict")
        check_diode_terminals(symbol_text, SYMBOL_LIB.name)
        check_serial_adc(symbol_text, SYMBOL_LIB.name, "ADS8588S_SERIAL")
        if not re.match(r"^\(kicad_symbol_lib\s+\(version\s+\d+\)", symbol_text):
            errors.append("ax7010_servo_reva.kicad_sym: invalid KiCad native symbol library header")
        try:
            assert_balanced(symbol_text)
        except ValueError as exc:
            errors.append(f"ax7010_servo_reva.kicad_sym: {exc}")

    legacy = sorted(HW.glob("*.sch"))
    if legacy:
        errors.append("legacy .sch files remain: " + ", ".join(path.name for path in legacy))
    legacy_libs = sorted(HW.glob("*.lib"))
    if legacy_libs:
        errors.append(
            "legacy symbol libraries remain: " + ", ".join(path.name for path in legacy_libs)
        )

    for path in SCHEMATICS:
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing/empty native schematic: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        check_diode_terminals(text, path.name)
        if path.name == "current_adc.kicad_sch":
            check_serial_adc(text, path.name, "ax7010_servo_reva:ADS8588S_SERIAL")
        if not re.match(r"^\(kicad_sch\s+\(version\s+\d+\)", text):
            errors.append(f"{path.name}: invalid KiCad native schematic header")
        try:
            assert_balanced(text)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
        if '(paper "A4")' not in text:
            errors.append(f"{path.name}: paper must be A4")
        if not extract_forms(text, "lib_symbols"):
            errors.append(f"{path.name}: embedded lib_symbols section is missing")

        root_uuid = re.search(r'\(uuid "([^"]+)"\)', TOP.read_text(encoding="utf-8")).group(1)
        for instance_path in sorted(set(re.findall(r'\(path "(/[^" ]+)"', text))):
            if instance_path != "/" and instance_path.split("/")[1] != root_uuid:
                errors.append(f"{path.name}: instance path root differs from top UUID: {instance_path}")

        authored = strip_form(text, "lib_symbols")
        if extract_forms(authored, "global_label"):
            errors.append(f"{path.name}: Global Labels are forbidden")
        if re.search(r'\.sch"', authored):
            errors.append(f"{path.name}: legacy .sch reference remains in native source")

    if TOP.exists():
        top = strip_form(TOP.read_text(encoding="utf-8"), "lib_symbols")
        sheetfiles = []
        for form in extract_forms(top, "sheet"):
            value = property_value(form.text, "Sheetfile")
            if value:
                sheetfiles.append(value)
        if sorted(sheetfiles) != sorted(CHILD_NAMES):
            errors.append(
                "top schematic native child set mismatch: "
                f"actual={sorted(sheetfiles)} expected={sorted(CHILD_NAMES)}"
            )
    return errors

def selection_contract(path):
    import xml.etree.ElementTree as ET
    from pathlib import Path
    import sys
    r=ET.parse(path).getroot()
    refs={c.attrib['ref']: c for c in r.findall('./components/comp')}
    pins={}
    for net in r.findall('./nets/net'):
        for n in net.findall('node'):
            pins[(n.attrib['ref'],n.attrib['pin'])]=net.attrib['name']
    e=[]
    if 'J2' in refs: e.append('unused J2 is still fitted')
    for i,phase in enumerate('UVW',1):
        ref=f'RSH{i}'
        actual={pin for comp,pin in pins if comp==ref}
        if actual!={'1','2'}:e.append(f'{ref}: SMD two-terminal shunt required, got {actual}')
        for pin,net in [('1',f'/SW_{phase}'),('2',f'/PH_{phase}')]:
            if pins.get((ref,pin))!=net:e.append(f'{ref}.{pin}: expected {net}')
        amp=f'U{i+1}'
        if refs[amp].findtext('value')!='INA240A1DR':e.append(f'{amp}: INA240A1DR required')
    return e
