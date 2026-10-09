#!/usr/bin/env python3
"""Read-only KiCad XML-netlist / PCB structure audit.

Not a KiCad-native parser, ERC, DRC, or release qualification. All reported
pad/footprint details must be cross-checked against KiCad native schematic parity.

Usage:
  kicad-cli sch export netlist --format kicadxml -o artifacts/netlist.xml hardware/project.kicad_sch
  python scripts/board_parity_audit.py --netlist artifacts/netlist.xml --board hardware/project.kicad_pcb --output artifacts/parity.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


REF_RE = re.compile(r'\(property\s+"Reference"\s+"((?:\\.|[^"\\])*)"')
FP_RE = re.compile(r'^\(footprint\s+"((?:\\.|[^"\\])*)"')
NET_RE = re.compile(r'^\(net\s+(?:(\d+)\s+)?"((?:\\.|[^"\\])*)"')
PAD_RE = re.compile(r'\(pad\s+"([^"]*)"\s+(smd|thru_hole|np_thru_hole)')
VERSION_RE = re.compile(r'^\(kicad_pcb\s+\(version\s+(\d+)\)')


def top_level_forms(text: str):
    """Return immediate children of one kicad_pcb root; respect quoted escapes."""
    depth = 0
    start = None
    quoted = False
    escaped = False
    for i, char in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == '(':
            if depth == 1:
                start = i
            depth += 1
        elif char == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('Invalid S-expression: extra closing parenthesis')
            if depth == 1 and start is not None:
                yield text[start:i + 1]
                start = None
    if quoted or depth:
        raise ValueError('Invalid S-expression: unterminated root / string')


def get_head(form: str) -> str:
    m = re.match(r'^\(([\w.-]+)', form)
    return m.group(1) if m else ''


def nested_net_names(root: str):
    """Read old net tables and KiCad 10 pad/track/zone net names.

    Traverse parsed forms so quoted descriptions cannot create fake networks.
    """
    for form in top_level_forms(root):
        if get_head(form) == 'net':
            match = NET_RE.match(form)
            if match and match.group(2):
                yield match.group(2).replace('{slash}', '/')
        else:
            yield from nested_net_names(form)


def parse_board(path: Path) -> dict:
    raw = path.read_text(encoding='utf-8')
    if not raw.startswith('(kicad_pcb'):
        raise ValueError('Expected KiCad PCB S-expression')
    fps = {}
    # Keys are local diagnostic indices, not persistent KiCad net codes.
    net_names = dict(enumerate(dict.fromkeys(nested_net_names(raw)), start=1))
    c = Counter()
    for form in top_level_forms(raw):
        head = get_head(form)
        c[head] += 1
        if head == 'footprint':
            ref = REF_RE.search(form)
            name = FP_RE.search(form)
            if not ref:
                raise ValueError('Footprint without reference property')
            if ref.group(1) in fps:
                raise ValueError(f'Duplicate PCB reference {ref.group(1)}')
            fps[ref.group(1)] = {
                'lib_id': name.group(1) if name else '',
                'pads': len(PAD_RE.findall(form)),
                'pad_numbers': sorted(set(m[0] for m in PAD_RE.findall(form))),
                'has_schematic_link': bool(re.search(r'\((path|tstamp)\s+', form)),
            }
    version = VERSION_RE.match(raw)
    return {
        'pcb_file': str(path),
        'file_version': version.group(1) if version else '?',
        'footprints': fps,
        'net_names': net_names,
        'net_count': len(net_names),
        'tracks': c['segment'],
        'vias': c['via'],
        'zones': c['zone'],
        'edge_rectangles': sum('"Edge.Cuts"' in f for f in top_level_forms(raw) if get_head(f) == 'gr_rect'),
    }


def parse_netlist(path: Path) -> dict:
    root = ET.parse(path).getroot()
    if root.tag != 'export':
        raise ValueError(f'Expected KiCad XML netlist export, got {root.tag}')
    comps = {}
    for x in root.findall('./components/comp'):
        ref = x.get('ref')
        if not ref:
            continue
        if ref in comps:
            raise ValueError(f'Duplicate schematic ref {ref}')
        comps[ref] = {
            'value': x.findtext('value', default=''),
            'footprint': x.findtext('footprint', default='').strip(),
        }
    names = [x.get('name', '') for x in root.findall('./nets/net')]
    return {'components': comps, 'net_names': names, 'net_count': len(names)}


def audit(netlist: dict, board: dict) -> dict:
    sch_refs = set(netlist['components'])
    pcb_refs = set(board['footprints'])
    unmatched_pcb = sorted(pcb_refs - sch_refs)
    board_only_mechanical = [x for x in unmatched_pcb if re.fullmatch(r'H\d+', x)]
    board_orphans = [x for x in unmatched_pcb if x not in board_only_mechanical]
    missing = sorted(sch_refs - pcb_refs)
    empty_fp = sorted(ref for ref, info in netlist['components'].items() if not info['footprint'])
    net_gap = sorted(set(netlist['net_names']) - set(board['net_names'].values()) - {''})
    summary = {
        'source': 'static S-expression + KiCad XML netlist; NOT KiCad native parity or DRC',
        'schematic_components': len(sch_refs),
        'schematic_nets': netlist['net_count'],
        'pcb_footprints': len(pcb_refs),
        'pcb_matched_references': len(sch_refs & pcb_refs),
        'pcb_extra_refs': board_orphans,
        'pcb_only_mechanical': board_only_mechanical,
        'missing_pcb_references': missing,
        'missing_pcb_reference_count': len(missing),
        'schematic_symbols_missing_footprint': empty_fp,
        'pcb_nets': board['net_count'],
        'schematic_net_names_absent_from_board': net_gap,
        'pcb_tracks': board['tracks'],
        'pcb_vias': board['vias'],
        'pcb_zones': board['zones'],
        'pcb_file_version': board['file_version'],
        'footprints_missing_schematic_link': sorted(k for k, v in board['footprints'].items() if not v['has_schematic_link']),
        'board_footprints': board['footprints'],
        'blocking': bool(missing or board_orphans or empty_fp or net_gap),
        'caveats': [
            'Reference equality is only the first parity dimension: pad-net correspondence and UUID link require native KiCad F8/DRC --schematic-parity.',
            'Board-only mechanical H refs are not schematic mismatches if they have been reviewed.',
            'A nonzero blocking result is diagnostic; this script does not certify a zero result as fab ready.',
        ],
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--netlist', type=Path, required=True, help='KiCad XML netlist, use --format kicadxml')
    parser.add_argument('--board', type=Path, required=True, help='KiCad .kicad_pcb')
    parser.add_argument('--output', type=Path, required=True, help='Output JSON path')
    parser.add_argument('--strict', action='store_true', help='Exit nonzero if structural blockers found')
    args = parser.parse_args()
    info = audit(parse_netlist(args.netlist), parse_board(args.board))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    public = {k: v for k, v in info.items() if k not in ('board_footprints', 'missing_pcb_references', 'schematic_net_names_absent_from_board', 'footprints_missing_schematic_link')}
    print(json.dumps(public, ensure_ascii=False, indent=2))
    print(f'Details: {args.output}')
    return 2 if args.strict and info['blocking'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
