"""Generic schematic hierarchy, syntax, geometry and visible local wiring."""
from collections import Counter
from pathlib import Path
import math
import re
from .kicad import assert_balanced, extract_forms, head_string, parse_at, parse_xy, property_value, strip_form
from .report import Finding
from .project import ProjectError


def discover_sheets(project):
    found = []
    def visit(path, stack):
        path = path.resolve()
        if not path.is_relative_to(project.root):
            raise ProjectError("Hierarchy source outside project root")
        if path in stack: raise ProjectError("Cyclic schematic hierarchy")
        if not path.is_file(): raise ProjectError(f"Missing child schematic: {path.name}")
        raw = path.read_text(encoding="utf-8-sig")
        assert_balanced(raw)
        text = strip_form(raw, "lib_symbols")
        ids = set()
        children = []
        for sheet in extract_forms(text, "sheet"):
            name = property_value(sheet.text, "Sheetfile")
            uuids = extract_forms(sheet.text, "uuid")
            ident = head_string(uuids[0].text, "uuid") if uuids else None
            if not name or not ident: raise ProjectError("Sheet requires a source file and instance UUID")
            if ident in ids: raise ProjectError("Duplicate hierarchy instance path")
            ids.add(ident)
            children.append(path.parent / name)
        if path not in found: found.append(path)
        for child in children: visit(child, (*stack, path))
    visit(project.schematic, ())
    return found


def missing_wire_junctions(text):
    """Find wire-end T taps; an unjoined interior/interior crossing stays unjoined."""
    segments = [tuple(parse_xy(f.text)) for f in extract_forms(text, "wire")]
    endpoints = {node for pair in segments for node in pair}
    existing = {parse_at(f.text) for f in extract_forms(text, "junction")}
    missing = []
    for node in sorted(endpoints - existing):
        rays = set()
        for a, b in segments:
            if not on_segment(node, a, b):
                continue
            for x, y in (a, b):
                dx, dy = round(x - node[0], 6), round(y - node[1], 6)
                if dx or dy:
                    rays.add((0 if not dx else 1 if dx > 0 else -1,
                              0 if not dy else 1 if dy > 0 else -1))
        if len(rays) >= 3:
            missing.append(node)
    return missing


def implicit_wire_widths(text):
    """Locate wires using a missing, zero or invalid explicit stroke width."""
    bad = []
    for wire in extract_forms(text, "wire"):
        widths = re.findall(r"\(width\s+([-+\d.eE]+)\)", wire.text)
        if len(widths) != 1 or not math.isfinite(float(widths[0])) or float(widths[0]) <= 0:
            bad.append(wire.line)
    return bad


