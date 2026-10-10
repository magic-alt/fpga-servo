"""Verify exact package escape rules and physically bounded, pad-connected copper."""

from pathlib import Path
import argparse, re, sys
from kicad_native import extract_forms, head_string

ROOT = Path(__file__).resolve().parents[1]
ESCAPES = {"U1": (0.25, (-4, 4.7, -4, 4)), "U18": (0.2, (-2.7, 2.7, -2, 2))}


def condition(ref):
    return f"A.memberOf('{ref}_pad_escape') && ((B.Type == 'Pad' && B.Reference == '{ref}') || B.memberOf('{ref}_pad_escape'))"


def check_rules(text, required=True):
    errors = []
    found = {}
    for rule in extract_forms(text, "rule"):
        name = head_string(rule.text, "rule")
        if not name.endswith(" bounded pad escape"):
            continue
        found[name] = found.get(name, 0) + 1
        rr = name.removesuffix(" bounded pad escape")
        if rr not in ESCAPES:
            errors.append("unreviewed escape " + rr)
            continue
        cond = extract_forms(rule.text, "condition")
        constraints = extract_forms(rule.text, "constraint")
        if len(cond) != 1 or head_string(cond[0].text, "condition") != condition(rr):
            errors.append(rr + ": escape scope expanded")
        gap = ESCAPES[rr][0]
        expected = f"(constraint clearance (min {gap}mm))"
        if (
            len(constraints) != 1
            or re.sub(r"\s+", " ", constraints[0].text).strip() != expected
        ):
            errors.append(rr + ": incorrect escape clearance")
        if extract_forms(rule.text, "severity"):
            errors.append(rr + ": forbidden severity override")
    expected = {rr + " bounded pad escape": 1 for rr in ESCAPES}
    if (required or found) and found != expected:
        errors.append("require exactly two reviewed escape rules")
    return errors


def audit(board):
    import pcbnew as p

    errors = []
    rows = []
    fs = {f.GetReference(): f for f in board.GetFootprints()}
    for rr, (gap, offset) in ESCAPES.items():
        center = fs[rr].GetPosition()
        x, y = p.ToMM(center.x), p.ToMM(center.y)
        box = (x + offset[0], x + offset[1], y + offset[2], y + offset[3])
        gs = [g for g in board.Groups() if g.GetName() == rr + "_pad_escape"]
        if len(gs) != 1:
            errors.append(rr + ": require exactly one native escape group")
            continue
        native = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
        ts = [native.get(t.m_Uuid.AsString(), t) for t in gs[0].GetItems()]
        pads = list(fs[rr].Pads())
        allowed = {v.GetNetCode() for v in pads}
        valid = []
        for t in ts:
            if (
                not isinstance(t, p.PCB_TRACK)
                or isinstance(t, p.PCB_VIA)
                and rr != "U1"
            ):
                errors.append(
                    rr + ": only short native tracks and reviewed U1 vias permitted"
                )
                continue
            valid.append(t)
            if t.GetNetCode() not in allowed or (
                not t.IsOnLayer(p.F_Cu) and not (rr == "U1" and t.IsOnLayer(p.B_Cu))
            ):
                errors.append(rr + ": foreign layer or net in escape")
            if isinstance(t, p.PCB_VIA):
                if (
                    not p.FromMM(0.5) <= t.GetWidth(p.F_Cu) <= p.FromMM(0.6)
                    or t.GetDrillValue() != p.FromMM(0.3)
                    or not t.IsOnLayer(p.B_Cu)
                ):
                    errors.append(
                        rr + ": only .5.. .6 mm / .3 mm through vias permitted"
                    )
            elif t.GetLayer() not in (
                [p.F_Cu, p.B_Cu] if rr == "U1" else [p.F_Cu]
            ) or not p.FromMM(0.2) <= t.GetWidth() <= p.FromMM(0.4):
                errors.append(
                    rr
                    + ": only reviewed copper layers and .2.. .4 mm escape tracks permitted"
                )
            if isinstance(t, p.PCB_VIA):
                vx, vy = p.ToMM(t.GetPosition().x), p.ToMM(t.GetPosition().y)
                radius = p.ToMM(t.GetWidth(p.F_Cu)) / 2
                if not (
                    box[0] <= vx - radius
                    and vx + radius <= box[1]
                    and box[2] <= vy - radius
                    and vy + radius <= box[3]
                ):
                    errors.append(
                        rr + ": via copper extends beyond bounded package region"
                    )
            for q in [t.GetStart(), t.GetEnd()]:
                x, y = p.ToMM(q.x), p.ToMM(q.y)
                if (
                    not box[0] - 0.0001 <= x <= box[1] + 0.0001
                    or not box[2] - 0.0001 <= y <= box[3] + 0.0001
                ):
                    errors.append(
                        rr + ": escape extends beyond reviewed package region"
                    )
        adjacency = [set() for t in valid]
        seen = set()
        for i, t in enumerate(valid):
            shape = t.GetEffectiveShape(p.F_Cu)
            if any(
                t.IsOnLayer(p.F_Cu)
                and t.GetNetCode() == pd.GetNetCode()
                and shape.Collide(pd.GetEffectiveShape(p.F_Cu))
                for pd in pads
            ):
                seen.add(i)
            for j in range(i):
                if t.GetNetCode() == valid[j].GetNetCode() and any(
                    t.IsOnLayer(l)
                    and valid[j].IsOnLayer(l)
                    and t.GetEffectiveShape(l).Collide(valid[j].GetEffectiveShape(l))
                    for l in [p.F_Cu, p.B_Cu]
                ):
                    adjacency[i].add(j)
                    adjacency[j].add(i)
        queue = list(seen)
        while queue:
            for j in adjacency[queue.pop()]:
                if j not in seen:
                    seen.add(j)
                    queue.append(j)
        if len(seen) != len(valid):
            errors.append(
                rr
                + ": detached group copper lacks a visible direct path to its own physical pad"
            )
        rows.append(
            {
                "reference": rr,
                "tracks": len(valid),
                "pad_connected": len(seen),
                "clearance": gap,
                "bounds_mm": box,
                "detached_uuids": [
                    valid[i].m_Uuid.AsString()
                    for i in range(len(valid))
                    if i not in seen
                ],
            }
        )
    return rows, errors


def main():
    import pcbnew as p, json

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "board",
        nargs="?",
        type=Path,
        default=ROOT / "hardware/ax7010_servo_reva.kicad_pcb",
    )
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    errors = check_rules(a.board.with_suffix(".kicad_dru").read_text(encoding="utf-8"))
    rows, ee = audit(p.LoadBoard(str(a.board)))
    errors += ee
    if a.output:
        a.output.write_text(
            json.dumps(
                {"passed": not errors, "groups": rows, "errors": errors}, indent=2
            )
        )
    print("PACKAGE ESCAPE " + ("FAILED" if errors else "PASSED"))
    for e in errors:
        print(" -", e)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
