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


def parse_legacy(path: Path) -> list[str]:
    lines = path.read_text(errors="strict").replace("\r", "").split("\n")
    errors: list[str] = []
    i = 0

    if i >= len(lines) or not re.fullmatch(r"EESchema Schematic File Version \d+", lines[i]):
        return [f"{path.name}:1: invalid legacy schematic header"]
    i += 1

    while i < len(lines) and lines[i] != "EELAYER END":
        i += 1
    if i >= len(lines):
        return [f"{path.name}: missing EELAYER END"]
    i += 1

    if i >= len(lines) or not lines[i].startswith("$Descr "):
        return [f"{path.name}:{i+1}: expected $Descr"]
    while i < len(lines) and lines[i] != "$EndDescr":
        i += 1
    if i >= len(lines):
        return [f"{path.name}: missing $EndDescr"]
    i += 1

    while i < len(lines):
        line = lines[i]

        # A final empty element is expected from a terminal newline only.
        if line == "" and i == len(lines) - 1:
            break
        if line == "":
            errors.append(f"{path.name}:{i+1}: blank physical line")
            i += 1
            continue

        if line == "$EndSCHEMATC":
            i += 1
            break

        if line == "$Comp":
            start = i + 1
            i += 1
            saw_l = saw_u = saw_p = saw_end = False
            transform_lines = 0

            while i < len(lines):
                item = lines[i]
                if item == "$EndComp":
                    saw_end = True
                    i += 1
                    break
                if re.fullmatch(r"L \S+ \S+", item):
                    saw_l = True
                elif re.fullmatch(r"U \d+ \d+ [0-9A-Fa-f]{8}", item):
                    saw_u = True
                elif re.fullmatch(r"P -?\d+ -?\d+", item):
                    saw_p = True
                elif item.startswith("AR ") or re.match(r"F \d+ ", item):
                    pass
                elif re.fullmatch(r"\s+-?\d+\s+-?\d+\s+-?\d+(?:\s+-?\d+)?\s*", item):
                    transform_lines += 1
                else:
                    errors.append(
                        f"{path.name}:{i+1}: unknown token inside $Comp: {item!r}"
                    )
                i += 1

            if not (saw_l and saw_u and saw_p and saw_end and transform_lines >= 2):
                errors.append(
                    f"{path.name}:{start}: incomplete $Comp "
                    f"L={saw_l} U={saw_u} P={saw_p} "
                    f"end={saw_end} transforms={transform_lines}"
                )
            continue

        if line == "$Sheet":
            start = i + 1
            i += 1
            saw_end = False
            while i < len(lines):
                item = lines[i]
                if item == "$EndSheet":
                    saw_end = True
                    i += 1
                    break
                valid = (
                    re.fullmatch(r"S -?\d+ -?\d+ \d+ \d+", item)
                    or re.fullmatch(r"U [0-9A-Fa-f]{8}", item)
                    or re.match(r"F\d+ ", item)
                )
                if not valid:
                    errors.append(
                        f"{path.name}:{i+1}: unknown token inside $Sheet: {item!r}"
                    )
                i += 1
            if not saw_end:
                errors.append(f"{path.name}:{start}: unclosed $Sheet")
            continue

        if re.fullmatch(r"Wire (Wire|Bus) Line", line):
            if i + 1 >= len(lines) or not re.fullmatch(
                r"\s*-?\d+\s+-?\d+\s+-?\d+\s+-?\d+\s*", lines[i + 1]
            ):
                errors.append(f"{path.name}:{i+2}: invalid Wire coordinate record")
            i += 2
            continue

        if re.match(r"Text (Label|HLabel|GLabel|Notes) ", line):
            if i + 1 >= len(lines) or lines[i + 1] == "":
                errors.append(f"{path.name}:{i+1}: Text record missing payload line")
            i += 2
            continue

        if re.fullmatch(r"(Connection|NoConn) ~ -?\d+ -?\d+", line):
            i += 1
            continue

        if line.startswith("Entry "):
            if i + 1 >= len(lines) or not re.fullmatch(
                r"\s*-?\d+\s+-?\d+\s+-?\d+\s+-?\d+\s*", lines[i + 1]
            ):
                errors.append(f"{path.name}:{i+2}: invalid Entry coordinate record")
            i += 2
            continue

        errors.append(f"{path.name}:{i+1}: unknown top-level token: {line!r}")
        i += 1

    return errors


all_errors: list[str] = []
for schematic in SCHEMATICS:
    if not schematic.exists():
        all_errors.append(f"missing schematic: {schematic.relative_to(ROOT)}")
        continue
    all_errors.extend(parse_legacy(schematic))

if all_errors:
    print("LEGACY SCHEMATIC PARSER CHECK FAILED")
    for error in all_errors:
        print(" -", error)
    sys.exit(1)

print("LEGACY SCHEMATIC PARSER CHECK PASSED")
