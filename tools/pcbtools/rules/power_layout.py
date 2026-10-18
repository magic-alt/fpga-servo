"""Grouped rule families; explicit contexts and no import-time checks."""
from types import SimpleNamespace


def reserved_ground_api():
    """Audit explicitly reserved copper layers across the entire native board.

    Foreign through-vias make antipads, not routed plane tracks. Rule areas are
    constraints, not copper. Neither exception permits a foreign track, arc or
    copper zone. Configuration is mandatory only for projects selecting this
    rule family; layer and net names are supplied by each project.
    """
    def audit(board, config):
        import pcbnew as p

        report = {'status':'FAIL', 'violations':[], 'reserved_layers':[],
                  'checked_tracks':0, 'checked_copper_zones':0,
                  'through_vias_not_plane_tracks':0, 'rule_areas_not_copper':0}
        if not isinstance(config, list) or not config:
            return report, ['Reserved ground layers require an explicit nonempty configuration']
        enabled = {board.GetLayerName(layer):layer
                   for layer in board.GetEnabledLayers().CuStack()}
        selected, errors = {}, []
        for row in config:
            if (not isinstance(row, dict) or set(row) != {'layer','net'}
                    or any(not isinstance(row[k], str) or not row[k].strip()
                           or any(c in row[k] for c in '*?[]') for k in ['layer','net'])):
                errors.append('Reserved ground layer requires exact layer and net names')
                continue
            if row['layer'] not in enabled:
                errors.append('Reserved ground layer is disabled, unknown or non-copper: '+row['layer'])
            elif enabled[row['layer']] in selected:
                errors.append('Duplicate reserved ground layer: '+row['layer'])
            else:
                selected[enabled[row['layer']]] = row['net']
                report['reserved_layers'].append(dict(row))
        if errors:
            return report, errors

        def reject(item, layer, kind):
            box = item.GetBoundingBox()
            row = {'uuid':item.m_Uuid.AsString(), 'kind':kind,
                   'layer':board.GetLayerName(layer), 'net':item.GetNetname(),
                   'required_net':selected[layer],
                   'copper_bounds_mm':[box.GetLeft()/1e6,box.GetTop()/1e6,
                                       box.GetRight()/1e6,box.GetBottom()/1e6]}
            report['violations'].append(row)
            errors.append(f"{row['uuid']}: {kind} net {row['net']!r} occupies reserved "
                          f"{row['layer']} (requires {row['required_net']!r})")

        for item in board.GetTracks():
            if isinstance(item, p.PCB_VIA):
                report['through_vias_not_plane_tracks'] += 1
                continue
            report['checked_tracks'] += 1
            layer = item.GetLayer()
            if layer in selected and item.GetNetname() != selected[layer]:
                reject(item, layer, 'arc' if isinstance(item,p.PCB_ARC) else 'track')
        # Native board.Zones() excludes footprint-owned zones. These can be
        # real copper as well as package keepouts, so inspect both containers
        # and deduplicate their native identities before classifying either.
        zones = list(board.Zones())
        for footprint in board.GetFootprints():
            zones.extend(footprint.Zones())
        seen_zone_uuids = set()
        for item in zones:
            uuid = item.m_Uuid.AsString()
            if uuid in seen_zone_uuids:
                continue
            seen_zone_uuids.add(uuid)
            if item.GetIsRuleArea():
                report['rule_areas_not_copper'] += 1
                continue
            report['checked_copper_zones'] += 1
            for layer in selected:
                if item.GetLayerSet().Contains(layer) and item.GetNetname() != selected[layer]:
                    reject(item, layer, 'copper_zone')
        report['status'] = 'FAIL' if errors else 'PASS'
        return report, errors

    def check_project(project, board):
        return audit(board, project.parameters.get('reserved_ground_layers'))[1]

    return SimpleNamespace(audit=audit, check_project=check_project)


def escape_api():
    """Verify exact package escape rules and physically bounded, pad-connected copper."""

    from pathlib import Path
    import argparse, re, sys
    from pcbtools.kicad import extract_forms, head_string

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
    return SimpleNamespace(**locals())

