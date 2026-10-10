"""One-shot native pcbnew migration of the 20 obsolete baseline copper paths.

Run using KiCad's Python, with an untouched baseline and a distinct output.
Coordinates are a provisional placement/routing study, not current qualification.
Every old segment UUID is retained as the first segment of its replacement.
"""
import argparse
import json
from pathlib import Path

import pcbnew as p


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    assert args.source.resolve() != args.output.resolve()
    assert args.output.parent.resolve() != (Path(__file__).resolve().parents[1] / "hardware"), "Candidate outputs only; adoption requires separate review"
    b = p.LoadBoard(str(args.source))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    tracks = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
    assert len(tracks) == 20, "Requires the archived 20-segment baseline"
    nets = b.GetNetsByName()
    report = {"source": str(args.source), "placements": [], "paths": []}

    def xy(v):
        return [p.ToMM(v.x), p.ToMM(v.y)]

    def point(v):
        return p.VECTOR2I(p.FromMM(v[0]), p.FromMM(v[1]))

    def move(ref, x, y, angle):
        f = fps[ref]
        before = {"pos": xy(f.GetPosition()), "angle": f.GetOrientationDegrees()}
        f.SetOrientationDegrees(angle)
        f.SetPosition(point((x, y)))
        report["placements"].append({"ref": ref, "before": before,
                                     "after": {"pos": [x, y], "angle": angle}})

    def pad(ref, number):
        return next(x for x in fps[ref].Pads() if x.GetNumber() == str(number))

    def route(prefix, net, points, width, layer=p.F_Cu, endpoints=None):
        old = next(t for uid, t in tracks.items() if uid.startswith(prefix))
        record = {"uuid": old.m_Uuid.AsString(), "before": {
            "net": old.GetNetname(), "points": [xy(old.GetStart()), xy(old.GetEnd())],
            "width": p.ToMM(old.GetWidth()), "layer": old.GetLayerName()},
            "after": {"net": net, "points": points, "width": width,
                      "layer": b.GetLayerName(layer)}, "endpoints": endpoints}
        if endpoints:
            for endpoint, pos in zip(endpoints, (points[0], points[-1])):
                ref, pin = endpoint
                pd = pad(ref, pin)
                assert pd.GetNetname() == net, (endpoint, pd.GetNetname(), net)
                assert xy(pd.GetPosition()) == list(pos), (endpoint, xy(pd.GetPosition()), pos)
        for i, (start, end) in enumerate(zip(points, points[1:])):
            segment = old if i == 0 else p.PCB_TRACK(b)
            segment.SetNet(nets[net])
            segment.SetLayer(layer)
            segment.SetWidth(p.FromMM(width))
            segment.SetStart(point(start))
            segment.SetEnd(point(end))
            if i:
                b.Add(segment)
        report["paths"].append(record)

    def via(net, pos):
        v = p.PCB_VIA(b)
        v.SetPosition(point(pos))
        v.SetWidth(p.FromMM(0.8))
        v.SetDrill(p.FromMM(0.4))
        v.SetViaType(p.VIATYPE_THROUGH)
        v.SetLayerPair(p.F_Cu, p.B_Cu)
        v.SetNet(nets[net])
        b.Add(v)

    for i, y in enumerate((38, 60, 82), 2):
        move("U" + str(i), 96, y, 180)
        move("C" + str(41 + i), 91, y - 1.2, 90)
    move("J4", 123, 39, 270)
    # Put gate/source resistors on the gate side rather than in the VBUS fanout.
    for i in range(1, 7):
        qy = (25, 34, 47, 56, 69, 78)[i - 1]
        move("RGS" + str(i), 73, qy + (-4.5 if i % 2 else 4.5), 0)
        if i % 2:
            move("Q" + str(i), 72, qy, 180)

    move("RGS4", 75.5, 60.5, 0)
    move("R1", 120, 16, 0)
    move("D1", 126, 20, 90)

    for ref, pos in {"RGS1": (73, 19), "RGS2": (77, 38.5),
                     "RGS3": (78, 42.5), "RGS4": (80, 60.5),
                     "RGS5": (78, 64.5), "RG3": (75, 40.5),
                     "C80": (78, 63), "C43": (88.5, 36.8),
                     "C44": (88.5, 58.8), "C45": (88.5, 80.8)}.items():
        fps[ref].Reference().SetPosition(point(pos))
        fps[ref].Reference().SetTextAngle(p.EDA_ANGLE(0, p.DEGREES_T))
    for drawing in b.GetDrawings():
        if isinstance(drawing, p.PCB_TEXT):
            if drawing.GetText() == "POWER STAGE":
                drawing.SetPosition(point((113, 85)))
            elif "12..48V" in drawing.GetText():
                drawing.SetText(drawing.GetText().replace("12..48V", "24..48V"))

    # Independent Kelvin traces start at sense pins 3/4, never at force pins 1/2.
    for phase, off, ina, ids in (
        ("U", 0, "U2", ("865ca4f5", "f459d854")),
        ("V", 22, "U3", ("d2057202", "9df9ccf9")),
        ("W", 44, "U4", ("a7075abc", "8c0f991c")),
    ):
        sh = "RSH" + str(1 + off // 22)
        route(ids[0], "/SW_" + phase,
              [(83.3, 32.175 + off), (88, 32.175 + off),
               (88, 39.905 + off), (93.525, 39.905 + off)], .25,
              endpoints=[(sh, "3"), (ina, "8")])
        route(ids[1], "/PH_" + phase,
              [(108.7, 32.175 + off), (108.7, 39.905 + off),
               (98.475, 39.905 + off)], .25,
              endpoints=[(sh, "4"), (ina, "1")])

    for prefix, phase, off in (("49404cf4", "U", 0), ("889e1bc7", "V", 22),
                                ("0e756e4a", "W", 44)):
        route(prefix, "/SW_" + phase,
              [(74.825, 26.905 + off), (77.5, 26.905 + off),
               (77.5, 34 + off), (72.675, 34 + off)], .8,
              endpoints=[("Q" + str(1 + off // 11), "1"),
                         ("Q" + str(2 + off // 11), "5")])
        for points, width in (([(77.5, 26.905 + off), (78.58, 25.825 + off),
                                (83.3, 25.825 + off)], .8),
                              ([(74.825, 24.365 + off), (74.825, 26.905 + off)], .2)):
            for start, end in zip(points, points[1:]):
                t = p.PCB_TRACK(b)
                t.SetNet(nets["/SW_" + phase])
                t.SetLayer(p.F_Cu)
                t.SetWidth(p.FromMM(width))
                t.SetStart(point(start))
                t.SetEnd(point(end))
                b.Add(t)

    route("6000a16d", "/PH_U", [(108.7, 25.825), (116, 25.825),
          (123, 32.825), (123, 39)], 3, endpoints=[("RSH1", "2"), ("J4", "1")])
    route("1a764a18", "/PH_V", [(108.7, 47.825), (122.305, 47.825),
          (123, 48.52)], 3, endpoints=[("RSH2", "2"), ("J4", "2")])
    route("ce95a868", "/PH_W", [(108.7, 69.825), (116, 69.825),
          (123, 62.825), (123, 58.04)], 3, endpoints=[("RSH3", "2"), ("J4", "3")])

    # Power paths are provisional: widths/vias still require thermal qualification.
    for prefix, q, y in (("3630db16", "Q1", 25), ("8b13c195", "Q3", 47),
                          ("ed6a1e9a", "Q5", 69)):
        route(prefix, "/VBUS_PROT", [(81, 12), (73, 20), (73, y), (71.325, y)],
              2, p.B_Cu, endpoints=[("C1", "1"), (q, "5")])
        via("/VBUS_PROT", (71.325, y))
    route("95dc3ed7", "/VBUS_PROT", [(109.675, 20), (118, 20),
          (118, 7), (81, 7), (81, 12)], 2,
          endpoints=[("Q8", "5"), ("C1", "1")])

    route("a7a4f73f", "/GND", [(100.48, 11), (98, 13.48), (87.48, 13.48),
          (86, 12)], 2, p.B_Cu, endpoints=[("J3", "2"), ("C1", "2")])
    for prefix, q, y in (("d2f8c544", "Q2", 32.095),
                          ("402cbec6", "Q4", 54.095),
                          ("846beff3", "Q6", 76.095)):
        route(prefix, "/GND", [(86, 12), (86, 7), (65, 7), (65, y), (69.175, y)],
              2, p.B_Cu, endpoints=[("C1", "2"), (q, "1")])
        via("/GND", (69.175, y))

    zone = next(z for z in b.Zones()
                if z.m_Uuid.AsString() == "0121f506-5f9a-4ea2-8a2a-49c4664a8ec7")
    report["zone"] = {"uuid": zone.m_Uuid.AsString(), "before": zone.GetNetname(),
                      "after": "/GND", "outline_changed": False}
    assert zone.GetNetname() == "GND"
    zone.SetNet(nets["/GND"])
    assert len(report["paths"]) == 20
    report["copper"] = [dict(uuid=t.m_Uuid.AsString(), net=t.GetNetname(),
                             start=xy(t.GetStart()), end=xy(t.GetEnd()),
                             width=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t, p.PCB_VIA) else t.GetWidth()), layer=t.GetLayerName(),
                             kind="via" if isinstance(t, p.PCB_VIA) else "segment")
                         for t in b.GetTracks()]
    report["qualification"] = "PROVISIONAL: widths, via-in-pad process, return loops, thermal and dynamic safety OPEN"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    p.ZONE_FILLER(b).Fill(b.Zones())
    p.SaveBoard(str(args.output), b)
    args.output.with_suffix(".migration.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"paths": len(report["paths"]), "placements": len(report["placements"]),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
