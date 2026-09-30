from pathlib import Path
import re
import sys

from kicad_native import assert_balanced, extract_forms, property_value, strip_form

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
TOP = HW / "ax7010_servo_reva.kicad_sch"
CHILD_NAMES = [
    "power_input.kicad_sch",
    "aux_power.kicad_sch",
    "gate_inverter.kicad_sch",
    "ax7010_interface.kicad_sch",
    "current_adc.kicad_sch",
    "encoder.kicad_sch",
]
SCHEMATICS = [TOP, *(HW / name for name in CHILD_NAMES)]
errors: list[str] = []

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
    if not re.match(r"^\\(kicad_sch\\s+\\(version\\s+\\d+\\)", text):
        errors.append(f"{path.name}: invalid KiCad native schematic header")
    try:
        assert_balanced(text)
    except ValueError as exc:
        errors.append(f"{path.name}: {exc}")
    if '(paper "A4")' not in text:
        errors.append(f"{path.name}: paper must be A4")
    if not extract_forms(text, "lib_symbols"):
        errors.append(f"{path.name}: embedded lib_symbols section is missing")

    authored = strip_form(text, "lib_symbols")
    if extract_forms(authored, "global_label"):
        errors.append(f"{path.name}: Global Labels are forbidden")
    if re.search(r'\\.sch"', authored):
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

if errors:
    print("NATIVE SCHEMATIC CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("NATIVE SCHEMATIC CHECK PASSED")
