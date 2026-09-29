from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
GRID = 50

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


def on_grid(value: int) -> bool:
    return value % GRID == 0


def check_coords(path: Path, lineno: int, kind: str, values: list[int]) -> None:
    bad = [value for value in values if not on_grid(value)]
    if bad:
        errors.append(
            f"{path.relative_to(ROOT)}:{lineno}: {kind} off {GRID}mil grid: "
            f"{values}"
        )


# Custom-symbol connection points must align with the same grid as the schematic.
lib = HW / "ax7010_servo_reva.lib"
for lineno, line in enumerate(lib.read_text(errors="strict").splitlines(), start=1):
    if not line.startswith("X "):
        continue
    parts = line.split()
    if len(parts) < 6:
        errors.append(f"{lib.relative_to(ROOT)}:{lineno}: malformed X pin: {line}")
        continue
    check_coords(
        lib,
        lineno,
        "symbol pin x/y/length",
        [int(parts[3]), int(parts[4]), int(parts[5])],
    )

for path in SCHEMATICS:
    lines = path.read_text(errors="strict").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        m = re.fullmatch(r"P (-?\d+) (-?\d+)", line)
        if m:
            check_coords(path, i + 1, "component origin", [int(m.group(1)), int(m.group(2))])
            i += 1
            continue

        if line == "Wire Wire Line":
            if i + 1 >= len(lines):
                errors.append(f"{path.relative_to(ROOT)}:{i+1}: Wire without coordinates")
                break
            coords = [int(v) for v in lines[i + 1].split()]
            if len(coords) == 4:
                check_coords(path, i + 2, "wire", coords)
            i += 2
            continue

        m = re.match(r"Text (?:Label|HLabel|GLabel) (-?\d+) (-?\d+)", line)
        if m:
            check_coords(path, i + 1, "electrical label", [int(m.group(1)), int(m.group(2))])
            i += 1
            continue

        m = re.fullmatch(r"(?:NoConn|Connection) ~ (-?\d+) (-?\d+)", line)
        if m:
            check_coords(path, i + 1, "connection marker", [int(m.group(1)), int(m.group(2))])
            i += 1
            continue

        m = re.match(r'F\d+ "[^"]+" [IOBT] [LRUD] (-?\d+) (-?\d+) \d+$', line)
        if m:
            check_coords(path, i + 1, "hierarchical sheet pin", [int(m.group(1)), int(m.group(2))])

        i += 1

if errors:
    print("KICAD GRID CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("KICAD GRID CHECK PASSED")
