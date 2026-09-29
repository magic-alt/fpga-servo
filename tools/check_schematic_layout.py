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
SAFE_HLABEL_X = (600, 11000)
SAFE_HLABEL_Y = (450, 7500)

for path in SCHEMATICS:
    lines = path.read_text(errors="strict").splitlines()
    labels_at = {}
    hlabels = {}

    i = 0
    while i < len(lines):
        line = lines[i]

        hm = re.match(r"^Text HLabel\s+(-?\d+)\s+(-?\d+)\s+", line)
        if hm:
            x, y = map(int, hm.groups())
            name = lines[i + 1] if i + 1 < len(lines) else ""
            if not (SAFE_HLABEL_X[0] <= x <= SAFE_HLABEL_X[1]):
                errors.append(f"{path.name}:{i+1}: HLabel {name} x={x} is too close to/outside A4 frame")
            if not (SAFE_HLABEL_Y[0] <= y <= SAFE_HLABEL_Y[1]):
                errors.append(f"{path.name}:{i+1}: HLabel {name} y={y} is too close to/outside A4 frame")
            if name in hlabels:
                errors.append(f"{path.name}:{i+1}: duplicate hierarchy port {name}")
            hlabels[name] = i + 1
            i += 2
            continue

        lm = re.match(r"^Text Label\s+(-?\d+)\s+(-?\d+)\s+", line)
        if lm:
            coord = tuple(map(int, lm.groups()))
            name = lines[i + 1] if i + 1 < len(lines) else ""
            previous = labels_at.get(coord)
            if previous is not None and previous != name:
                errors.append(
                    f"{path.name}:{i+1}: conflicting local labels at {coord}: "
                    f"{previous!r} vs {name!r}"
                )
            labels_at[coord] = name
            i += 2
            continue

        if line == "Wire Wire Line" and i + 1 < len(lines):
            coords = [int(v) for v in lines[i + 1].split()]
            if len(coords) == 4 and coords[0] == coords[2] and coords[1] == coords[3]:
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
