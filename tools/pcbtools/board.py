"""Grouped rule families; explicit contexts and no import-time checks."""
from types import SimpleNamespace

def parity_api():
    """Compare a freshly exported KiCad netlist with physical PCB pad assignments.

    No pcbnew dependency: usable in CI with Python 3.12. This proves graph parity,
    not routing, package dimensions, current ratings or release readiness.
    """

    import argparse
    import hashlib
    import json
    import re
    from pathlib import Path

    from pcbtools.kicad import assert_balanced, extract_forms, head_string, property_value



    def field(text: str, key: str) -> str:
        forms = extract_forms(text, key)
        return (head_string(forms[0].text, key) or "") if forms else ""


    def audit_text(netlist: str, pcb: str, mechanical_refs: set[str] | None = None) -> dict:
        assert_balanced(netlist)
        assert_balanced(pcb)
        allowed = mechanical_refs or set()
        components = {}
        duplicates = []
        for form in extract_forms(netlist, "comp"):
            ref = field(form.text, "ref")
            if ref in components:
                duplicates.append("schematic:" + ref)
            components[ref] = {"value": field(form.text, "value"),
                               "footprint": field(form.text, "footprint"), "pins": {},
                               "dnp": any(field(x.text, "name") == "dnp"
                                          for x in extract_forms(form.text, "property"))}
        nets = extract_forms(netlist, "net")
        for net in nets:
            name = field(net.text, "name")
            for node in extract_forms(net.text, "node"):
                ref, pin = field(node.text, "ref"), field(node.text, "pin")
                if ref not in components:
                    raise ValueError(f"netlist node references absent component: {ref}")
                if pin in components[ref]["pins"]:
                    raise ValueError(f"duplicate netlist physical pin: {ref}.{pin}")
                components[ref]["pins"][pin] = name
        footprints = {}
        for form in extract_forms(pcb, "footprint"):
            ref = property_value(form.text, "Reference")
            if not ref:
                raise ValueError("PCB footprint has no reference")
            if ref in footprints:
                duplicates.append("pcb:" + ref)
            pads = {}
            for pad in extract_forms(form.text, "pad"):
                pin = head_string(pad.text, "pad")
                net = extract_forms(pad.text, "net")
                name = ""
                if net:
                    match = re.fullmatch(r'\(net(?:\s+\d+)?\s+"((?:\\.|[^"\\])*)"\)', net[0].text)
                    if not match:
                        raise ValueError(f"cannot parse PCB net: {net[0].text}")
                    name = match.group(1)
                if pin:
                    pads.setdefault(pin, []).append(name)
            footprints[ref] = {"footprint": head_string(form.text, "footprint"),
                               "value": property_value(form.text, "Value"), "pads": pads,
                               "dnp": any(re.search(r"\bdnp\b", x.text)
                                          for x in extract_forms(form.text, "attr"))}
        report = {"schematic_components": len(components), "schematic_nets": len(nets),
                  "pcb_footprints": len(footprints), "duplicate_references": duplicates,
                  "missing_on_pcb": sorted(components.keys() - footprints.keys()),
                  "extra_on_pcb": [], "mechanical_preserved": [], "unassigned_footprints": [],
                  "footprint_mismatches": [], "pin_mismatches": [], "net_mismatches": [],
                  "value_mismatches": [], "dnp_mismatches": []}
        for ref in sorted(footprints.keys() - components.keys()):
            fp = footprints[ref]
            if (ref in allowed and fp["value"] == "M3_HOLE"
                    and not any(name for names in fp["pads"].values() for name in names)):
                report["mechanical_preserved"].append(ref)
            else:
                report["extra_on_pcb"].append(ref)
        for ref, comp in sorted(components.items()):
            if not comp["footprint"]:
                report["unassigned_footprints"].append(ref)
            if ref not in footprints:
                continue
            fp = footprints[ref]
            if comp["footprint"] != fp["footprint"]:
                report["footprint_mismatches"].append({"ref": ref,
                    "schematic": comp["footprint"], "pcb": fp["footprint"]})
            if comp["value"] != fp["value"]:
                report["value_mismatches"].append({"ref": ref,
                    "schematic": comp["value"], "pcb": fp["value"]})
            missing = comp["pins"].keys() - fp["pads"].keys()
            # Fresh KiCad exports include NC nodes. No unexplained numbered pads
            # are allowed; repeated physical pads with a legitimate number are OK.
            extra = fp["pads"].keys() - comp["pins"].keys()
            if comp["dnp"] != fp["dnp"]:
                report["dnp_mismatches"].append({"ref": ref,
                    "schematic": comp["dnp"], "pcb": fp["dnp"]})
            if missing or extra:
                report["pin_mismatches"].append({"ref": ref,
                    "missing_pads": sorted(missing), "extra_pads": sorted(extra)})
            for pin in sorted(comp["pins"].keys() & fp["pads"].keys()):
                expected = comp["pins"][pin]
                actual = fp["pads"][pin]
                if any(name != expected for name in actual):
                    report["net_mismatches"].append({"ref": ref, "pin": pin,
                        "schematic_net": expected, "pcb_nets": actual})
        issues = ["duplicate_references", "missing_on_pcb", "extra_on_pcb",
                  "unassigned_footprints", "footprint_mismatches", "pin_mismatches",
                  "net_mismatches", "value_mismatches", "dnp_mismatches"]
        report["passed"] = not any(report[key] for key in issues)
        return report
    return SimpleNamespace(**locals())