def vendor_api():
    """Verify TI copper lands and bounded same-package pad rules, not release readiness."""

    from pathlib import Path
    import argparse
    import re
    from pcbtools.kicad import extract_forms, property_value, head_string
    from pcbtools.rules.power_layout import escape_api
    _family_check_pcb_escape = escape_api()
    check_escape_rules = _family_check_pcb_escape.check_rules

    LANDS = {}
    for ref in ("U8", "U9", "U10", "U20", "U26"):
        LANDS[ref] = ("TI_DCU0008A_VSSOP8_P0.5mm", (0.85, 0.30), 1.55, 0.50)
    LANDS["U18"] = ("TI_DDF0008A_SOT23_8_P0.65mm", (1.05, 0.45), 1.30, 0.65)
    LANDS["U15"] = ("TI_DDF0008A", (1.05, 0.45), 1.30, 0.65)
    for ref in ("U2", "U3", "U4", "U5"):
        LANDS[ref] = ("TI_D0008A_SOIC8_P1.27mm", (1.55, 0.60), 2.70, 1.27)
    INTERNAL_GAPS = {
        **{f"Q{i}": 0.60 for i in range(1, 9)},
        **{f"U{i}": 0.65 for i in (2, 3, 4, 5)},
        "U1": 0.25,
        "U6": 0.20,
        "U18": 0.20,
        "U15": 0.20,
    }


    def check(text):
        errors, found = [], set()
        for footprint in extract_forms(text, "footprint"):
            ref = property_value(footprint.text, "Reference")
            if ref not in LANDS:
                continue
            found.add(ref)
            name, size, x, pitch = LANDS[ref]
            if head_string(footprint.text, "footprint") != "fpga-servo:" + name:
                errors.append(ref + ": expected manufacturer land-pattern identifier")
            pads = extract_forms(footprint.text, "pad")
            if {head_string(p.text, "pad") for p in pads} != set("12345678") or len(
                pads
            ) != 8:
                errors.append(ref + ": expected physical pads 1..8 exactly once")
                continue
            for pad in pads:
                number = int(head_string(pad.text, "pad"))
                pos = re.search(r"\(at\s+([-\d.]+)\s+([-\d.]+)", pad.text)
                dimensions = re.search(r"\(size\s+([-\d.]+)\s+([-\d.]+)", pad.text)
                expected = (
                    (-x, -1.5 * pitch + pitch * (number - 1))
                    if number <= 4
                    else (x, 1.5 * pitch - pitch * (number - 5))
                )
                if not pos or any(
                    abs(float(v) - e) > 1e-6 for v, e in zip(pos.groups(), expected)
                ):
                    errors.append(
                        f"{ref}.{number}: pad center differs from manufacturer lands"
                    )
                if not dimensions or any(
                    abs(float(v) - e) > 1e-6 for v, e in zip(dimensions.groups(), size)
                ):
                    errors.append(
                        f"{ref}.{number}: copper land differs from manufacturer dimensions"
                    )
        errors.extend(ref + ": missing footprint" for ref in sorted(set(LANDS) - found))
        return errors


    def internal_pad_rule_errors(text, ref, gap):
        errors = []
        conditions = extract_forms(text, "condition")
        intended = f"A.Type == 'Pad' && B.Type == 'Pad' && A.Reference == '{ref}' && B.Reference == '{ref}'"
        if len(conditions) != 1 or head_string(conditions[0].text, "condition") != intended:
            errors.append(ref + ": internal clearance must apply only to two pads of this exact instance")
        minimum = re.search(r"\(constraint\s+clearance\s+\(min\s+([\d.]+)mm\)\)",text)
        if not minimum or abs(float(minimum[1])-gap)>1e-9:
            errors.append(ref + ": internal clearance differs from reviewed minimum")
        if re.search(r"\(severity\b",text):
            errors.append(ref + ": severity override is prohibited")
        if ref == 'U12':
            constraints = extract_forms(text,'constraint')
            if len(constraints)!=1 or re.sub(r'\s+',' ',constraints[0].text).strip()!='(constraint clearance (min 0.45mm))':
                errors.append('U12: require only the reviewed internal pad clearance constraint')
        return errors


    def check_internal_pad_rules(text):
        """Reject scope expansion to tracks/vias/other instances or reduced minima."""
        errors = []
        rules = extract_forms(text, "rule")
        escape_rules = [
            r for r in rules if head_string(r.text, "rule").endswith(" bounded pad escape")
        ]
        if escape_rules:
            errors.extend(check_escape_rules(text, required=False))
        rules = [r for r in rules if r not in escape_rules]
        from pcbtools.rules.adc_layout import classify_native_body_rules
        body_rules, body_errors = classify_native_body_rules(text)
        errors.extend(body_errors)
        rules = [r for r in rules if r not in body_rules]
        expected = {ref + " internal lands": ref for ref in INTERNAL_GAPS}
        names = [head_string(rule.text, "rule") for rule in rules]
        # Keep the historic sixteen required rules and their exact diagnostics.
        # U12 is independently mandatory only for the selected new DDA footprint.
        if 'U12 internal lands' in names:
            expected['U12 internal lands']='U12'
        if set(names) != set(expected) or len(names) != len(expected):
            errors.append(
                "internal pad rules: expected exactly the reviewed sixteen rules"
            )
        for rule in rules:
            name = head_string(rule.text, "rule")
            if name not in expected:
                continue
            ref = expected[name]
            errors.extend(internal_pad_rule_errors(rule.text,ref,.45 if ref=='U12' else INTERNAL_GAPS[ref]))
        return errors
    return SimpleNamespace(**locals())

