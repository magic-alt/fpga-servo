from collections import defaultdict
from pathlib import Path
import re
import sys

from kicad_native import (
    extract_forms,
    head_string,
    parse_at,
    parse_xy,
    property_value,
    strip_form,
)

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
TOP = HW / "ax7010_servo_reva.kicad_sch"
CHILDREN = [
    HW / "power_input.kicad_sch",
    HW / "aux_power.kicad_sch",
    HW / "gate_inverter.kicad_sch",
    HW / "current_adc.kicad_sch",
    HW / "encoder.kicad_sch",
    HW / "ocp_latch.kicad_sch",
    HW / "ax7010_interface.kicad_sch",
]
errors: list[str] = []


def authored(path: Path) -> str:
    return strip_form(
        path.read_text(encoding="utf-8", errors="strict"), "lib_symbols"
    )


def on_segment(point, a, b, tol=1e-6) -> bool:
    x, y = point
    x1, y1 = a
    x2, y2 = b
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > tol:
        return False
    return (
        min(x1, x2) - tol <= x <= max(x1, x2) + tol
        and min(y1, y2) - tol <= y <= max(y1, y2) + tol
    )


def wire_segments(text: str):
    segments = []
    for form in extract_forms(text, "wire"):
        points = parse_xy(form.text)
        for a, b in zip(points, points[1:]):
            segments.append((a, b))
    return segments


def label_names(text: str, head: str):
    result = []
    for form in extract_forms(text, head):
        name = head_string(form.text, head)
        at = parse_at(form.text)
        if name and at:
            result.append((name, at, form.line))
    return result


refs = defaultdict(list)
for path in CHILDREN:
    text = authored(path)
    for form in extract_forms(text, "symbol"):
        if "(lib_id " not in form.text:
            continue
        ref = property_value(form.text, "Reference")
        if ref and not ref.startswith("#"):
            refs[ref].append(path.name)
for ref, sheets in refs.items():
    if len(sheets) > 1:
        errors.append(f"duplicate component reference {ref}: {sheets}")

for path in CHILDREN:
    text = authored(path)
    segments = wire_segments(text)
    if not segments:
        errors.append(f"{path.name}: no native wire records")
    for head in ["label", "hierarchical_label"]:
        for name, point, line in label_names(text, head):
            if not any(on_segment(point, a, b) for a, b in segments):
                errors.append(f"{path.name}:{line}: floating {head} {name} at {point}")

top = authored(TOP)
parent: dict[str, list[str]] = {}
for sheet in extract_forms(top, "sheet"):
    file = property_value(sheet.text, "Sheetfile")
    if not file:
        continue
    pins = []
    for pin in extract_forms(sheet.text, "pin"):
        match = re.match(r'\(pin\s+"((?:\\.|[^"\\])*)"', pin.text)
        if match:
            pins.append(match.group(1))
    parent[file] = sorted(pins)

for child in CHILDREN:
    text = authored(child)
    expected = sorted(
        name for name, _, _ in label_names(text, "hierarchical_label")
    )
    actual = parent.get(child.name)
    if actual is None:
        errors.append(f"top schematic missing child sheet {child.name}")
        continue
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        errors.append(
            f"{child.name}: hierarchy pin mismatch "
            f"missing_in_parent={missing} extra_in_parent={extra}"
        )

for obsolete in ["U_SH_P", "U_SH_N", "V_SH_P", "V_SH_N", "W_SH_P", "W_SH_N"]:
    if obsolete in top:
        errors.append(f"top schematic still contains obsolete Kelvin pseudo-net {obsolete}")

if errors:
    print("SCHEMATIC CONNECTIVITY CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("SCHEMATIC CONNECTIVITY CHECK PASSED")
