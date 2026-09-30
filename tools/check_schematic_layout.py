from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
SCHEMATICS = [
    HW / "ax7010_servo_reva.sch",
    HW / "power_input.sch",
    HW / "aux_power.sch",
    HW / "gate_inverter.sch",
    HW / "current_adc.sch",
    HW / "encoder.sch",
    HW / "ax7010_interface.sch",
]

errors = []

# Legacy KiCad A4 coordinates are mils. Keep all authored schematic objects
# comfortably inside the 11693 x 8268 frame so conversion/rendering cannot
# clip labels, wires or symbols into the title block/frame.
SAFE_DRAW_X = (300, 11393)
SAFE_DRAW_Y = (300, 7968)
SAFE_HLABEL_X = (600, 11000)
SAFE_HLABEL_Y = (450, 7500)


def check_point(path: Path, line_no: int, kind: str, x: int, y: int):
    if not (SAFE_DRAW_X[0] <= x <= SAFE_DRAW_X[1]):
        errors.append(
            f"{path.name}:{line_no}: {kind} x={x} is too close to/outside A4 frame"
        )
    if not (SAFE_DRAW_Y[0] <= y <= SAFE_DRAW_Y[1]):
        errors.append(
            f"{path.name}:{line_no}: {kind} y={y} is too close to/outside A4 frame"
        )


for path in SCHEMATICS:
    lines = path.read_text(errors="strict").splitlines()
    labels_at = {}
    hlabels = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        pm = re.match(r"^P\s+(-?\d+)\s+(-?\d+)$", line)
        if pm:
            x, y = map(int, pm.groups())
            check_point(path, i + 1, "component origin", x, y)
            i += 1
            continue

        gm = re.match(r"^Text GLabel\s+(-?\d+)\s+(-?\d+)\s+", line)
        if gm:
            x, y = map(int, gm.groups())
            name = lines[i + 1] if i + 1 < len(lines) else ""
            errors.append(
                f"{path.name}:{i+1}: Global Label {name!r} is forbidden in this "
                "hierarchical design; use HLabel+sheet pin for cross-sheet nets, "
                "or direct wire/local label within one sheet"
            )
            check_point(path, i + 1, f"GLabel {name}", x, y)
            i += 2
            continue

        hm = re.match(r"^Text HLabel\s+(-?\d+)\s+(-?\d+)\s+", line)
        if hm:
            x, y = map(int, hm.groups())
            name = lines[i + 1] if i + 1 < len(lines) else ""
            check_point(path, i + 1, f"HLabel {name}", x, y)
            if not (SAFE_HLABEL_X[0] <= x <= SAFE_HLABEL_X[1]):
                errors.append(
                    f"{path.name}:{i+1}: HLabel {name} x={x} is too close to/outside A4 frame"
                )
            if not (SAFE_HLABEL_Y[0] <= y <= SAFE_HLABEL_Y[1]):
                errors.append(
                    f"{path.name}:{i+1}: HLabel {name} y={y} is too close to/outside A4 frame"
                )
            if name in hlabels:
                errors.append(f"{path.name}:{i+1}: duplicate hierarchy port {name}")
            hlabels[name] = i + 1
            i += 2
            continue

        lm = re.match(r"^Text Label\s+(-?\d+)\s+(-?\d+)\s+", line)
        if lm:
            coord = tuple(map(int, lm.groups()))
            name = lines[i + 1] if i + 1 < len(lines) else ""
            check_point(path, i + 1, f"local label {name}", *coord)
            previous = labels_at.get(coord)
            if previous is not None:
                if previous == name:
                    errors.append(
                        f"{path.name}:{i+1}: duplicate local label {name!r} at {coord}"
                    )
                else:
                    errors.append(
                        f"{path.name}:{i+1}: conflicting local labels at {coord}: "
                        f"{previous!r} vs {name!r}"
                    )
            labels_at[coord] = name
            i += 2
            continue

        tm = re.match(r"^Text Notes\s+(-?\d+)\s+(-?\d+)\s+", line)
        if tm:
            x, y = map(int, tm.groups())
            check_point(path, i + 1, "note", x, y)
            i += 2
            continue

        mm = re.match(r"^(?:Connection|NoConn) ~ (-?\d+) (-?\d+)$", line)
        if mm:
            x, y = map(int, mm.groups())
            check_point(path, i + 1, "connection marker", x, y)
            i += 1
            continue

        if line == "Wire Wire Line" and i + 1 < len(lines):
            coords = [int(v) for v in lines[i + 1].split()]
            if len(coords) == 4:
                check_point(path, i + 2, "wire endpoint", coords[0], coords[1])
                check_point(path, i + 2, "wire endpoint", coords[2], coords[3])
                if coords[0] == coords[2] and coords[1] == coords[3]:
                    errors.append(
                        f"{path.name}:{i+2}: zero-length wire at ({coords[0]}, {coords[1]})"
                    )
            i += 2
            continue

        i += 1

if errors:
    print("SCHEMATIC LAYOUT CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("SCHEMATIC LAYOUT CHECK PASSED")
