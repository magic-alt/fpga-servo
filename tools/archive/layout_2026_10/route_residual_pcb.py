"""Route residual connections in an isolated candidate; native DRC is mandatory."""

import argparse, heapq, json, math, time, sys
from pathlib import Path
import pcbnew as p

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_pcb_kelvin import audit

ap = argparse.ArgumentParser()
ap.add_argument("board", type=Path)
ap.add_argument("drc", type=Path)
ap.add_argument("output", type=Path)
ap.add_argument("--only", default="")
ap.add_argument("--source-choice", type=int, default=0)
ap.add_argument("--source-pads", action="store_true")
ap.add_argument("--multi-source", action="store_true")
ap.add_argument("--rip-up", action="store_true")
ap.add_argument("--rip-front-only", action="store_true")
ap.add_argument("--rip-back-only", action="store_true")
ap.add_argument("--prefer-back", action="store_true")
ap.add_argument("--rip-gates", action="store_true")
ap.add_argument("--reserve-rpp", action="store_true")
ap.add_argument("--seconds", type=float, default=15)
ap.add_argument("--escape", action="store_true")
ap.add_argument("--ordinary", action="store_true")
ap.add_argument("--fine-gates", action="store_true")
ap.add_argument("--step", type=float, default=0.25)
a = ap.parse_args()
b = p.LoadBoard(str(a.board))
report = json.loads(a.drc.read_text(encoding="utf-8"))
savedpro = a.board.with_suffix(".kicad_pro").read_bytes()
items = {v.m_Uuid.AsString(): v for f in b.GetFootprints() for v in f.Pads()}
items.update({v.m_Uuid.AsString(): v for v in b.GetTracks()})
fs = {f.GetReference(): f for f in b.GetFootprints()}


def xy(v):
    return p.ToMM(v.x), p.ToMM(v.y)


def pt(v):
    return p.VECTOR2I(p.FromMM(v[0]), p.FromMM(v[1]))


def ref(v):
    return (
        p.Cast_to_FOOTPRINT(v.GetParent()).GetReference()
        if isinstance(v, p.PAD)
        else ""
    )


def clr(v):
    name = v.GetNetname()
    leaf = name.rsplit("/", 1)[-1]
    return (
        0.8
        if leaf
        in [
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
        ]
        else (
            0.25
            if leaf
            in [
                "VA_5V",
                "VBUS_ADC",
                "IU_ADC",
                "IV_ADC",
                "IW_ADC",
                "VDRV_12V",
                "GH_U",
                "GH_V",
                "GH_W",
                "GL_U",
                "GL_V",
                "GL_W",
                "BST_U",
                "BST_V",
                "BST_W",
            ]
            or name.startswith("Net-(Q")
            else 0.2
        )
    )


rows, errors = audit(b)
assert not errors, errors
kelvin = {uid for row in rows for uid in row["copper_uuids"]}
kelvinpads = {name for row in rows for name in row["expected_pads"]}


def isolated(v):
    return (
        v.m_Uuid.AsString() in kelvin
        or isinstance(v, p.PAD)
        and ref(v) + "." + v.GetNumber() in kelvinpads
    )


ripobs = {0: set(), 2: set()}
ripitems = {}
obs = {0: [], 2: []}
bins = {0: {}, 2: {}}
holes = []
groups = {g.GetName(): g for g in b.Groups()}
# Physical package escape regions; only same-package pads/escape groups get local spacing.
esc = {}
for rr, gap, offset in [
    ("U1", 0.25, (-4, 4.7, -4, 4)),
    ("U18", 0.2, (-2.7, 2.7, -2, 2)),
]:
    x, y = xy(fs[rr].GetPosition())
    esc[rr] = (gap, (x + offset[0], x + offset[1], y + offset[2], y + offset[3]))


def inside(q, box):
    return (
        box[0] - 1e-6 <= q[0] <= box[1] + 1e-6
        and box[2] - 1e-6 <= q[1] <= box[3] + 1e-6
    )


def eroute(points, net=None, radius=0):
    if not a.escape:
        return None
    for rr, (gap, box) in esc.items():
        if (net is None or net in {v.GetNetCode() for v in fs[rr].Pads()}) and all(
            inside((q[0] - radius, q[1] - radius), box)
            and inside((q[0] + radius, q[1] + radius), box)
            for q in points
        ):
            return rr
    return None


