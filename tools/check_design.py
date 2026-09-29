from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

required = [
    ROOT / "hardware/ax7010_servo_reva.sch",
    ROOT / "hardware/ax7010_servo_reva.kicad_pcb",
    ROOT / "hardware/bom.csv",
    ROOT / "fpga/ax7010_servo_reva.xdc",
]
for p in required:
    if not p.exists() or p.stat().st_size == 0:
        errors.append(f"missing/empty: {p.relative_to(ROOT)}")

pcb = (ROOT / "hardware/ax7010_servo_reva.kicad_pcb").read_text(errors="ignore")
if pcb.count("(") != pcb.count(")"):
    errors.append("PCB s-expression parentheses are unbalanced")
for token in ["FD6288T", "ADS8588S", "BSC040N10NS5", "INA241A2", "AX7010_PL_A", "AX7010_PL_B"]:
    if token not in pcb:
        errors.append(f"PCB missing token: {token}")

sch = (ROOT / "hardware/ax7010_servo_reva.sch").read_text(errors="ignore")
if "$EndSCHEMATC" not in sch:
    errors.append("legacy schematic missing $EndSCHEMATC")
for token in ["FD6288T", "ADS8588S", "INA241A2", "AM26LV32E", "5mR"]:
    if token not in sch:
        errors.append(f"schematic missing token: {token}")

xdc = (ROOT / "fpga/ax7010_servo_reva.xdc").read_text()
for port in ["PWM_UH", "PWM_UL", "PWM_VH", "PWM_VL", "PWM_WH", "PWM_WL", "ENC_A", "ENC_B", "ENC_Z", "ADC_BUSY"]:
    if port not in xdc:
        errors.append(f"XDC missing port: {port}")

with (ROOT / "hardware/bom.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
joined = "\n".join(str(r) for r in rows)
for part in ["FD6288T", "BSC040N10NS5", "INA241A2", "ADS8588S", "AM26LV32E"]:
    if part not in joined:
        errors.append(f"BOM missing part: {part}")

if errors:
    print("DESIGN CHECK FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("DESIGN CHECK PASSED")
