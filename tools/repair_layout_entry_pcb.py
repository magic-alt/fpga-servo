"""Limited native pcbnew repair for the reviewed layout-entry defects.

This is not a general F8 replacement or a router. Default is dry-run. It only
updates D1..4/U6/J3 physical pads, J1 confirmed metadata, and removes off-board
F1. Existing copper and mechanical objects are retained for separate review.
Run using KiCad's pcbnew-enabled Python after a fresh native netlist export.
"""
import argparse
import json
from pathlib import Path
import pcbnew
from kicad_native import extract_forms, head_string


def field(text, key):
    forms = extract_forms(text, key)
    return head_string(forms[0].text, key) if forms else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("netlist", type=Path)
    parser.add_argument("--board", type=Path, default=Path("hardware/ax7010_servo_reva.kicad_pcb"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    text = args.netlist.read_text(encoding="utf-8")
    components = {field(c.text, "ref"): c.text for c in extract_forms(text, "comp")}
    assert "F1" not in components and "J6" not in components
    expected = {}
    for net in extract_forms(text, "net"):
        name = field(net.text, "name")
        for node in extract_forms(net.text, "node"):
            expected[(field(node.text, "ref"), field(node.text, "pin"))] = name
    targets = {("D1", "1"): "/VBUS_PROT", ("D1", "2"): "/GND",
               ("J3", "1"): "/DC Input & Protection/VIN_FUSED"}
    for diode, phase in [("D2", "U"), ("D3", "V"), ("D4", "W")]:
        targets[(diode, "1")] = f"/Gate Driver {{slash}} Inverter/BST_{phase}"
        targets[(diode, "2")] = "/VDRV_12V"
    targets.update({("U6", str(pin)): "/GND" for pin in [*range(16, 23), *range(27, 33)]})
    for pin, name in targets.items():
        assert expected.get(pin) == name, f"Unreviewed target at {pin}: {expected.get(pin)}"
    board = pcbnew.LoadBoard(str(args.board))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    assert len(footprints) == len(board.GetFootprints()), "Duplicate references"
    mechanical = {r: (footprints[r].GetPosition().x, footprints[r].GetPosition().y)
                  for r in ["H1", "H2", "H3", "H4"]}
    net_objects = {str(n.GetNetname()): n for n in board.GetNetInfo().NetsByNetcode().values()}
    changes = []
    for ref in ["D1", "D2", "D3", "D4", "U6", "J3"]:
        identity = footprints[ref].GetFPID()
        actual_footprint = str(identity.GetLibNickname()) + ":" + str(identity.GetLibItemName())
        assert actual_footprint == field(components[ref], "footprint"), f"Unreviewed footprint: {ref}"
        for pad in footprints[ref].Pads():
            pin = pad.GetNumber()
            name = expected[(ref, pin)]
            old = pad.GetNetname()
            if str(old) == name:
                continue
            # Reject unrelated deltas rather than silently synchronizing them.
            allowed = (ref in ["D1", "D2", "D3", "D4"] or
                       (ref == "U6" and int(pin) in [*range(16, 23), *range(27, 33)]) or
                       (ref == "J3" and pin == "1"))
            assert allowed, f"Unexpected pad delta {ref}.{pin}: {old} -> {name}"
            assert name in net_objects, f"Missing target net: {name}"
            changes.append({"ref": ref, "pin": pin, "before": str(old), "after": name})
            pad.SetNet(net_objects[name])
    j1 = components["J1"]
    metadata = {}
    for prop in extract_forms(j1, "property"):
        key = field(prop.text, "name")
        if key in ["Board_Revision", "Board_Connector"]:
            value = field(prop.text, "value")
            assert value
            metadata[key] = value
            footprints["J1"].SetField(key, value)
            footprints["J1"].GetField(key).SetVisible(False)
    # Native .net fields use (field (name ...) value) in some versions;
    # require confirmed metadata rather than inventing a value on parse failure.
    assert metadata == {"Board_Revision": "ALINX AX7010 2022", "Board_Connector": "J10"}
    removed = []
    if "F1" in footprints:
        assert footprints["F1"].GetFPID().GetLibItemName() == "Fuse_2920_7451Metric"
        board.Remove(footprints["F1"])
        removed.append("F1")
    assert mechanical == {r: (footprints[r].GetPosition().x, footprints[r].GetPosition().y)
                          for r in mechanical}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    report = {"applied": args.apply, "physical_pad_changes": changes,
              "removed_off_board_references": removed,
              "j1_fields": {"Board_Revision": "ALINX AX7010 2022", "Board_Connector": "J10"},
              "mount_centers_unchanged": True, "routing_changed": False}
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
