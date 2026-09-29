from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
LIB = HW / "ax7010_servo_reva.lib"
TOP = HW / "ax7010_servo_reva.sch"
CHILDREN = [
    HW / "power_input.sch",
    HW / "aux_power.sch",
    HW / "gate_inverter.sch",
    HW / "current_adc.sch",
    HW / "encoder.sch",
    HW / "ax7010_interface.sch",
]


def parse_symbols(text: str):
    symbols = {}
    current = None
    in_draw = False
    for line in text.splitlines():
        m = re.match(r"^DEF\s+(\S+)", line)
        if m:
            current = m.group(1)
            symbols[current] = {}
            continue
        if line == "DRAW":
            in_draw = True
            continue
        if line == "ENDDRAW":
            in_draw = False
            continue
        if line == "ENDDEF":
            current = None
            continue
        if current and in_draw and line.startswith("X "):
            parts = line.split()
            symbols[current][parts[2]] = {
                "name": parts[1],
                "x": int(parts[3]),
                "y": int(parts[4]),
            }
    return symbols


def components(text: str):
    result = []
    for block in text.split("$Comp\n")[1:]:
        body = block.split("$EndComp", 1)[0]
        lm = re.search(r"^L ax7010_servo_reva:(\S+)\s+(\S+)", body, re.M)
        pm = re.search(r"^P\s+(-?\d+)\s+(-?\d+)", body, re.M)
        if lm and pm:
            result.append(
                {
                    "symbol": lm.group(1),
                    "ref": lm.group(2),
                    "x": int(pm.group(1)),
                    "y": int(pm.group(2)),
                }
            )
    return result


def wire_and_noconn_points(text: str):
    lines = text.splitlines()
    wire_points = set()
    noconn_points = set()
    i = 0
    while i < len(lines):
        if lines[i] == "Wire Wire Line":
            if i + 1 < len(lines):
                nums = [int(v) for v in lines[i + 1].split()]
                if len(nums) == 4:
                    wire_points.add((nums[0], nums[1]))
                    wire_points.add((nums[2], nums[3]))
            i += 2
            continue
        m = re.match(r"^NoConn ~ (-?\d+) (-?\d+)$", lines[i])
        if m:
            noconn_points.add((int(m.group(1)), int(m.group(2))))
        i += 1
    return wire_points, noconn_points


def child_hlabels(text: str):
    lines = text.splitlines()
    names = []
    for i, line in enumerate(lines[:-1]):
        if line.startswith("Text HLabel "):
            names.append(lines[i + 1])
    return sorted(names)


def parent_sheet_pins(text: str):
    result = {}
    for block in text.split("$Sheet\n")[1:]:
        body = block.split("$EndSheet", 1)[0]
        fm = re.search(r'^F1 "([^"]+)"', body, re.M)
        if not fm:
            continue
        pins = [
            m.group(1)
            for m in re.finditer(r'^F\d+ "([^"]+)" [IOBT] ', body, re.M)
        ]
        result[fm.group(1)] = sorted(pins)
    return result


errors = []
symbols = parse_symbols(LIB.read_text(errors="strict"))

# Legacy hierarchical schematics need AR records so child symbols are
# instantiated on the parent sheet path. Without them KiCad can render the
# drawings yet export an empty component/net list.
SHEET_IDS = {
    "power_input.sch": "69000001",
    "aux_power.sch": "69000002",
    "gate_inverter.sch": "69000003",
    "ax7010_interface.sch": "69000004",
    "current_adc.sch": "69000005",
    "encoder.sch": "69000006",
}
for path in CHILDREN:
    text = path.read_text(errors="strict")
    expected_sheet = SHEET_IDS[path.name]
    for block in text.split("$Comp\\n")[1:]:
        body = block.split("$EndComp", 1)[0]
        um = re.search(r"^U\\s+\\d+\\s+\\d+\\s+([0-9A-Fa-f]{8})$", body, re.M)
        lm = re.search(r"^L\\s+\\S+\\s+(\\S+)$", body, re.M)
        if not um or not lm:
            continue
        stamp = um.group(1).upper()
        ref = lm.group(1)
        expected = f'AR Path="/{expected_sheet}/{stamp}" Ref="{ref}"  Part="1"'
        if expected not in body:
            errors.append(f"{path.name}: {ref} missing hierarchy AR record {expected}")

for path in CHILDREN:
    text = path.read_text(errors="strict")
    wire_points, noconn_points = wire_and_noconn_points(text)
    if not wire_points:
        errors.append(f"{path.name}: no Wire Wire Line records")

    for comp in components(text):
        symbol = symbols.get(comp["symbol"])
        if symbol is None:
            errors.append(f"{path.name}: missing local symbol {comp['symbol']}")
            continue
        for pin_no, pin in symbol.items():
            # All current Rev.A1 project symbols use transform 1 0 0 -1.
            endpoint = (comp["x"] + pin["x"], comp["y"] - pin["y"])
            if endpoint not in wire_points and endpoint not in noconn_points:
                errors.append(
                    f"{path.name}: {comp['ref']} pin {pin_no} ({pin['name']}) "
                    f"has no Wire endpoint or NoConn at {endpoint}"
                )

top_text = TOP.read_text(errors="strict")
if not re.search(r"^Wire Wire Line$", top_text, re.M):
    errors.append("top schematic has no visible wiring")

parent = parent_sheet_pins(top_text)
for child in CHILDREN:
    text = child.read_text(errors="strict")
    expected = child_hlabels(text)
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
    if obsolete in top_text:
        errors.append(f"top schematic still contains obsolete Kelvin pseudo-net {obsolete}")

if errors:
    print("SCHEMATIC CONNECTIVITY CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("SCHEMATIC CONNECTIVITY CHECK PASSED")
