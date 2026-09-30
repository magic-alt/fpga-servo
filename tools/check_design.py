from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
errors = []

schematic_paths = [
    HW / "ax7010_servo_reva.sch",
    HW / "power_input.sch",
    HW / "aux_power.sch",
    HW / "gate_inverter.sch",
    HW / "current_adc.sch",
    HW / "encoder.sch",
    HW / "ax7010_interface.sch",
]

required = [
    *schematic_paths,
    HW / "ax7010_servo_reva.lib",
    HW / "ax7010_servo_reva-cache.lib",
    HW / "ax7010_servo_reva.kicad_pcb",
    HW / "bom.csv",
    ROOT / "fpga/ax7010_servo_reva.xdc",
]
for p in required:
    if not p.exists() or p.stat().st_size == 0:
        errors.append(f"missing/empty: {p.relative_to(ROOT)}")

# Legacy KiCad project/library integrity.
if (HW / "ax7010_servo_reva.lib").exists() and (HW / "ax7010_servo_reva-cache.lib").exists():
    project_lib = (HW / "ax7010_servo_reva.lib").read_text(errors="ignore")
    cache_lib = (HW / "ax7010_servo_reva-cache.lib").read_text(errors="ignore")
    if project_lib != cache_lib:
        errors.append("ax7010_servo_reva.lib and ax7010_servo_reva-cache.lib are not synchronized")

schematic_text = ""
valid_hlabel_types = {"Input", "Output", "BiDi", "TriState", "UnSpc"}
hlabel_re = re.compile(
    r"^Text HLabel\s+\d+\s+\d+\s+\d+\s+\d+\s+(\S+)\s+~\s+\d+\s*$"
)

for p in schematic_paths:
    if not p.exists():
        continue
    txt = p.read_text(errors="ignore")
    schematic_text += "\n" + txt

    if "$EndSCHEMATC" not in txt:
        errors.append(f"legacy schematic missing $EndSCHEMATC: {p.relative_to(ROOT)}")

    # Project drafting standard: all schematic pages use A4 landscape.
    if "$Descr A4 11693 8268" not in txt:
        errors.append(
            f"all schematic pages must use A4 landscape: {p.relative_to(ROOT)}"
        )

    # KiCad legacy readers are line-oriented and some versions reject blank
    # physical lines as top-level unknown tokens.
    blank_lines = [
        lineno for lineno, line in enumerate(txt.splitlines(), start=1)
        if not line.strip()
    ]
    if blank_lines:
        errors.append(
            f"legacy schematic contains blank physical lines: "
            f"{p.relative_to(ROOT)}:{blank_lines[:8]}"
        )

    # Component U records must carry a conventional 8-hex legacy timestamp.
    # Sheet UUID records also begin with "U " but have a different grammar,
    # so only validate U records while inside a $Comp/$EndComp block.
    in_comp = False
    for lineno, line in enumerate(txt.splitlines(), start=1):
        if line == "$Comp":
            in_comp = True
            continue
        if line == "$EndComp":
            in_comp = False
            continue
        if in_comp and line.startswith("U "):
            if not re.fullmatch(r"U\s+\d+\s+\d+\s+[0-9A-Fa-f]{8}", line):
                errors.append(
                    f"invalid component legacy timestamp record: "
                    f"{p.relative_to(ROOT)}:{lineno}: {line}"
                )

    for lineno, line in enumerate(txt.splitlines(), start=1):
        if line.startswith("Text HLabel "):
            match = hlabel_re.match(line)
            if not match:
                errors.append(
                    f"malformed legacy Text HLabel: {p.relative_to(ROOT)}:{lineno}: {line}"
                )
                continue
            label_type = match.group(1)
            if label_type not in valid_hlabel_types:
                errors.append(
                    f"invalid legacy HLabel type {label_type!r}: "
                    f"{p.relative_to(ROOT)}:{lineno}"
                )

root_sch = (HW / "ax7010_servo_reva.sch").read_text(errors="ignore")
for child in [
    "power_input.sch",
    "aux_power.sch",
    "gate_inverter.sch",
    "current_adc.sch",
    "encoder.sch",
    "ax7010_interface.sch",
]:
    if child not in root_sch:
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

# Known stale/incorrect constructs that must not regress.
for token in [
    "Text HLabel 600 1500 0    50   I ~ 0",
    "Text HLabel 14900 2250 2    50   O ~ 0",
    "Package_DirectFET:DirectFET_L4",
]:
    if token in schematic_text:
        errors.append(f"obsolete schematic construct remains: {token}")

pcb = (HW / "ax7010_servo_reva.kicad_pcb").read_text(errors="ignore")
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

xdc = (ROOT / "fpga/ax7010_servo_reva.xdc").read_text(errors="ignore")
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

with (HW / "bom.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
joined = "\n".join(str(r) for r in rows)
for part in [
    "FD6288T",
    "BSC040N10NS5",
    "INA241A2",
    "ADS8588S",
    "AM26LV32E",
]:
    if part not in joined:
        errors.append(f"BOM missing part: {part}")

if errors:
    print("DESIGN CHECK FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("DESIGN CHECK PASSED")