def addobs(v):
    nc = -v.GetNetCode() if isolated(v) else v.GetNetCode()
    group = v.GetParentGroup()
    gr = group.GetName() if group else ""
    for l in [0, 2]:
        if not v.IsOnLayer(l):
            continue
        idx = len(obs[l])
        if (
            a.rip_up
            and (not a.rip_front_only or l == 0)
            and (not a.rip_back_only or l == 2)
            and isinstance(v, p.PCB_TRACK)
            and not isinstance(v, p.PCB_VIA)
            and not isolated(v)
            and v.GetNetname().rsplit("/", 1)[-1] != "GND"
            and not gr.endswith("_pad_escape")
            and p.ToMM(v.GetWidth()) <= 0.4
            and clr(v) <= 0.25
            and (
                a.rip_gates
                or not (
                    v.GetNetname().rsplit("/", 1)[-1].startswith(("GH_", "GL_", "BST_"))
                    or v.GetNetname().startswith("Net-(Q")
                )
            )
        ):
            ripobs[l].add(idx)
            ripitems[(l, idx)] = v
        obs[l].append((nc, clr(v), v.GetEffectiveShape(l), ref(v), gr))
        bb = v.GetBoundingBox()
        x, y = xy(bb.GetPosition())
        z, w = xy(bb.GetEnd())
        for ix in range(math.floor((x - 1.5) / 3), math.floor((z + 1.5) / 3) + 1):
            for iy in range(math.floor((y - 1.5) / 3), math.floor((w + 1.5) / 3) + 1):
                bins[l].setdefault((ix, iy), set()).add(idx)


for v in items.values():
    addobs(v)
for v in b.GetTracks():
    if isinstance(v, p.PCB_VIA):
        holes.append((xy(v.GetPosition()), p.ToMM(v.GetDrillValue()) / 2))
for f in b.GetFootprints():
    for v in f.Pads():
        if v.GetAttribute() in [p.PAD_ATTRIB_PTH, p.PAD_ATTRIB_NPTH]:
            holes.append((xy(v.GetPosition()), max(xy(v.GetDrillSize())) / 2))
if a.reserve_rpp:
    reserved_fp = p.FOOTPRINT(b)
    reserved_fp.SetReference("RESERVED_RPP_CURRENT_BRIDGE")
    reserved_pad = p.PAD(reserved_fp)
    reserved_pad.SetNet(b.FindNet("/DC Input & Protection/RPP_SRC"))
    reserved_pad.SetPosition(pt((103.5, 20.025)))
    reserved_pad.SetSize(pt((6.5, 5.25)))
    reserved_pad.SetShape(p.PAD_SHAPE_RECT)
    reserved_pad.SetAttribute(p.PAD_ATTRIB_SMD)
    reserved_layers = p.LSET()
    reserved_layers.AddLayer(p.F_Cu)
    reserved_pad.SetLayerSet(reserved_layers)
    addobs(reserved_pad)


def track(x, y, n, l, w):
    t = p.PCB_TRACK(b)
    t.SetStart(pt(x))
    t.SetEnd(pt(y))
    t.SetNetCode(n)
    t.SetLayer(l)
    t.SetWidth(p.FromMM(w))
    return t


def clear(v, n, c, l, points, w, allow=True):
    if any(
        q[0] < 2.3 + w / 2
        or q[0] > 131.7 - w / 2
        or q[1] < 2.3 + w / 2
        or q[1] > 96.7 - w / 2
        for q in points
    ):
        return False
    ids = set()
    for ix in range(
        math.floor((min(q[0] for q in points) - w / 2) / 3),
        math.floor((max(q[0] for q in points) + w / 2) / 3) + 1,
    ):
        for iy in range(
            math.floor((min(q[1] for q in points) - w / 2) / 3),
            math.floor((max(q[1] for q in points) + w / 2) / 3) + 1,
        ):
            ids.update(bins[l].get((ix, iy), ()))
    sh = v.GetEffectiveShape(l)
    rr = (
        eroute(points, n)
        if allow
        and isinstance(v, p.PCB_TRACK)
        and (
            (
                not isinstance(v, p.PCB_VIA)
                and (l == p.F_Cu or eroute(points, n) == "U1")
            )
            or (isinstance(v, p.PCB_VIA) and eroute(points, n, w / 2) == "U1")
        )
        else None
    )
    for idx in ids:
        if idx in ripobs[l]:
            continue
        nc, gap, s, r, g = obs[l][idx]
        if nc == n:
            continue
        distance = (
            esc[rr][0] if rr and (r == rr or g == rr + "_pad_escape") else max(c, gap)
        )
        if s.Collide(sh, p.FromMM(max(0, distance - 0.0001))):
            return False
    return True


