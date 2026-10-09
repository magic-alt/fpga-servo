"""Compare a freshly exported KiCad netlist with physical PCB pad assignments.

No pcbnew dependency: usable in CI with Python 3.12. This proves graph parity,
not routing, package dimensions, current ratings or release readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from kicad_native import assert_balanced, extract_forms, head_string, property_value

ROOT = Path(__file__).resolve().parents[1]


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("board", nargs="?", type=Path,
                        default=ROOT / "hardware/ax7010_servo_reva.kicad_pcb")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_text(args.netlist.read_text(encoding="utf-8"),
                        args.board.read_text(encoding="utf-8"), {"H1", "H2", "H3", "H4"})
    if not report["schematic_components"] or not report["schematic_nets"]:
        report["passed"] = False
        report["invalid_source"] = ["empty netlist cannot prove parity"]
    if set(report["mechanical_preserved"]) != {"H1", "H2", "H3", "H4"}:
        report["passed"] = False
        report["missing_mechanics"] = sorted({"H1", "H2", "H3", "H4"} - set(report["mechanical_preserved"]))
    report["source_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (args.netlist, args.board)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PCB PARITY " + ("PASSED" if report["passed"] else "FAILED") +
          f": {report['schematic_components']} components / {report['schematic_nets']} nets / {report['pcb_footprints']} footprints")
    for key, value in report.items():
        if isinstance(value, list) and value and key != "mechanical_preserved":
            print(f" - {key}: {len(value)}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
