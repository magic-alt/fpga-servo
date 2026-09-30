from pathlib import Path
import csv
import sys

from kicad_native import extract_forms, property_value, strip_form

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
errors: list[str] = []

schematic_paths = [
    HW / "ax7010_servo_reva.kicad_sch",
    HW / "power_input.kicad_sch",
    HW / "aux_power.kicad_sch",
    HW / "gate_inverter.kicad_sch",
    HW / "current_adc.kicad_sch",
    HW / "encoder.kicad_sch",
    HW / "ax7010_interface.kicad_sch",
]

required = [
    *schematic_paths,
    HW / "ax7010_servo_reva.kicad_sym",
    HW / "ax7010_servo_reva.kicad_pro",
    HW / "ax7010_servo_reva.kicad_pcb",
    HW / "bom.csv",
    ROOT / "fpga/ax7010_servo_reva.xdc",
]
for path in required:
    if not path.exists() or path.stat().st_size == 0:
        errors.append(f"missing/empty: {path.relative_to(ROOT)}")

for path in [*HW.glob("*.sch"), *HW.glob("*.lib")]:
    errors.append(f"legacy KiCad source must not be tracked: {path.relative_to(ROOT)}")
if (HW / "sym-lib-table").exists():
    errors.append("hardware/sym-lib-table is local generated state and must not be tracked")

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
        "ax7010_interface.kicad_sch",
    ]:
        if child not in children:
            errors.append(f"top schematic missing hierarchical child: {child}")

for token in [
    "FD6288T",
    "ADS8588S",
    "INA241A2",
    "AM26LV32E",
    "BSC040N10NS5",
    "LM5164",
    "TPS62163",
    "TLV9024",
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

pcb_path = HW / "ax7010_servo_reva.kicad_pcb"
if pcb_path.exists():
    pcb = pcb_path.read_text(errors="ignore")
    if pcb.count("(") != pcb.count(")"):
        errors.append("PCB s-expression parentheses are unbalanced")
    for token in [
        "FD6288T",
        "ADS8588S",
        "BSC040N10NS5",
        "INA241A2",
        "AX7010_PL_A",
        "AX7010_PL_B",
    ]:
        if token not in pcb:
            errors.append(f"PCB baseline missing token: {token}")

xdc_path = ROOT / "fpga/ax7010_servo_reva.xdc"
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
    joined = "\n".join(str(row) for row in rows)
    for part in ["FD6288T", "BSC040N10NS5", "INA241A2", "ADS8588S", "AM26LV32E"]:
        if part not in joined:
            errors.append(f"BOM missing part: {part}")

if errors:
    print("DESIGN CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("DESIGN CHECK PASSED")
