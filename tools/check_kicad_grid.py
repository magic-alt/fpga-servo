from pathlib import Path
import sys

from kicad_native import extract_forms, parse_at, parse_xy, strip_form

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
SCHEMATICS = sorted(HW.glob("*.kicad_sch"))
GRID_MM = 1.27  # 50 mil
TOL = 1e-6
errors: list[str] = []


def on_grid(value: float) -> bool:
    return abs(value / GRID_MM - round(value / GRID_MM)) <= TOL


def check_point(
    path: Path, line: int, kind: str, point: tuple[float, float]
) -> None:
    if any(not on_grid(value) for value in point):
        errors.append(
            f"{path.relative_to(ROOT)}:{line}: {kind} off 50mil/1.27mm grid: {point}"
        )


for path in SCHEMATICS:
    text = strip_form(
        path.read_text(encoding="utf-8", errors="strict"), "lib_symbols"
    )

    for head in ["label", "hierarchical_label", "junction", "no_connect"]:
        for form in extract_forms(text, head):
            at = parse_at(form.text)
            if at:
                check_point(path, form.line, head, at)

    for form in extract_forms(text, "wire"):
        for point in parse_xy(form.text):
            check_point(path, form.line, "wire point", point)

    for form in extract_forms(text, "symbol"):
        if "(lib_id " not in form.text:
            continue
        at = parse_at(form.text)
        if at:
            check_point(path, form.line, "symbol origin", at)

    for sheet in extract_forms(text, "sheet"):
        at = parse_at(sheet.text)
        if at:
            check_point(path, sheet.line, "sheet origin", at)
        for pin in extract_forms(sheet.text, "pin"):
            pin_at = parse_at(pin.text)
            if pin_at:
                check_point(path, sheet.line, "sheet pin", pin_at)

if errors:
    print("KICAD GRID CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("KICAD GRID CHECK PASSED")
