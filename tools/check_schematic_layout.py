from pathlib import Path
import sys

from kicad_native import extract_forms, head_string, parse_at, parse_xy, strip_form

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
SCHEMATICS = sorted(HW.glob("*.kicad_sch"))

# Legacy safe envelope converted exactly from mils to millimetres.
SAFE_DRAW_X = (7.62, 289.3822)
SAFE_DRAW_Y = (7.62, 202.3872)
SAFE_HLABEL_X = (15.24, 279.4)
SAFE_HLABEL_Y = (11.43, 190.5)
TOL = 1e-6
errors: list[str] = []


def in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] - TOL <= value <= bounds[1] + TOL


def check_point(
    path: Path,
    line: int,
    kind: str,
    point: tuple[float, float],
    *,
    hlabel: bool = False,
) -> None:
    x, y = point
    if not in_range(x, SAFE_DRAW_X) or not in_range(y, SAFE_DRAW_Y):
        errors.append(
            f"{path.name}:{line}: {kind} at ({x}, {y}) outside A4 drawing-safe region"
        )
    if hlabel and (
        not in_range(x, SAFE_HLABEL_X) or not in_range(y, SAFE_HLABEL_Y)
    ):
        errors.append(
            f"{path.name}:{line}: {kind} at ({x}, {y}) too close to A4 frame"
        )


for path in SCHEMATICS:
    text = strip_form(
        path.read_text(encoding="utf-8", errors="strict"), "lib_symbols"
    )

    for form in extract_forms(text, "global_label"):
        errors.append(f"{path.name}:{form.line}: Global Label is forbidden")

    local_at: dict[tuple[float, float], str] = {}
    for form in extract_forms(text, "label"):
        at = parse_at(form.text)
        name = head_string(form.text, "label") or "<unnamed>"
        if at:
            check_point(path, form.line, f"local label {name}", at)
            if at in local_at:
                errors.append(
                    f"{path.name}:{form.line}: duplicate/conflicting local label at "
                    f"{at}: {local_at[at]!r} vs {name!r}"
                )
            local_at[at] = name

    hnames: set[str] = set()
    for form in extract_forms(text, "hierarchical_label"):
        at = parse_at(form.text)
        name = head_string(form.text, "hierarchical_label") or "<unnamed>"
        if at:
            check_point(
                path, form.line, f"hierarchical label {name}", at, hlabel=True
            )
        if name in hnames:
            errors.append(f"{path.name}:{form.line}: duplicate hierarchy port {name}")
        hnames.add(name)

    for head in ["junction", "no_connect"]:
        for form in extract_forms(text, head):
            at = parse_at(form.text)
            if at:
                check_point(path, form.line, head, at)

    for form in extract_forms(text, "wire"):
        points = parse_xy(form.text)
        for point in points:
            check_point(path, form.line, "wire endpoint", point)
        if len(points) >= 2 and points[0] == points[-1]:
            errors.append(f"{path.name}:{form.line}: zero-length wire at {points[0]}")

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
    print("SCHEMATIC LAYOUT CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("SCHEMATIC LAYOUT CHECK PASSED")
