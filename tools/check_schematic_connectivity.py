from pathlib import Path
from collections import defaultdict
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


def labels_at_wire_neighbours(text: str, point: tuple[int, int]) -> set[str]:
    lines = text.splitlines()
    labels = {}
    for index, line in enumerate(lines[:-1]):
        match = re.match(r"^Text (?:HLabel|Label) (-?\d+) (-?\d+) ", line)
        if match:
            labels.setdefault((int(match.group(1)), int(match.group(2))), set()).add(
                lines[index + 1]
            )

    found = set(labels.get(point, set()))
    for index, line in enumerate(lines[:-1]):
        if line != "Wire Wire Line":
            continue
        coords = tuple(int(value) for value in lines[index + 1].split())
        if len(coords) != 4:
            continue
        start, end = coords[:2], coords[2:]
        if start == point:
            found.update(labels.get(end, set()))
        elif end == point:
            found.update(labels.get(start, set()))
    return found


def wire_label_issues(text: str) -> tuple[list[list[str]], list[tuple[str, tuple[int, int]]]]:
    lines = text.splitlines()
    wires = []
    labels = []
    junctions = []
    for index, line in enumerate(lines[:-1]):
        if line == "Wire Wire Line":
            x1, y1, x2, y2 = map(int, lines[index + 1].split())
            wires.append(((x1, y1), (x2, y2)))
        match = re.match(r"^Text (?:HLabel|Label) (-?\d+) (-?\d+) ", line)
        if match:
            labels.append(((int(match.group(1)), int(match.group(2))), lines[index + 1]))
        match = re.match(r"^Connection ~ (-?\d+) (-?\d+)$", line)
        if match:
            junctions.append((int(match.group(1)), int(match.group(2))))

    def contains(wire, point):
        (x1, y1), (x2, y2) = wire
        x, y = point
        return (x - x1) * (y2 - y1) == (y - y1) * (x2 - x1) and (
            min(x1, x2) <= x <= max(x1, x2)
            and min(y1, y2) <= y <= max(y1, y2)
        )

    parent = list(range(len(wires)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for index, wire in enumerate(wires):
        for previous in range(index):
            other = wires[previous]
            connected = any(contains(other, point) for point in wire)
            connected |= any(contains(wire, point) for point in other)
            connected |= any(contains(wire, point) and contains(other, point) for point in junctions)
            if connected:
                parent[root(index)] = root(previous)

    names_by_group = defaultdict(set)
    floating = []
    for point, name in labels:
        attached = False
        for index, wire in enumerate(wires):
            if contains(wire, point):
                attached = True
                names_by_group[root(index)].add(name)
        if not attached:
            floating.append((name, point))
    conflicts = [sorted(names) for names in names_by_group.values() if len(names) > 1]
    return conflicts, floating


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


def sheet_pin_geometry_errors(text: str) -> list[str]:
    problems = []
    for block in text.split("$Sheet\n")[1:]:
        body = block.split("$EndSheet", 1)[0]
        rect = re.search(r"^S (\d+) (\d+) (\d+) (\d+)$", body, re.M)
        name = re.search(r'^F0 "([^"]+)"', body, re.M)
        if not rect or not name:
            problems.append("top schematic: malformed sheet rectangle")
            continue
        left, top, width, height = map(int, rect.groups())
        right, bottom = left + width, top + height
        for pin, side, x_text, y_text in re.findall(
            r'^F\d+ "([^"]+)" [IOBT] ([LR]) (\d+) (\d+) \d+$', body, re.M
        ):
            x, y = int(x_text), int(y_text)
            edge = left if side == "L" else right
            if x != edge or not (top < y < bottom):
                problems.append(
                    f"top schematic: {name.group(1)} pin {pin} at ({x}, {y}) "
                    f"is outside its {side} edge ({edge}, {top}..{bottom})"
                )
    return problems


errors = []
symbols = parse_symbols(LIB.read_text(errors="strict"))
references = defaultdict(list)
for path in CHILDREN:
    for comp in components(path.read_text(errors="strict")):
        references[comp["ref"]].append(path.name)
for ref, sheets in references.items():
    if len(sheets) > 1:
        errors.append(f"duplicate component reference {ref}: {sheets}")

for path in CHILDREN:
    text = path.read_text(errors="strict")
    wire_points, noconn_points = wire_and_noconn_points(text)
    conflicts, floating = wire_label_issues(text)
    for names in conflicts:
        errors.append(f"{path.name}: conflicting labels on one wire network: {names}")
    for name, point in floating:
        errors.append(f"{path.name}: floating label {name} at {point}")
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

        if comp["symbol"] == "INA241A2":
            ref2 = symbol["3"]
            endpoint = (comp["x"] + ref2["x"], comp["y"] - ref2["y"])
            net_labels = labels_at_wire_neighbours(text, endpoint)
            if net_labels != {"GND"}:
                errors.append(
                    f"{path.name}: {comp['ref']} REF2 must connect only to GND; "
                    f"found {sorted(net_labels)}"
                )

top_text = TOP.read_text(errors="strict")
errors.extend(sheet_pin_geometry_errors(top_text))
top_conflicts, top_floating = wire_label_issues(top_text)
for names in top_conflicts:
    errors.append(f"top schematic: conflicting labels on one wire network: {names}")
for name, point in top_floating:
    errors.append(f"top schematic: floating label {name} at {point}")
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