def via(q, n, c, diam=0.5, drill=0.3):
    v = p.PCB_VIA(b)
    v.SetPosition(pt(q))
    v.SetWidth(p.FromMM(diam))
    v.SetDrill(p.FromMM(drill))
    v.SetViaType(p.VIATYPE_THROUGH)
    v.SetLayerPair(0, 2)
    v.SetNetCode(n)
    if any(math.dist(q, h) < r + drill / 2 + 0.251 for h, r in holes):
        return None
    if not all(clear(v, n, c, l, [q], diam, True) for l in [0, 2]):
        return None
    return v


def ends(v, other):
    if isinstance(v, p.PCB_TRACK) and not isinstance(v, p.PCB_VIA):
        x, y = xy(v.GetStart()), xy(v.GetEnd())
        z = xy(other.GetPosition())
        dx, dy = y[0] - x[0], y[1] - x[1]
        d = dx * dx + dy * dy
        t = max(0, min(1, ((z[0] - x[0]) * dx + (z[1] - x[1]) * dy) / d)) if d else 0
        return [(x[0] + t * dx, x[1] + t * dy), x, y]
    return [xy(v.GetPosition())]


def search(i, j, w, c, forced_goals=None, front_only=False):
    b.BuildConnectivity()
    native_items = {v.m_Uuid.AsString(): v for v in b.GetTracks()}
    native_items.update(
        {v.m_Uuid.AsString(): v for f in b.GetFootprints() for v in f.Pads()}
    )
    n = i.GetNetCode()
    localpads = [
        xy(v.GetPosition())
        for f in b.GetFootprints()
        for v in f.Pads()
        if v.GetNetCode() == n
    ]

    def width(x, y):
        return (
            0.2
            if w == 0.4
            and any(math.dist(x, z) < 1.5 and math.dist(y, z) < 1.5 for z in localpads)
            else w
        )

    conn = b.GetConnectivity()
    source = {i.m_Uuid.AsString(): i}
    if forced_goals is None:
        source = {i.m_Uuid.AsString(): i}
        sq = [i]
        while sq and len(source) < 1200:
            v = sq.pop()
            for z in conn.GetConnectedItems(v):
                z = native_items.get(z.m_Uuid.AsString(), z)
                if (
                    not isinstance(z, (p.PAD, p.PCB_TRACK))
                    or isolated(z)
                    or z.GetNetCode() != n
                ):
                    continue
                uid = z.m_Uuid.AsString()
                if uid not in source:
                    source[uid] = z
                    sq.append(z)
        sources = [
            v
            for v in source.values()
            if isinstance(v, p.PAD if a.source_pads else p.PCB_VIA)
        ] or list(source.values())
        i = sorted(
            sources,
            key=lambda v: min(
                math.dist(q, qq) for q in ends(v, j) for qq in ends(j, v)
            ),
        )[min(a.source_choice, len(sources) - 1)]
    orig = ends(i, j)[0]
    cluster = {j.m_Uuid.AsString(): j}
    queue = [j]
    while queue and len(cluster) < 700:
        v = queue.pop()
        for z in conn.GetConnectedItems(v):
            z = native_items.get(z.m_Uuid.AsString(), z)
            if (
                not isinstance(z, (p.PAD, p.PCB_TRACK))
                or isolated(z)
                or z.GetNetCode() != n
            ):
                continue
            uid = z.m_Uuid.AsString()
            if uid not in cluster:
                cluster[uid] = z
                queue.append(z)
    targets = sorted(
        cluster.values(), key=lambda v: min(math.dist(orig, q) for q in ends(v, i))
    )[:20]
    targets += [v for v in cluster.values() if isinstance(v, (p.PAD, p.PCB_VIA))]
    goals = list(
        {(q, l) for v in targets for q in ends(v, i) for l in [0, 2] if v.IsOnLayer(l)}
    )
    step = a.step
    if forced_goals is not None:
        goals = forced_goals

    def pos(k):
        return orig[0] + k[0] * step, orig[1] + k[1] * step

    def h(k):
        return min(math.dist(pos(k), q) + (0 if k[2] == l else 1.5) for q, l in goals)

    queue = []
    cost = {}
    prev = {}
    edgecache = {}
    vcache = {}
    nodes = 0
    deadline = time.monotonic() + a.seconds
    seeds = [(q, l) for q in ends(i, j)[:1] for l in [0, 2] if i.IsOnLayer(l)]
    if a.multi_source and forced_goals is None:
        seed_items = [v for v in source.values() if isinstance(v, (p.PAD, p.PCB_VIA))]
        seed_items += sorted(
            source.values(),
            key=lambda v: min(math.dist(q, z) for q in ends(v, j) for z in ends(j, v)),
        )[:30]
        seeds = [
            (q, l)
            for v in seed_items
            for q in ends(v, j)
            for l in [0, 2]
            if v.IsOnLayer(l)
        ]
    seedtails = {}
    for q, l in seeds:
        if front_only and l != 0:
            continue
        k = (round((q[0] - orig[0]) / step), round((q[1] - orig[1]) / step), l)
        end = pos(k)
        t = track(q, end, n, l, width(q, end))
        if not clear(t, n, c, l, [q, end], width(q, end)):
            continue
        distance = math.dist(q, end)
        if distance >= cost.get(k, 1e20):
            continue
        cost[k] = distance
        seedtails[k] = [t] if distance > 1e-5 else []
        heapq.heappush(queue, (h(k) + distance, distance, k))
    if a.multi_source:
        print(
            "SEARCH OUTLETS",
            len(seeds),
            len(cost),
            "goals",
            len(goals),
            "source vias",
            [xy(v.GetPosition()) for v in source.values() if isinstance(v, p.PCB_VIA)],
            flush=True,
        )
    goal = None
    tail = []
    while queue and time.monotonic() < deadline:
        _, g, k = heapq.heappop(queue)
        if g != cost.get(k):
            continue
        q = pos(k)
        nodes += 1
        for end, l in goals:
            if l == k[2] and math.dist(q, end) <= step * 1.5:
                ww = width(q, end)
                t = track(q, end, n, l, ww)
                if clear(t, n, c, l, [q, end], ww):
                    goal = k
                    tail = [t] if math.dist(q, end) > 1e-5 else []
                    break
        if goal is not None:
            break
        for dx, dy in [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
            (0, 0),
        ]:
            if front_only and not (dx or dy):
                continue
            z = (k[0] + dx, k[1] + dy, k[2] if dx or dy else 2 - k[2])
            q2 = pos(z)
            ng = g + (
                math.hypot(dx, dy) * step * (5 if a.prefer_back and k[2] == 0 else 1)
                if dx or dy
                else 3
            )
            if ng >= cost.get(z, 1e20):
                continue
            if not 2.3 < q2[0] < 131.7 or not 2.3 < q2[1] < 96.7:
                continue
            if dx or dy:
                key = (k, z)
                if key not in edgecache:
                    edgecache[key] = clear(
                        track(q, q2, n, k[2], width(q, q2)),
                        n,
                        c,
                        k[2],
                        [q, q2],
                        width(q, q2),
                    )
                if not edgecache[key]:
                    continue
            else:
                key = (k[0], k[1])
                if key not in vcache:
                    vcache[key] = (
                        via(
                            q,
                            n,
                            c,
                            1.6 if w >= 1 else 0.8 if w == 0.8 else 0.5,
                            0.8 if w >= 1 else 0.4 if w == 0.8 else 0.3,
                        )
                        is not None
                    )
                if not vcache[key]:
                    continue
            cost[z] = ng
            prev[z] = k
            heapq.heappush(queue, (ng + 2.5 * h(z), ng, z))
    print(
        "SEARCH",
        i.GetNetname(),
        ref(i),
        ref(j),
        "width",
        w,
        "nodes",
        nodes,
        "done",
        goal is not None,
        "frontier",
        len(queue),
        flush=True,
    )
    if goal is None:
        if a.only:
            a.output.with_suffix(".search.json").write_text(
                json.dumps(
                    {
                        "origin": orig,
                        "step": step,
                        "goals": goals,
                        "visited": list(cost),
                        "net": i.GetNetname(),
                    }
                )
            )
        return None
    ks = [goal]
    while ks[-1] in prev:
        ks.append(prev[ks[-1]])
    ks.reverse()
    ts = list(seedtails.get(ks[0], []))
    vs = []
    # Keep grid edges at region transitions so rule scope stays physically bounded.
    for u, v in zip(ks, ks[1:]):
        if u[2] != v[2]:
            vs.append(via(pos(u), n, c, 1.6 if w == 3 else 0.5, 0.8 if w == 3 else 0.3))
        else:
            ts.append(track(pos(u), pos(v), n, u[2], width(pos(u), pos(v))))
    ts += tail
    return ts, vs


