"""Export current procurement decisions without mutating historical evidence.

The authored BOM determines fitted references. Explicit selected overrides win;
a BOM mismatch is reported, never silently replaced by a historical candidate.
Stock and prices are dated Chinese storefront snapshots, not reservations/quotes.
"""
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'docs/sourcing'


def export(root=ROOT):
    source = root / 'docs/sourcing'
    decisions = json.loads((source / 'selected_overrides_2026-10-10.json').read_text())
    selected = decisions['refs']
    with (root / 'hardware/bom.csv').open(newline='') as handle:
        authored = {row['Ref']: row for row in csv.DictReader(handle)}
    excluded = dict(decisions.get('excluded_refs', {}))
    excluded.update({ref: 'Removed by final architecture' for ref in decisions['removed_refs']})
    fitted = {}
    for ref, row in authored.items():
        note = row.get('Status / note', '')
        if ref in excluded:
            continue
        if note.startswith('DNP'):
            excluded[ref] = 'DNP option'
        elif note.startswith('External'):
            excluded[ref] = 'External system interface'
        elif row.get('Package', '').startswith('TestPoint:TestPoint_Pad'):
            excluded[ref] = 'Bare PCB test pad; no purchased component'
        else:
            fitted[ref] = row
    groups = {}
    for ref, row in fitted.items():
        choice = selected.get(ref, {})
        primary = choice.get('primary', {})
        alternate = choice.get('alternate', {})
        # Never infer procurement qualification from a matching part elsewhere.
        # New references remain explicit unresolved until reviewed into overrides.
        matched = (primary.get('mpn') == row.get('MPN')
                   and primary.get('code') == row.get('LCSC'))
        footprint = choice.get('required_footprint')
        footprint_ok = not footprint or row.get('Package') == footprint
        stock = primary.get('stock')
        evidence_ok = (primary.get('mpn') and primary.get('code')
                       and primary.get('url', '').startswith('https://item.szlcsc.com/')
                       and primary.get('timestamp') and isinstance(stock, (int, float)))
        if not evidence_ok:
            disposition = 'UNRESOLVED_SOURCE_EVIDENCE'
        elif not matched or not footprint_ok:
            disposition = 'SELECTED_PENDING_BOM_OR_FOOTPRINT'
        elif not choice.get('source_qualified'):
            disposition = 'CANDIDATE_QUALIFICATION_OPEN'
        else:
            disposition = 'SOURCED_PROTOTYPE_ELIGIBLE'
        # Identical decisions aggregate fitted quantity before pack rounding.
        key = json.dumps([primary, alternate, choice.get('qualification'),
                          choice.get('alternate_qualification'), choice.get('notes'),
                          disposition, footprint], sort_keys=True, ensure_ascii=False)
        if key not in groups:
            groups[key] = {'refs': [], 'qty': 0, 'choice': choice,
                           'primary': primary, 'alternate': alternate,
                           'disposition': disposition, 'applied': []}
        group = groups[key]
        group['refs'].append(ref)
        group['qty'] += int(row.get('Qty') or 1)
        if matched and footprint_ok:
            group['applied'].append(ref)
    rows = []
    for group in groups.values():
        a, b, choice = group['primary'], group['alternate'], group['choice']
        need = math.ceil(group['qty'] * 5 * 1.2)
        multiple = a.get('multiple')
        minimum = a.get('minimum') or 1
        order = (math.ceil(max(need, int(minimum)) / int(multiple)) * int(multiple)
                 if multiple and int(multiple) > 0 else None)
        stock = a.get('stock')
        covers = order is not None and stock is not None and stock >= order
        disposition = group['disposition']
        if disposition == 'SOURCED_PROTOTYPE_ELIGIBLE' and not covers:
            disposition = 'SOURCED_CHECK_ORDER_MULTIPLE' if order is None else 'SOURCED_INSUFFICIENT_STOCK'
        rows.append({
            'Refs': ','.join(group['refs']), 'Disposition': disposition,
            'Candidate MPN': a.get('mpn') or 'UNRESOLVED', 'LCSC': a.get('code') or 'UNVERIFIED',
            'Manufacturer': a.get('manufacturer') or '', 'China stock snapshot': stock,
            'Stock timestamp UTC': a.get('timestamp'), '5 boards + 20%': need,
            'Candidate order multiple': multiple, 'Candidate order qty': order,
            'Stock covers candidate qty': covers, 'Displayed starting price CNY': a.get('price'),
            'Source': a.get('url'), 'OEM datasheet': a.get('datasheet'),
            'Qualification': choice.get('qualification', 'UNRESOLVED'),
            'Applied to schematic refs': ','.join(group['applied']),
            'Alternate candidate': b.get('mpn', ''), 'Alternate LCSC': b.get('code', ''),
            'Alternate China stock': b.get('stock'), 'Alternate stock timestamp UTC': b.get('timestamp'),
            'Alternate source': b.get('url'), 'Alternate qualification': choice.get('alternate_qualification', 'UNQUALIFIED'),
            'Notes': choice.get('notes', 'No exact source decision reviewed for this fitted reference.')})
    seen = [ref for group in groups.values() for ref in group['refs']]
    assert len(seen) == len(set(seen)) and set(seen) == set(fitted), 'Fitted coverage/duplicate failure'
    output = root / 'hardware/procurement_candidates.csv'
    with output.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row['Disposition'] for row in rows)
    print(f'Procurement export: {len(rows)} groups, {len(fitted)} fitted references; {dict(counts)}')
    pending = sorted(set(selected) - set(authored))
    print(f'Excluded non-purchased references: {dict(sorted(excluded.items()))}')
    print(f'Selected references absent from current BOM (not ordered): {pending}')
    return rows


if __name__ == '__main__':
    export()
