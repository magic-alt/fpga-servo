"""Project-configured exports; authored inputs are never overwritten."""
from pathlib import Path
import csv
import re
import json
import math
from collections import Counter
from .schematic import discover_sheets
from .kicad import extract_forms, property_value, strip_form, run_native, portable_netlist
from .report import Finding, RunReport
from .project import ProjectError

def export_bom(project, output, cli="kicad-cli"):
    import xml.etree.ElementTree as ET
    from .kicad import read_xml_summary
    target=output/"bom-source.xml"
    r=run_native([cli,"sch","export","netlist","--format","kicadxml","--output",str(target),str(project.schematic)],project.root,180)
    if r["exit_code"]:
        raise RuntimeError("Native BOM export " + r["status"] + ": " + r.get("error",r.get("stderr","failed")))
    read_xml_summary(target)
    portable_netlist(target,project.schematic.relative_to(project.root).as_posix())
    components=ET.parse(target).getroot().findall("./components/comp")
    rows=[]
    for comp in components:
        fields={f.get("name"):f.text or "" for f in comp.findall("fields/field")}
        ref=comp.get("ref")
        mpn=fields.get("MPN") or "TBD"
        note="DNP; populate only after option review" if comp.find("property[@name='dnp']") is not None else "Fitted"
        if comp.find("property[@name='exclude_from_board']") is not None:
            note="External; NOT fitted to PCB"
            if fields.get("Holder_MPN"):note+="; required holder "+fields["Holder_MPN"]
        if mpn=="TBD":note+="; exact MPN / rating qualification open"
        rows.append({"Ref":ref,"Qty":1,"Value / Part":comp.findtext("value", ""),
                     "Manufacturer":fields.get("Manufacturer") or "TBD","MPN":mpn,
                     "Package":comp.findtext("footprint", ""),"LCSC":fields.get("LCSC") or "UNVERIFIED",
                     "Alternative MPN":fields.get("Alternative_MPN") or "UNQUALIFIED",
                     "Alternative LCSC":fields.get("Alternative_LCSC") or "UNVERIFIED",
                     "Alternative status":fields.get("Alternative_Status") or "OPEN",
                     "Sourcing status":fields.get("Sourcing_Status") or "OPEN",
                     "Function":fields.get("Description") or "See schematic","Status / note":note})
    rows.sort(key=lambda row:(re.sub(r"\d+","",row["Ref"]),tuple(int(n) for n in re.findall(r"\d+",row["Ref"])),row["Ref"]))
    with (output/"bom.csv").open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return len(rows)


def export_procurement(root, source, bom_path, output):
    source = Path(source)
    decisions = json.loads((source / 'selected_overrides_2026-10-10.json').read_text(encoding="utf-8"))
    selected = decisions['refs']
    with bom_path.open(newline='', encoding='utf-8') as handle:
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
    output = output / 'procurement_candidates.csv'
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row['Disposition'] for row in rows)
    print(f'Procurement export: {len(rows)} groups, {len(fitted)} fitted references; {dict(counts)}')
    pending = sorted(set(selected) - set(authored))
    print(f'Excluded non-purchased references: {dict(sorted(excluded.items()))}')
    print(f'Selected references absent from current BOM (not ordered): {pending}')
    return rows


def export_project(project, kind, output, tools):
    import tempfile
    from .verification import new_run_directory, save_run
    output = project.safe_output(output or project.output)
    out = new_run_directory(output)
    report = RunReport(project.id, [], {"output":str(out), "pcb_release":"BLOCKED"})
    try:
        if kind == "bom":
            count=export_bom(project,out,tools.get("kicad-cli","kicad-cli"))
            report.findings.append(Finding("export.bom","PASS",f"{count} components exported"))
        elif kind == "procurement":
            name=project.parameters.get("procurement_source")
            if not isinstance(name,str) or not name or project.bom is None:
                raise ProjectError("Procurement requires configured sourcing data and BOM")
            source=(project.root/name).resolve()
            if not source.is_relative_to(project.root) or not source.is_dir(): raise ProjectError("Invalid sourcing directory")
            rows=export_procurement(project.root,source,project.bom,out)
            report.findings.append(Finding("export.procurement","PASS",f"{len(rows)} historical sourcing groups; stock/price snapshots require refresh"))
        else:
            extension="xml" if kind=="netlist" else "pdf"
            target=out/("netlist."+extension)
            command=[tools.get("kicad-cli","kicad-cli"),"sch","export",kind]
            if kind=="netlist": command += ["--format","kicadxml"]
            r=run_native(command+["--output",str(target),str(project.schematic)],project.root,180)
            valid=r["exit_code"]==0 and target.is_file() and target.stat().st_size>0
            if valid and kind=="netlist":
                from .kicad import read_xml_summary
                read_xml_summary(target)
                portable_netlist(target,project.schematic.relative_to(project.root).as_posix())
            report.findings.append(Finding("export."+kind,"PASS" if valid else r["status"] if r["status"]!="PASS" else "FAIL", "Native export",r))
    except ProjectError:
        raise
    except Exception as exc:
        report.findings.append(Finding("export."+kind,"NOT_RUN" if "NOT_RUN" in str(exc) else "FAIL",f"{type(exc).__name__}: {exc}"))
    save_run(report,out)
    return report
