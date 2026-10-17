"""Add collision-checked short connection candidates; run with KiCad Python.

The output must differ from the input. Native DRC remains authoritative.
"""

import argparse, json, math, heapq, time
from pathlib import Path
import pcbnew as p

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--fanout", action="store_true")
ap.add_argument("--ground-vias", action="store_true")
ap.add_argument("--bridge", action="store_true")
ap.add_argument("--astar", action="store_true")
ap.add_argument("board", type=Path)
ap.add_argument("drc", type=Path)
ap.add_argument("output", type=Path)
a = ap.parse_args()
assert a.board.resolve() != a.output.resolve()
b = p.LoadBoard(str(a.board))
report = json.loads(a.drc.read_text(encoding="utf-8"))


def mm(v):
    return p.ToMM(v)


def pt(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def xy(v):
    return (mm(v.x), mm(v.y))


items = {x.m_Uuid.AsString(): x for f in b.GetFootprints() for x in f.Pads()}
items.update({x.m_Uuid.AsString(): x for x in b.GetTracks()})
obs = {0: [], 2: []}
buckets = {0: {}, 2: {}}


def clearance(i):
    leaf = i.GetNetname().rsplit("/", 1)[-1]
    if leaf in {
        "VIN_RAW",
        "VIN_FUSED",
        "RPP_SRC",
        "VBUS_PROT",
        "SW_U",
        "SW_V",
        "SW_W",
        "PH_U",
        "PH_V",
        "PH_W",
    }:
        return 0.8
    if leaf in {
        "VA_5V",
        "VBUS_ADC",
        "IU_ADC",
        "IV_ADC",
        "IW_ADC",
        "VDRV_12V",
        "BST_U",
        "BST_V",
        "BST_W",
        "GH_U",
        "GH_V",
        "GH_W",
        "GL_U",
        "GL_V",
        "GL_W",
    } or leaf.startswith("Net-(Q"):
        return 0.25
    return 0.2


def add_obstacle(i):
    for layer in [p.F_Cu, p.B_Cu]:
        if not i.IsOnLayer(layer):
            continue
        shape = i.GetEffectiveShape(layer)
        box = i.GetBoundingBox()
        x1, y1 = xy(box.GetPosition())
        x2, y2 = xy(box.GetEnd())
        idx = len(obs[layer])
        obs[layer].append(
            (
                i.GetNetCode(),
                clearance(i),
                shape,
                (
                    p.Cast_to_FOOTPRINT(i.GetParent()).GetReference()
                    if isinstance(i, p.PAD)
                    else None
                ),
                i.GetParentGroup().GetName() if i.GetParentGroup() else None,
            )
        )
        for xx in range(math.floor((x1 - 1.2) / 4), math.floor((x2 + 1.2) / 4) + 1):
            for yy in range(math.floor((y1 - 1.2) / 4), math.floor((y2 + 1.2) / 4) + 1):
                buckets[layer].setdefault((xx, yy), set()).add(idx)


for i in items.values():
    add_obstacle(i)


def clear_shape(shape, net, clr, layer, points, width, escape=None):
    x1 = min(x[0] for x in points) - width / 2
    x2 = max(x[0] for x in points) + width / 2
    y1 = min(x[1] for x in points) - width / 2
    y2 = max(x[1] for x in points) + width / 2
    if x1 < 2.3 or x2 > 131.7 or y1 < 2.3 or y2 > 96.7:
        return False
    ids = set()
    for xx in range(math.floor(x1 / 4), math.floor(x2 / 4) + 1):
        for yy in range(math.floor(y1 / 4), math.floor(y2 / 4) + 1):
            ids.update(buckets[layer].get((xx, yy), ()))
    for idx in ids:
        nc, c, s, ref, group = obs[layer][idx]
        if nc == net:
            continue
        gap = (
            ESCAPES[escape]
            if escape and (ref == escape or group == escape + "_pad_escape")
            else max(c, clr)
        )
        if s.Collide(shape, p.FromMM(max(0, gap - 0.0005))):
            return False
    return True


def segment(x, y, width, net, layer):
    t = p.PCB_TRACK(b)
    t.SetStart(pt(*x))
    t.SetEnd(pt(*y))
    t.SetWidth(p.FromMM(width))
    t.SetLayer(layer)
    t.SetNetCode(net)
    return t


def paths(x, y):
    yield [x, y]
    yield [x, (x[0], y[1]), y]
    yield [x, (y[0], x[1]), y]
    dx = y[0] - x[0]
    dy = y[1] - x[1]
    d = min(abs(dx), abs(dy))
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    yield [x, (x[0] + sx * d, x[1] + sy * d), y]
    yield [x, (y[0] - sx * d, y[1] - sy * d), y]


def endpoints(i, other):
    if isinstance(i, p.PCB_TRACK) and not isinstance(i, p.PCB_VIA):
        x, y = xy(i.GetStart()), xy(i.GetEnd())
        v = (y[0] - x[0], y[1] - x[1])
        o = xy(other.GetPosition())
        d = v[0] ** 2 + v[1] ** 2
        t = (
            max(0, min(1, ((o[0] - x[0]) * v[0] + (o[1] - x[1]) * v[1]) / d))
            if d
            else 0
        )
        return [(x[0] + t * v[0], x[1] + t * v[1]), x, y]
    return [xy(i.GetPosition())]


def try_path(x, y, width, net, clr, layer):
    for path in paths(x, y):
        ts = [
            segment(u, v, width, net, layer)
            for u, v in zip(path, path[1:])
            if math.dist(u, v) > 0.00001
        ]
        if ts and all(
            clear_shape(
                t.GetEffectiveShape(layer),
                net,
                clr,
                layer,
                [xy(t.GetStart()), xy(t.GetEnd())],
                width,
            )
            for t in ts
        ):
            return ts
    return None


def astar_path(start, goal, width, net, clr, layer):
    step = 0.25
    deadline = time.monotonic() + 3
    limit = 8000
    bounds = (
        min(start[0], goal[0]) - 5,
        max(start[0], goal[0]) + 5,
        min(start[1], goal[1]) - 5,
        max(start[1], goal[1]) + 5,
    )

    def point(n):
        return (start[0] + n[0] * step, start[1] + n[1] * step)

    def heuristic(n):
        return math.dist(point(n), goal)

    queue = [(heuristic((0, 0)), 0, (0, 0))]
    cost = {(0, 0): 0}
    prev = {}
    visited = set()
    edges = {}
    while queue and len(visited) < limit and time.monotonic() < deadline:
        _, g, n = heapq.heappop(queue)
        if n in visited:
            continue
        visited.add(n)
        pos = point(n)
        if heuristic(n) < 0.7:
            finish = None
            for path in paths(pos, goal):
                ts = [
                    segment(u, v, width, net, layer)
                    for u, v in zip(path, path[1:])
                    if math.dist(u, v) > 0.00001
                ]
                if all(
                    clear_shape(
                        t.GetEffectiveShape(layer),
                        net,
                        clr,
                        layer,
                        [xy(t.GetStart()), xy(t.GetEnd())],
                        width,
                    )
                    for t in ts
                ):
                    finish = path
                    break
            if finish:
                nodes = [n]
                while nodes[-1] in prev:
                    nodes.append(prev[nodes[-1]])
                points = [point(k) for k in reversed(nodes)] + finish[1:]
                simple = [points[0]]
                for k in range(1, len(points) - 1):
                    u, v, w = simple[-1], points[k], points[k + 1]
                    if (
                        abs(
                            (v[0] - u[0]) * (w[1] - v[1])
                            - (v[1] - u[1]) * (w[0] - v[0])
                        )
                        > 1e-7
                    ):
                        simple.append(v)
                simple.append(points[-1])
                return [
                    segment(u, v, width, net, layer)
                    for u, v in zip(simple, simple[1:])
                    if math.dist(u, v) > 0.00001
                ]
        for dx, dy in [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        ]:
            nxt = (n[0] + dx, n[1] + dy)
            q = point(nxt)
            if nxt in visited or not (
                bounds[0] <= q[0] <= bounds[1] and bounds[2] <= q[1] <= bounds[3]
            ):
                continue
            ng = g + math.hypot(dx, dy) * step
            if ng >= cost.get(nxt, float("inf")):
                continue
            key = tuple(sorted([n, nxt]))
            if key not in edges:
                t = segment(pos, q, width, net, layer)
                edges[key] = clear_shape(
                    t.GetEffectiveShape(layer), net, clr, layer, [pos, q], width
                )
            if not edges[key]:
                continue
            cost[nxt] = ng
            prev[nxt] = n
            heapq.heappush(queue, (ng + heuristic(nxt), ng, nxt))
    return None


ESCAPES = {
    **{f"Q{i}": 0.6 for i in range(1, 9)},
    **{f"U{i}": 0.65 for i in [2, 3, 4]},
    "U1": 0.25,
    "U6": 0.2,
    "U18": 0.2,
}
added = []
if a.fanout:
    groups = {}
    seen = set()
    for u in report["unconnected_items"]:
        for record in u["items"]:
            pad = items.get(record["uuid"])
            if not isinstance(pad, p.PAD) or record["uuid"] in seen:
                continue
            seen.add(record["uuid"])
            f = p.Cast_to_FOOTPRINT(pad.GetParent())
            ref = f.GetReference()
            if ref not in ESCAPES:
                continue
            x = xy(pad.GetPosition())
            center = xy(f.GetPosition())
            dx = x[0] - center[0]
            dy = x[1] - center[1]
            angle = math.radians(pad.GetOrientationDegrees())
            axis = (
                (math.cos(angle), math.sin(angle))
                if not ref.startswith("Q")
                else (1, 0)
            )
            sign = 1 if dx * axis[0] + dy * axis[1] > 0 else -1
            direction = (round(axis[0] * sign), round(axis[1] * sign))
            width = 0.65 if ref.startswith("Q") else 0.2
            length = 1.9
            end = (x[0] + direction[0] * length, x[1] + direction[1] * length)
            t = segment(x, end, width, pad.GetNetCode(), p.F_Cu)
            if clear_shape(
                t.GetEffectiveShape(p.F_Cu),
                pad.GetNetCode(),
                clearance(pad),
                p.F_Cu,
                [x, end],
                width,
                ref,
            ):
                if ref not in groups:
                    g = p.PCB_GROUP(b)
                    g.SetName(ref + "_pad_escape")
                    b.Add(g)
                    groups[ref] = g
                b.Add(t)
                groups[ref].AddItem(t)
                add_obstacle(t)
                added.append(
                    {
                        "ref": ref,
                        "pin": pad.GetNumber(),
                        "net": pad.GetNetname(),
                        "segments": 1,
                        "start": x,
                        "end": end,
                        "width": width,
                    }
                )
if a.ground_vias:
    seen = set()
    ground_vias = [
        v
        for v in b.GetTracks()
        if isinstance(v, p.PCB_VIA) and v.GetNetname() == "/GND"
    ]
    holes = [
        (xy(v.GetPosition()), mm(v.GetDrillValue()) / 2)
        for v in b.GetTracks()
        if isinstance(v, p.PCB_VIA)
    ]
    holes += [
        (
            xy(pd.GetPosition()),
            max(mm(pd.GetDrillSize().x), mm(pd.GetDrillSize().y)) / 2,
        )
        for f in b.GetFootprints()
        for pd in f.Pads()
        if pd.GetAttribute() in [p.PAD_ATTRIB_PTH, p.PAD_ATTRIB_NPTH]
    ]
    smd = [
        x
        for x in items.values()
        if isinstance(x, p.PAD) and x.GetAttribute() == p.PAD_ATTRIB_SMD
    ]
    for u in report["unconnected_items"]:
        for record in u["items"]:
            item = items.get(record["uuid"])
            if (
                item is None
                or item.GetNetname() != "/GND"
                or record["uuid"] in seen
                or not item.IsOnLayer(p.F_Cu)
            ):
                continue
            seen.add(record["uuid"])
            x = xy(item.GetPosition())
            net = item.GetNetCode()
            found = None
            for old_via in sorted(
                ground_vias, key=lambda v: math.dist(x, xy(v.GetPosition()))
            ):
                pos = xy(old_via.GetPosition())
                dist = math.dist(x, pos)
                if 0.0001 < dist < 6:
                    ts = try_path(x, pos, 0.2, net, 0.2, p.F_Cu)
                    if ts:
                        found = (None, ts, pos)
                        break
            for radius in [] if found else [0.8, 1, 1.25, 1.5, 2, 2.5, 3, 4]:
                for dx, dy in [
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                    (0.7071, 0.7071),
                    (-0.7071, 0.7071),
                    (0.7071, -0.7071),
                    (-0.7071, -0.7071),
                ]:
                    pos = (x[0] + radius * dx, x[1] + radius * dy)
                    v = p.PCB_VIA(b)
                    v.SetPosition(pt(*pos))
                    v.SetWidth(p.FromMM(0.8))
                    v.SetDrill(p.FromMM(0.4))
                    v.SetViaType(p.VIATYPE_THROUGH)
                    v.SetLayerPair(p.F_Cu, p.B_Cu)
                    v.SetNetCode(net)
                    if any(math.dist(pos, h) < r + 0.2 + 0.251 for h, r in holes):
                        continue
                    if any(
                        pd.GetEffectiveShape(p.F_Cu).Collide(pt(*pos), p.FromMM(0.5))
                        for pd in smd
                    ):
                        continue
                    if not all(
                        clear_shape(
                            v.GetEffectiveShape(layer), net, 0.2, layer, [pos], 0.8
                        )
                        for layer in [p.F_Cu, p.B_Cu]
                    ):
                        continue
                    ts = try_path(x, pos, 0.2, net, 0.2, p.F_Cu)
                    if ts:
                        found = (v, ts, pos)
                        break
                if found:
                    break
            if found:
                v, ts, pos = found
                if v is not None:
                    b.Add(v)
                    add_obstacle(v)
                    holes.append((pos, 0.2))
                    ground_vias.append(v)
                for t in ts:
                    b.Add(t)
                    add_obstacle(t)
                added.append(
                    {
                        "net": "/GND",
                        "segments": len(ts),
                        "via": pos,
                        "start": x,
                        "end": pos,
                        "width": 0.2,
                    }
                )
if a.bridge:
    holes = [
        (xy(v.GetPosition()), mm(v.GetDrillValue()) / 2)
        for v in b.GetTracks()
        if isinstance(v, p.PCB_VIA)
    ]
    holes += [
        (
            xy(pd.GetPosition()),
            max(mm(pd.GetDrillSize().x), mm(pd.GetDrillSize().y)) / 2,
        )
        for f in b.GetFootprints()
        for pd in f.Pads()
        if pd.GetAttribute() in [p.PAD_ATTRIB_PTH, p.PAD_ATTRIB_NPTH]
    ]
    smd = [
        x
        for x in items.values()
        if isinstance(x, p.PAD) and x.GetAttribute() == p.PAD_ATTRIB_SMD
    ]

    def anchors(item, other):
        net = item.GetNetCode()
        clr = clearance(item)
        base = endpoints(item, other)[0]
        options = []
        searches = 0
        if item.IsOnLayer(p.B_Cu):
            options.extend((point, [], None) for point in endpoints(item, other))
        if not item.IsOnLayer(p.F_Cu):
            return options
        old_vias = [
            v
            for v in b.GetTracks()
            if isinstance(v, p.PCB_VIA)
            and v.GetNetCode() == net
            and math.dist(base, xy(v.GetPosition())) < 6
        ]
        for v in old_vias:
            pos = xy(v.GetPosition())
            ts = try_path(base, pos, 0.2, net, clr, p.F_Cu)
            if not ts and a.astar and searches < 3:
                searches += 1
                ts = astar_path(base, pos, 0.2, net, clr, p.F_Cu)
            if ts:
                options.append((pos, ts, None))
        for radius in [1, 1.5, 2, 2.5, 3, 4, 5]:
            for dx, dy in [
                (1, 0),
                (-1, 0),
                (0, 1),
                (0, -1),
                (0.7071, 0.7071),
                (-0.7071, 0.7071),
                (0.7071, -0.7071),
                (-0.7071, -0.7071),
            ]:
                pos = (base[0] + radius * dx, base[1] + radius * dy)
                if any(math.dist(pos, h) < r + 0.15 + 0.251 for h, r in holes):
                    continue
                if any(
                    pd.GetEffectiveShape(p.F_Cu).Collide(pt(*pos), p.FromMM(0.4))
                    for pd in smd
                ):
                    continue
                v = p.PCB_VIA(b)
                v.SetPosition(pt(*pos))
                v.SetWidth(p.FromMM(0.6))
                v.SetDrill(p.FromMM(0.3))
                v.SetViaType(p.VIATYPE_THROUGH)
                v.SetLayerPair(p.F_Cu, p.B_Cu)
                v.SetNetCode(net)
                if not all(
                    clear_shape(v.GetEffectiveShape(layer), net, clr, layer, [pos], 0.6)
                    for layer in [p.F_Cu, p.B_Cu]
                ):
                    continue
                ts = try_path(base, pos, 0.2, net, clr, p.F_Cu)
                if not ts and a.astar and searches < 3:
                    searches += 1
                    ts = astar_path(base, pos, 0.2, net, clr, p.F_Cu)
                if ts:
                    options.append((pos, ts, v))
        target = xy(other.GetPosition())
        return sorted(
            options, key=lambda x: math.dist(x[0], base) + math.dist(x[0], target)
        )[:12]

    for u in report["unconnected_items"]:
        pair = [items.get(x["uuid"]) for x in u["items"]]
        if len(pair) != 2 or any(x is None for x in pair):
            continue
        i, j = pair
        net = i.GetNetCode()
        clr = max(clearance(i), clearance(j))
        if i.GetNetCode() != j.GetNetCode() or clr > 0.25:
            continue
        aa = anchors(i, j)
        zz = anchors(j, i)
        found = None
        searched = 0
        for x, lead1, v1 in aa:
            for y, lead2, v2 in zz:
                if v1 is not None and v2 is not None and math.dist(x, y) < 0.551:
                    continue
                width = (
                    0.4
                    if i.GetNetname().rsplit("/", 1)[-1]
                    in {
                        "VDRV_12V",
                        "BST_U",
                        "BST_V",
                        "BST_W",
                        "GH_U",
                        "GH_V",
                        "GH_W",
                        "GL_U",
                        "GL_V",
                        "GL_W",
                    }
                    or i.GetNetname().startswith("Net-(Q")
                    else 0.25
                )
                ts = try_path(x, y, width, net, clr, p.B_Cu)
                if not ts and a.astar and searched < 3:
                    searched += 1
                    ts = astar_path(x, y, width, net, clr, p.B_Cu)
                if ts:
                    found = (lead1 + ts + lead2, v1, v2)
                    break
            if found:
                break
        if found:
            tracks, v1, v2 = found
            for via in [v1, v2]:
                if via is not None:
                    b.Add(via)
                    add_obstacle(via)
                    holes.append((xy(via.GetPosition()), 0.15))
            for t in tracks:
                b.Add(t)
                add_obstacle(t)
            added.append(
                {
                    "net": i.GetNetname(),
                    "segments": len(tracks),
                    "start": xy(tracks[0].GetStart()),
                    "end": xy(tracks[-1].GetEnd()),
                    "width": width,
                    "vias": sum(v is not None for v in [v1, v2]),
                }
            )
for u in [] if a.fanout or a.ground_vias or a.bridge else report["unconnected_items"]:
    pair = [items.get(x["uuid"]) for x in u["items"]]
    if len(pair) != 2 or any(x is None for x in pair):
        continue
    i, j = pair
    if i.GetNetCode() != j.GetNetCode():
        continue
    clr = max(clearance(i), clearance(j))
    net = i.GetNetCode()
    found = None
    for layer in [p.F_Cu, p.B_Cu]:
        if not (i.IsOnLayer(layer) and j.IsOnLayer(layer)):
            continue
        for x in endpoints(i, j):
            for y in endpoints(j, i):
                distance = math.dist(x, y)
                if distance > 12:
                    continue
                # Thin escapes are for low-current IC branches, never load-current copper.
                width = 0.2 if clr <= 0.25 else (3 if distance > 2 else 0.8)
                ts = try_path(x, y, width, net, clr, layer)
                if not ts and a.astar and clr <= 0.25:
                    ts = astar_path(x, y, width, net, clr, layer)
                if ts:
                    found = ts
                    break
            if found:
                break
        if found:
            break
    if found:
        for t in found:
            b.Add(t)
            add_obstacle(t)
        added.append(
            {
                "net": i.GetNetname(),
                "segments": len(found),
                "start": xy(found[0].GetStart()),
                "end": xy(found[-1].GetEnd()),
                "width": mm(found[0].GetWidth()),
            }
        )
p.SaveBoard(str(a.output), b)
a.output.with_suffix(".connections.json").write_text(
    json.dumps(added, indent=2), encoding="utf-8"
)
print("added checked paths", len(added), "segments", sum(x["segments"] for x in added))