def corners_api():
    """Audit exposed degree-two 90-degree PCB bends using native KiCad geometry.

    Run with KiCad's pcbnew-capable Python. Pad/via anchors and sub-micron
    router quantization stubs are reported separately, not treated as free bends.
    T junctions are not bends and are outside this check's scope.
    """

    import argparse
    import collections
    import json
    import math
    from pathlib import Path



    def audit(board):
        import pcbnew as p

        endpoints = collections.defaultdict(list)
        for track in board.GetTracks():
            if type(track) != p.PCB_TRACK:
                continue
            for a, b in [(track.GetStart(), track.GetEnd()),
                         (track.GetEnd(), track.GetStart())]:
                endpoints[track.GetLayer(), a.x, a.y, track.GetNetCode()].append(
                    (track, b.x - a.x, b.y - a.y)
                )
        anchors = [pad for fp in board.GetFootprints() for pad in fp.Pads()]
        anchors += [t for t in board.GetTracks() if isinstance(t, p.PCB_VIA)]
        rows = []
        for (layer, x, y, net), tracks in endpoints.items():
            if len(tracks) != 2:
                continue
            (_, ux, uy), (_, vx, vy) = tracks
            lengths = [math.hypot(ux, uy), math.hypot(vx, vy)]
            if not min(lengths) or abs(ux * vx + uy * vy) > 1e-5 * math.prod(lengths):
                continue
            point = p.VECTOR2I(x, y)
            if min(lengths) < p.FromMM(0.001):
                category = "sub_micron_stub"
            elif any(a.IsOnLayer(layer) and a.HitTest(point) for a in anchors):
                category = "pad_or_via_anchor"
            else:
                category = "exposed_bend"
            rows.append({"layer": board.GetLayerName(layer), "x_mm": p.ToMM(x),
                         "y_mm": p.ToMM(y), "net": tracks[0][0].GetNetname(),
                         "category": category})
        return rows
    return SimpleNamespace(**locals())


def check_board(project, netlist=None):
    from .report import Finding
    project.require_board()
    if netlist is None:
        return [Finding("pcb.parity", "NOT_RUN", "Fresh native netlist required")]
    report = parity_api().audit_text(Path(netlist).read_text(encoding="utf-8"), project.board.read_text(encoding="utf-8"), set(project.parameters.get("mechanical_refs", [])))
    # Empty exports cannot prove parity, even for a deliberately empty board.
    valid = report["passed"] and report["schematic_components"] > 0 and report["schematic_nets"] > 0
    return [Finding("pcb.parity", "PASS" if valid else "FAIL", "Physical pin/net/footprint/value/DNP parity", report)]
