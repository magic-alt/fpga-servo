"""Prove two-terminal SMD Kelvin isolation using native KiCad copper polygons.

Subtract the actual terminal land from the copper graph, then traverse from the
INA input. That branch must contain no load pad, zone, or power-width track and
must land at the shunt's inner half. DRC, thermal and PWM qualification are separate.
"""
import argparse
import collections
import json
from pathlib import Path
from kicad_native import extract_forms, property_value, head_string
ROOT = Path(__file__).resolve().parents[1]


def check_shunt_contract(board_text, symbol_text, embedded_text, footprint_text):
    errors = []
    sources = []
    for form in extract_forms(board_text, 'footprint'):
        ref = property_value(form.text, 'Reference')
        if ref in {'RSH1', 'RSH2', 'RSH3', 'RSH4'}:
            sources.append((ref, form.text, 'pad', 'jumper_pad_groups'))
            if head_string(form.text, 'footprint') != 'fpga-servo:HoYLR2512_Kelvin':
                errors.append(ref + ': manufacturer SMD land required')
    if {x[0] for x in sources} != {'RSH1', 'RSH2', 'RSH3', 'RSH4'}:
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


def main():
    import pcbnew as p
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', nargs='?', type=Path, default=ROOT/'hardware/ax7010_servo_reva.kicad_pcb')
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    folder = args.board.parent
    errors = check_shunt_contract(args.board.read_text(),
        (folder/'ax7010_servo_reva.kicad_sym').read_text(),
        (folder/'gate_inverter.kicad_sch').read_text(),
        (folder/'fpga-servo.pretty/HoYLR2512_Kelvin.kicad_mod').read_text())
    rows, copper_errors = audit(p.LoadBoard(str(args.board)))
    errors.extend(copper_errors)
    if args.output:
        args.output.write_text(json.dumps({'board': str(args.board), 'passed': not errors,
                                          'branches': rows, 'errors': errors}, indent=2)+'\n')
    print('KELVIN TOPOLOGY '+('FAILED' if errors else 'PASSED')+f': {sum(r["passed"] for r in rows)}/8 independent inner-edge pickups')
    for e in errors: print(' -',e)
    return int(bool(errors))
if __name__ == '__main__':
    raise SystemExit(main())