def check_schematic(project):
    issues = {key: [] for key in ("native", "grid", "layout", "connectivity", "power")}
    try:
        paths = discover_sheets(project)
    except (ProjectError, ValueError, OSError) as exc:
        return [Finding("schematic.native", "FAIL", str(exc))]
    grid = project.parameters.get("grid_mm", 1.27)
    if not isinstance(grid, (int, float)) or grid <= 0: raise ProjectError("grid_mm must be positive")
    paper = project.parameters.get("paper", "A4")
    if paper != "A4": raise ProjectError("Only A4 landscape geometry is implemented; other page envelopes must be added explicitly")
    refs = Counter()
    top_raw = project.schematic.read_text(encoding="utf-8-sig")
    roots = extract_forms(strip_form(top_raw, "lib_symbols"), "uuid")
    root_uuid = head_string(roots[0].text, "uuid") if roots else None
    for path in paths:
        try:
            raw = path.read_text(encoding="utf-8-sig")
            if not re.match(r"^\(kicad_sch\s+\(version\s+\d+\)", raw):
                issues["native"].append(f"{path.name}: invalid native header")
            if f'(paper "{paper}")' not in raw: issues["native"].append(f"{path.name}: paper must be {paper}")
            if not extract_forms(raw, "lib_symbols"): issues["native"].append(f"{path.name}: missing embedded symbols")
            if re.search(r'\.sch"', raw): issues["native"].append(f"{path.name}: legacy source reference")
            text = strip_form(raw, "lib_symbols")
            if extract_forms(text, "global_label") and project.parameters.get("forbid_global_labels", False):
                issues["layout"].append(f"{path.name}: Global Labels are forbidden by project")
            if project.parameters.get("require_explicit_wire_junctions", False):
                for node in missing_wire_junctions(text):
                    issues["connectivity"].append(f"{path.name}: wire T tap at {node} lacks explicit junction")
            if project.parameters.get("require_explicit_wire_widths", False):
                for line in implicit_wire_widths(text):
                    issues["native"].append(f"{path.name}:{line}: wire needs a positive explicit width for GUI save stability")
            local_points = {}
            hnames = set()
            segments = [pair for f in extract_forms(text, "wire") for pair in zip(parse_xy(f.text), parse_xy(f.text)[1:])]
            for head in ("label", "hierarchical_label", "junction", "no_connect", "wire", "symbol", "sheet"):
                for form in extract_forms(text, head):
                    if head == "symbol" and "(lib_id " not in form.text: continue
                    points = parse_xy(form.text) if head == "wire" else ([parse_at(form.text)] if parse_at(form.text) else [])
                    if head == "sheet":
                        points += [parse_at(pin.text) for pin in extract_forms(form.text, "pin") if parse_at(pin.text)]
                    for x, y in points:
                        if any(abs(v/grid-round(v/grid)) > 1e-6 for v in (x,y)):
                            issues["grid"].append(f"{path.name}:{form.line}: {head} off {grid}mm grid")
                        if not (7.62-1e-6 <= x <= 289.3822+1e-6 and 7.62-1e-6 <= y <= 202.3872+1e-6):
                            issues["layout"].append(f"{path.name}:{form.line}: outside A4 drawing-safe region")
                        if head == "hierarchical_label" and not (15.24-1e-6 <= x <= 279.4+1e-6 and 11.43-1e-6 <= y <= 190.5+1e-6):
                            issues["layout"].append(f"{path.name}:{form.line}: hierarchy port too close to A4 frame")
                    if head == "wire" and points and points[0] == points[-1]: issues["layout"].append(f"{path.name}: zero-length wire")
                    if head in {"label", "hierarchical_label"}:
                        name = head_string(form.text, head)
                        at = parse_at(form.text)
                        if head == "label":
                            if at in local_points: issues["layout"].append(f"{path.name}: duplicate local label position")
                            local_points[at] = name
                        else:
                            if name in hnames: issues["layout"].append(f"{path.name}: duplicate hierarchy port {name}")
                            hnames.add(name)
                        if at and not any(on_segment(at,a,b) for a,b in segments):
                            issues["connectivity"].append(f"{path.name}: floating {head} {name}")
            for f in extract_forms(text, "symbol"):
                if "(lib_id " not in f.text: continue
                ref = property_value(f.text, "Reference")
                unit = re.search(r"\(unit (\d+)\)", f.text)
                if ref and not ref.startswith("#"): refs[(ref,unit[1] if unit else "1")] += 1
            for child in extract_forms(text, "sheet"):
                name = property_value(child.text, "Sheetfile")
                child_text = strip_form((path.parent/name).read_text(encoding="utf-8-sig"),"lib_symbols")
                expected = {head_string(f.text,"hierarchical_label") for f in extract_forms(child_text,"hierarchical_label")}
                actual = {head_string(f.text,"pin") for f in extract_forms(child.text,"pin")}
                if expected != actual: issues["connectivity"].append(f"{name}: hierarchy pin mismatch")
            if path != project.schematic or not extract_forms(text,"sheet"):
                issues["power"].extend(check_power(path))
            if root_uuid:
                for instance in set(re.findall(r'\(path "(/[^" ]+)"', text)):
                    if instance != "/" and instance.split("/")[1] != root_uuid:
                        issues["native"].append(f"{path.name}: instance path root differs from top UUID")
        except (OSError, ValueError, IndexError, KeyError, TypeError) as exc:
            issues["native"].append(f"{path.name}: {type(exc).__name__}: {exc}")
    for ref, count in refs.items():
        if count > 1: issues["connectivity"].append(f"duplicate component reference/unit {ref}")
    for lib in project.libraries:
        text = lib.read_text(encoding="utf-8-sig")
        try:
            assert_balanced(text)
            if not re.match(r"^\(kicad_symbol_lib\s+\(version\s+\d+\)", text): raise ValueError("invalid native library header")
        except ValueError as exc: issues["native"].append(f"{lib.name}: {exc}")
    for path in project.schematic.parent.glob("*"):
        if path.suffix in {".sch", ".lib"}: issues["native"].append(f"legacy source remains: {path.name}")
    return [Finding("schematic."+key, "FAIL" if errors else "PASS", "; ".join(errors) if errors else "Check passed", {"errors":errors,"files":len(paths)}) for key,errors in issues.items()]

def point(x, y):
    return round(x, 6), round(y, 6)


def on_segment(p, a, b):
    return (abs((p[0] - a[0]) * (b[1] - a[1]) -
                (p[1] - a[1]) * (b[0] - a[0])) < 1e-6 and
            min(a[0], b[0]) - 1e-6 <= p[0] <= max(a[0], b[0]) + 1e-6 and
            min(a[1], b[1]) - 1e-6 <= p[1] <= max(a[1], b[1]) + 1e-6)


def check_power(path):
    raw = path.read_text(encoding="utf-8")
    lib = extract_forms(raw, "lib_symbols")[0].text
    definitions = {head_string(f.text, "symbol"): f.text
                   for f in extract_forms(lib, "symbol")}
    text = strip_form(raw, "lib_symbols")
    wires = [parse_xy(f.text) for f in extract_forms(text, "wire")]
    segments = [(a, b) for p in wires for a, b in zip(p, p[1:])]
    physical = set()
    targets = []
    for f in extract_forms(text, "symbol"):
        if "(lib_id " not in f.text:
            continue
        ref = property_value(f.text, "Reference")
        origin = parse_at(f.text)
        if ref and ref.startswith("#"):
            targets.append((ref, origin))
            continue
        name = re.search(r'\(lib_id "([^"]+)"', f.text)[1]
        angle_match = re.search(r'\(at [-\d.]+ [-\d.]+ ([-\d.]+)\)', f.text)
        angle = float(angle_match[1]) if angle_match else 0.0
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