def kelvin_api():
    """Prove two-terminal SMD Kelvin isolation using native KiCad copper polygons.

    Subtract the actual terminal land from the copper graph, then traverse from the
    INA input. That branch must contain no load pad, zone, or power-width track and
    must land at the shunt's inner half. DRC, thermal and PWM qualification are separate.
    """
    import argparse
    import collections
    import json
    from pathlib import Path
    from pcbtools.kicad import extract_forms, property_value, head_string


    def check_shunt_contract(board_text, symbol_text, embedded_text, footprint_text, *, include_board=True):
        errors = []
        sources = []
        for form in extract_forms(board_text, 'footprint') if include_board else []:
            ref = property_value(form.text, 'Reference')
            if ref in {'RSH1', 'RSH2', 'RSH3', 'RSH4'}:
                sources.append((ref, form.text, 'pad', 'jumper_pad_groups'))
                if head_string(form.text, 'footprint') != 'fpga-servo:HoYLR2512_Kelvin':
                    errors.append(ref + ': manufacturer SMD land required')
        if include_board and {x[0] for x in sources} != {'RSH1', 'RSH2', 'RSH3', 'RSH4'}:
            errors.append('All four two-terminal SMD shunts required')
        sources.append(('land library', footprint_text, 'pad', 'jumper_pad_groups'))
        for label, text in [('symbol library', symbol_text), ('embedded symbol', embedded_text)]:
            forms = [f.text for f in extract_forms(text, 'symbol')
                     if (head_string(f.text, 'symbol') or '').split(':')[-1] == 'SHUNT_5mR_SMD']
            if len(forms) != 1:
                errors.append(label + ': one SMD definition required')
            else:
                sources.append((label, forms[0], 'pin', 'jumper_pin_groups'))
        for label, text, kind, jumper in sources:
            numbers = [head_string(f.text, 'pad') if kind == 'pad' else
                       head_string(extract_forms(f.text, 'number')[0].text, 'number')
                       for f in extract_forms(text, kind)]
            if sorted(numbers) != ['1', '2'] or extract_forms(text, jumper):
                errors.append(label + ': exactly physical terminals 1/2, no internal jumper groups')
        return errors


    def audit(board):
        import pcbnew as p
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        rows, errors = [], []
        for phase, ref, amp in [('U', 'RSH1', 'U2'), ('V', 'RSH2', 'U3'), ('W', 'RSH3', 'U4'), ('BUS', 'RSH4', 'U5')]:
            for prefix, number, input_number in [('SW_', '1', '8'), ('PH_', '2', '1')]:
                name = ('/VBUS_PROT' if number == '1' else '/VBUS_BRIDGE') if phase == 'BUS' else '/' + prefix + phase
                expected = [ref + '.' + number, amp + '.' + input_number]
                pads = {v.GetNumber(): v for v in fps[ref].Pads()}
                if set(pads) != {'1', '2'}:
                    errors.append(ref + ': expected two physical pads')
                    rows.append({'net': name, 'expected_pads': expected, 'passed': False})
                    continue
                terminal = pads[number]
                other = pads['2' if number == '1' else '1']
                clip = p.SHAPE_POLY_SET()
                terminal.GetEffectiveShape(p.F_Cu).TransformToPolygon(clip, 100, p.ERROR_OUTSIDE)
                # A 1nm moat prevents polygon boundary-only contact reconnecting the land.
                clip.Inflate(1, p.CORNER_STRATEGY_ROUND_ALL_CORNERS, 100)
                nodes = [t for t in board.GetTracks() if t.GetNetname() == name]
                nodes += [v for f in board.GetFootprints() for v in f.Pads()
                          if v.GetNetname() == name and v != terminal]
                nodes += [z for z in board.Zones() if z.GetNetname() == name]
                shapes = []
                landings = set()
                for i, node in enumerate(nodes):
                    layers = {}
                    for layer in board.GetEnabledLayers().CuStack():
                        if not node.IsOnLayer(layer):
                            continue
                        poly = p.SHAPE_POLY_SET()
                        if isinstance(node, p.ZONE):
                            if not node.IsFilled():
                                errors.append(name + ': refill zones before Kelvin audit')
                                continue
                            if not node.HasFilledPolysForLayer(layer):
                                continue
                            poly = p.SHAPE_POLY_SET(node.GetFilledPolysList(layer))
                        else:
                            node.GetEffectiveShape(layer).TransformToPolygon(poly, 100, p.ERROR_OUTSIDE)
                        if layer == p.F_Cu:
                            if not isinstance(node, (p.PAD, p.ZONE, p.PCB_VIA)):
                                a, z = terminal.GetPosition(), other.GetPosition()
                                boundary = terminal.GetEffectiveShape(layer)
                                for inside, outside in [(node.GetStart(), node.GetEnd()), (node.GetEnd(), node.GetStart())]:
                                    if not boundary.Collide(inside) or boundary.Collide(outside):
                                        continue
                                    # Validate where the centerline LEAVES the actual land,
                                    # not the buried endpoint (which can conceal an outer pickup).
                                    lo, hi = 0.0, 1.0
                                    for _ in range(32):
                                        mid = (lo + hi) / 2
                                        point = p.VECTOR2I(round(inside.x + mid*(outside.x-inside.x)),
                                                          round(inside.y + mid*(outside.y-inside.y)))
                                        if boundary.Collide(point): lo = mid
                                        else: hi = mid
                                    ex = inside.x + lo*(outside.x-inside.x)
                                    ey = inside.y + lo*(outside.y-inside.y)
                                    inward = (ex-a.x)*(z.x-a.x)+(ey-a.y)*(z.y-a.y)
                                    if inward > (node.GetWidth()/2 + 1000) * ((z.x-a.x)**2 + (z.y-a.y)**2)**.5:
                                        landings.add(i)
                            poly.BooleanSubtract(clip)
                        if poly.OutlineCount():
                            layers[layer] = poly
                    shapes.append(layers)
                adjacent = [set() for _ in nodes]
                for i in range(len(nodes)):
                    for j in range(i):
                        if any(shapes[i][layer].Collide(shapes[j][layer])
                               for layer in shapes[i].keys() & shapes[j].keys()):
                            adjacent[i].add(j)
                            adjacent[j].add(i)
                def pad_name(node):
                    return (p.Cast_to_FOOTPRINT(node.GetParent()).GetReference()+'.'+node.GetNumber()
                            if isinstance(node, p.PAD) else None)
                origins = [i for i,n in enumerate(nodes) if pad_name(n) == expected[1]]
                seen = set(origins)
                queue = collections.deque(origins)
                while queue:
                    for j in adjacent[queue.popleft()]:
                        if j not in seen:
                            seen.add(j)
                            queue.append(j)
                actual = sorted(pad_name(nodes[i]) for i in seen if isinstance(nodes[i], p.PAD))
                zones = [i for i in seen if isinstance(nodes[i], p.ZONE)]
                wide = [i for i in seen if isinstance(nodes[i], p.PCB_TRACK)
                        and not isinstance(nodes[i], p.PCB_VIA) and nodes[i].GetWidth() > p.FromMM(.5)]
                # Arc terminal exits need curved intersection proof; fail closed until supported.
                arcs = [i for i in seen if isinstance(nodes[i], p.PCB_ARC)]
                ok = actual == [expected[1]] and bool(seen & landings) and not zones and not wide and not arcs
                if not ok:
                    errors.append(f'{name}: pads={actual}, inner pickup={bool(seen & landings)}, zones={len(zones)}, power tracks={len(wide)}, unsupported arcs={len(arcs)}')
                rows.append({'net': name, 'expected_pads': expected, 'actual_pads_outside_land': actual,
                             'inner_pickup': bool(seen & landings), 'passed': ok,
                             'copper_uuids': sorted(nodes[i].m_Uuid.AsString() for i in seen
                                                    if not isinstance(nodes[i], p.PAD))})
        return rows, errors
    return SimpleNamespace(**locals())

def constraints_api():
    """Mechanical and netclass regressions; not a fabrication-readiness certificate."""
    from pathlib import Path
    import argparse
    import json
    import re
    from pcbtools.kicad import extract_forms, property_value, parse_at
    from pcbtools.board import parity_api
    _family_check_pcb_parity = parity_api()
    field = _family_check_pcb_parity.field

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
    return SimpleNamespace(**locals())
