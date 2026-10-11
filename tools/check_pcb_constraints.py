"""Mechanical and netclass regressions; not a fabrication-readiness certificate."""
from pathlib import Path
import argparse
import json
import re
from kicad_native import extract_forms, property_value, parse_at
from check_pcb_parity import field

ROOT = Path(__file__).resolve().parents[1]
HOLES = {"H1": (5, 5), "H2": (129, 5), "H3": (5, 94), "H4": (129, 94)}


def check(board: str, project: dict, netlist: str) -> list[str]:
    errors = []
    fps = {property_value(x.text, "Reference"): x.text for x in extract_forms(board, "footprint")}
    for ref, xy in HOLES.items():
        f = fps.get(ref, "")
        if not f or parse_at(f) != xy:
            errors.append(f"{ref}: mounting-hole center changed or missing")
        for pad in extract_forms(f, "pad"):
            d = re.search(r"\(drill\s+([\d.]+)\)", pad.text)
            if not d or float(d.group(1)) < 3.2:
                errors.append(f"{ref}: M3 drill must be >=3.2mm")
    outlines = extract_forms(board, "gr_rect")
    if not any(re.search(r"\(start\s+2(?:\.0+)?\s+2(?:\.0+)?\)", x.text)
               and re.search(r"\(end\s+132(?:\.0+)?\s+97(?:\.0+)?\)", x.text)
               and '"Edge.Cuts"' in x.text for x in outlines):
        errors.append("130x95mm board outline moved or changed")
    for comp in extract_forms(netlist, "comp"):
        ref, fp = field(comp.text, "ref"), field(comp.text, "footprint")
        if not fp:
            errors.append(f"{ref}: footprint not assigned")
    classes = {x["name"]: x for x in project["net_settings"]["classes"]}
    patterns = project["net_settings"].get("netclass_patterns") or []
    assignments = {x["pattern"]: x["netclass"] for x in patterns}
    power = {"VIN_RAW", "VIN_FUSED", "RPP_SRC", "VBUS_PROT", "VBUS_BRIDGE", "SW_U", "SW_V", "SW_W", "PH_U", "PH_V", "PH_W"}
    gate = {"VDRV_12V", "BST_U", "BST_V", "BST_W", "GH_U", "GL_U", "GH_V", "GL_V", "GH_W", "GL_W"}
    for net in extract_forms(netlist, "net"):
        name = field(net.text, "name")
        leaf = name.rsplit("/", 1)[-1]
        required = "POWER" if leaf in power else "GATE" if leaf in gate else None
        if required and assignments.get(name) != required:
            errors.append(f"{name}: missing exact {required} netclass assignment")
    for required in ["POWER", "GATE", "ANALOG"]:
        if required not in classes:
            errors.append(f"missing netclass {required}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    args = parser.parse_args()
    errors = check((ROOT / "hardware/ax7010_servo_reva.kicad_pcb").read_text(encoding="utf-8"),
                   json.loads((ROOT / "hardware/ax7010_servo_reva.kicad_pro").read_text(encoding="utf-8")),
                   args.netlist.read_text(encoding="utf-8"))
    print("PCB CONSTRAINTS " + ("FAILED" if errors else "PASSED"))
    for error in errors:
        print(" -", error)
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
