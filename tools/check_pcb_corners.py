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

ROOT = Path(__file__).resolve().parents[1]


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


def main():
    import pcbnew as p

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", nargs="?", type=Path,
                        default=ROOT / "hardware/ax7010_servo_reva.kicad_pcb")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = audit(p.LoadBoard(str(args.board)))
    counts = dict(collections.Counter(row["category"] for row in rows))
    failed = counts.get("exposed_bend", 0) > 0
    if args.output:
        args.output.write_text(json.dumps({"passed": not failed, "counts": counts,
                                          "corners": rows}, indent=2) + "\n")
    print("PCB CORNERS " + ("FAILED" if failed else "PASSED") + ": " + str(counts))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
