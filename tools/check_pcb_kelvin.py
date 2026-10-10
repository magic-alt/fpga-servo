"""Check physical Kelvin isolation with KiCad Python; DRC alone cannot prove it.

Run with the pcbnew-capable KiCad Python. The copper graph deliberately excludes
component-internal jumper edges: a sense branch must contain just the dedicated
shunt sense pad and the corresponding INA input pad.
"""

import argparse
import collections
import json
import re
from pathlib import Path
from kicad_native import extract_forms, property_value, head_string

ROOT = Path(__file__).resolve().parents[1]
PAIRS = {frozenset(("1", "3")), frozenset(("2", "4"))}


def check_internal_groups(board_text, symbol_text, embedded_text, footprint_text):
    errors = []
    sources = []
    for form in extract_forms(board_text, "footprint"):
        ref = property_value(form.text, "Reference")
        if ref in {"RSH1", "RSH2", "RSH3"}:
            sources.append((ref, form.text, "jumper_pad_groups"))
    if {ref for ref, _, _ in sources} != {"RSH1", "RSH2", "RSH3"}:
        errors.append("Expected all three four-terminal shunts")
    sources.append(("shunt land library", footprint_text, "jumper_pad_groups"))
    for label, text in [
        ("shunt symbol library", symbol_text),
        ("embedded shunt symbol", embedded_text),
    ]:
        forms = [
            s
            for s in extract_forms(text, "symbol")
            if (head_string(s.text, "symbol") or "").endswith("SHUNT_5mR")
        ]
        if len(forms) != 1:
            errors.append(label + ": expected exactly one definition")
        else:
            sources.append((label, forms[0].text, "jumper_pin_groups"))
    for label, text, key in sources:
        forms = extract_forms(text, key)
        groups = []
        if len(forms) == 1:
            groups = [
                frozenset(re.findall(r'"([^\"]+)"', group))
                for group in re.findall(r"\([^()]*\)", forms[0].text)
            ]
        if set(groups) != PAIRS or len(groups) != 2:
            errors.append(
                label + ": require manufacturer internal pairs 1/3 and 2/4 only"
            )
    return errors


def audit(board):
    import pcbnew as p

    rows, errors = [], []
    for phase, ref, amp in [
        ("U", "RSH1", "U2"),
        ("V", "RSH2", "U3"),
        ("W", "RSH3", "U4"),
    ]:
        for name, sense_number, input_number in [
            ("/SW_" + phase, "3", "8"),
            ("/PH_" + phase, "4", "1"),
        ]:
            nodes = [t for t in board.GetTracks() if t.GetNetname() == name]
            nodes.extend(
                v
                for f in board.GetFootprints()
                for v in f.Pads()
                if v.GetNetname() == name
            )
            adjacency = [set() for _ in nodes]
            for i, u in enumerate(nodes):
                for j in range(i):
                    v = nodes[j]
                    if any(
                        u.IsOnLayer(layer)
                        and v.IsOnLayer(layer)
                        and u.GetEffectiveShape(layer).Collide(
                            v.GetEffectiveShape(layer)
                        )
                        for layer in [p.F_Cu, p.B_Cu]
                    ):
                        adjacency[i].add(j)
                        adjacency[j].add(i)

            def pad_name(node):
                return (
                    p.Cast_to_FOOTPRINT(node.GetParent()).GetReference()
                    + "."
                    + node.GetNumber()
                    if isinstance(node, p.PAD)
                    else None
                )

            origin = next(
                i
                for i, node in enumerate(nodes)
                if pad_name(node) == ref + "." + sense_number
            )
            queue = collections.deque([origin])
            seen = {origin}
            while queue:
                for j in adjacency[queue.popleft()]:
                    if j not in seen:
                        seen.add(j)
                        queue.append(j)
            actual = sorted(
                pad_name(nodes[i]) for i in seen if isinstance(nodes[i], p.PAD)
            )
            expected = sorted([ref + "." + sense_number, amp + "." + input_number])
            ok = actual == expected
            if not ok:
                errors.append(
                    name
                    + ": sense copper touches "
                    + ", ".join(actual)
                    + "; expected only "
                    + ", ".join(expected)
                )
            rows.append(
                {
                    "net": name,
                    "expected_pads": expected,
                    "actual_pads": actual,
                    "passed": ok,
                    "copper_uuids": sorted(
                        nodes[i].m_Uuid.AsString()
                        for i in seen
                        if not isinstance(nodes[i], p.PAD)
                    ),
                }
            )
    return rows, errors


def main():
    import pcbnew as p

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "board",
        nargs="?",
        type=Path,
        default=ROOT / "hardware/ax7010_servo_reva.kicad_pcb",
    )
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    folder = args.board.parent
    errors = check_internal_groups(
        args.board.read_text(encoding="utf-8"),
        (folder / "ax7010_servo_reva.kicad_sym").read_text(encoding="utf-8"),
        (folder / "gate_inverter.kicad_sch").read_text(encoding="utf-8"),
        (folder / "fpga-servo.pretty/Ohmite_650_4T_P25.40x6.35mm.kicad_mod").read_text(
            encoding="utf-8"
        ),
    )
    rows, copper_errors = audit(p.LoadBoard(str(args.board)))
    errors.extend(copper_errors)
    if args.output:
        args.output.write_text(
            json.dumps(
                {
                    "board": str(args.board),
                    "passed": not errors,
                    "branches": rows,
                    "errors": errors,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    print(
        "KELVIN TOPOLOGY "
        + ("FAILED" if errors else "PASSED")
        + f': {sum(row["passed"] for row in rows)}/6 isolated sense branches'
    )
    for error in errors:
        print(" -", error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
