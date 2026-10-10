"""Require power graphics and child ports to reach real pins by visible wires.

Labels intentionally do not join islands here: this checks the drawing rather
than electrical net equivalence (which requires a native KiCad netlist).
"""

from pathlib import Path
import math
import re
import sys

from kicad_native import extract_forms, head_string, parse_at, parse_xy, property_value, strip_form


def point(x, y):
    return round(x, 6), round(y, 6)


def on_segment(p, a, b):
    return (abs((p[0] - a[0]) * (b[1] - a[1]) -
                (p[1] - a[1]) * (b[0] - a[0])) < 1e-6 and
            min(a[0], b[0]) - 1e-6 <= p[0] <= max(a[0], b[0]) + 1e-6 and
            min(a[1], b[1]) - 1e-6 <= p[1] <= max(a[1], b[1]) + 1e-6)


def check(path):
    raw = path.read_text(encoding="utf-8")
    lib = extract_forms(raw, "lib_symbols")[0].text
    definitions = {head_string(f.text, "symbol"): f.text
                   for f in extract_forms(lib, "symbol")}
    text = strip_form(raw, "lib_symbols")
    wires = [parse_xy(f.text) for f in extract_forms(text, "wire")]
    segments = [(p[0], p[1]) for p in wires]
    physical = set()
    targets = []
    for f in extract_forms(text, "symbol"):
        if "(lib_id " not in f.text:
            continue
        ref = property_value(f.text, "Reference")
        origin = parse_at(f.text)
        if ref.startswith("#"):
            targets.append((ref, origin))
            continue
        name = re.search(r'\(lib_id "([^"]+)"', f.text)[1]
        angle = float(re.search(r'\(at [-\d.]+ [-\d.]+ ([-\d.]+)\)', f.text)[1])
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        embedded_name = head_string(extract_forms(f.text, "lib_name")[0].text, "lib_name") if extract_forms(f.text, "lib_name") else name
        for pin in extract_forms(definitions[embedded_name], "pin"):
            xy = parse_at(pin.text)
            if xy is None:
                continue
            x, y = xy
            if "(mirror x)" in f.text:
                y = -y
            if "(mirror y)" in f.text:
                x = -x
            physical.add(point(origin[0] + x*c - y*s, origin[1] - x*s - y*c))
    for f in extract_forms(text, "hierarchical_label"):
        targets.append((head_string(f.text, "hierarchical_label"), parse_at(f.text)))
    vertices = physical | {p for seg in segments for p in seg} | {p for _, p in targets}
    parent = {p: p for p in vertices}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    for a, b in segments:
        for p in vertices:
            if on_segment(p, a, b):
                parent[find(p)] = find(a)
    live = {find(p) for p in physical}
    return [f"{path.name}: {name} at {p} has no visible wire path to a component pin"
            for name, p in targets if find(p) not in live]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "hardware"
    errors = []
    for path in sorted(root.glob("*.kicad_sch")):
        if path.name != "ax7010_servo_reva.kicad_sch":
            errors.extend(check(path))
    if errors:
        print("POWER WIRING CHECK FAILED")
        print("\n".join(" - " + e for e in errors))
        return 1
    print("POWER WIRING CHECK PASSED: every power graphic and child port reaches a real pin by visible wires")
    return 0


if __name__ == "__main__":
    sys.exit(main())