added = []
for u in report["unconnected_items"]:
    pair = [items.get(v["uuid"]) for v in u["items"]]
    if len(pair) != 2 or any(v is None for v in pair):
        continue
    i, j = pair
    if ref(j).startswith("U") and not ref(i).startswith("U"):
        i, j = j, i
    name = i.GetNetname()
    if a.only and a.only not in name:
        continue
    if isolated(i) or isolated(j):
        continue
    if i.GetNetCode() != j.GetNetCode():
        continue
    # Main force current must retain 3mm; IC/bootstrap/testpoint branches are low current.
    c = max(clr(i), clr(j))
    if a.ordinary and c > 0.25:
        continue
    leaf = name.rsplit("/", 1)[-1]
    bias = any(
        ref(v).startswith(("U", "TP", "CBOOT", "RGS")) or ref(v) in ["C18", "C19"]
        for v in pair
    )
    bias = bias or any(
        isinstance(v, p.PCB_VIA)
        and p.ToMM(v.GetWidth(0)) <= 0.8
        or isinstance(v, p.PCB_TRACK)
        and not isinstance(v, p.PCB_VIA)
        and p.ToMM(v.GetWidth()) <= 0.3
        for v in pair
    )
    w = (
        3
        if c == 0.8 and not bias
        else (
            0.4
            if leaf.startswith(("GH_", "GL_", "BST_")) or name.startswith("Net-(Q")
            else 0.2
        )
    )
    if name == "/VBUS_PROT" and any(ref(v) in ["C3", "C4"] for v in pair):
        w = 1.0
    if name == "/VBUS_PROT" and any(ref(v) in ["C20", "C21"] for v in pair):
        w = 0.8
    if a.fine_gates and w == 0.4:
        w = 0.2
    found = search(i, j, w, c)
    if found is None:
        found = search(j, i, w, c)
    if found is None:
        continue
    ts, vs = found
    if a.rip_up:
        remove = {}
        for v in ts + vs:
            for l in [0, 2]:
                if not v.IsOnLayer(l):
                    continue
                for idx in ripobs[l]:
                    nc, gap, sh, rr, gr = obs[l][idx]
                    if nc != v.GetNetCode() and sh.Collide(
                        v.GetEffectiveShape(l), p.FromMM(max(c, gap) - 0.0001)
                    ):
                        o = ripitems[(l, idx)]
                        remove[o.m_Uuid.AsString()] = o
        existing = {o.m_Uuid.AsString() for o in b.GetTracks()}
        for uid, o in remove.items():
            if uid not in existing:
                continue
            if o.GetParentGroup():
                o.GetParentGroup().RemoveItem(o)
            b.Remove(o)
        print("RIP UP", name, len(remove), flush=True)
    for v in vs:
        assert v is not None
        b.Add(v)
        if (
            eroute([xy(v.GetPosition())], v.GetNetCode(), p.ToMM(v.GetWidth(0)) / 2)
            == "U1"
        ):
            key = "U1_pad_escape"
            if key not in groups:
                g = p.PCB_GROUP(b)
                g.SetName(key)
                b.Add(g)
                groups[key] = g
            groups[key].AddItem(v)
        addobs(v)
        holes.append((xy(v.GetPosition()), p.ToMM(v.GetDrillValue()) / 2))
    for t in ts:
        b.Add(t)
        rr = eroute([xy(t.GetStart()), xy(t.GetEnd())], t.GetNetCode())
        if rr and (t.GetLayer() == p.F_Cu or rr == "U1"):
            key = rr + "_pad_escape"
            if key not in groups:
                g = p.PCB_GROUP(b)
                g.SetName(key)
                b.Add(g)
                groups[key] = g
            groups[key].AddItem(t)
        addobs(t)
    added.append({"net": name, "segments": len(ts), "vias": len(vs), "width": w})
p.SaveBoard(str(a.output), b)
a.output.with_suffix(".kicad_pro").write_bytes(savedpro)
a.output.with_suffix(".routes.json").write_text(json.dumps(added, indent=2))
print("ADDED", added, flush=True)
