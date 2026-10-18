"""Project-configured exports; authored inputs are never overwritten."""
from pathlib import Path
import csv
import re
import json
import math
from collections import Counter
from .schematic import discover_sheets
from .kicad import extract_forms, head_string, property_value, strip_form, run_native, portable_netlist
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
        geometry = project.parameters.get("copper_only_refs", {})
        if ref in geometry:
            if comp.findtext("footprint", "") != geometry[ref] or mpn.upper() not in {"TBD", "UNVERIFIED", "UNQUALIFIED"}:
                raise ProjectError(f"{ref}: copper-only identity disagrees with native BOM")
            note = "PCB copper geometry; do not procure or place"
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


def export_assembly(project, output, cli=None):
    """Validate fresh native positions/XML, then exclude declared bare copper.

    This consumes native outputs from one frozen design; it never invents a
    centroid or substitutes a library origin. The complete inventory BOM stays
    separate from the list of purchased, fitted assembly components.
    """
    import hashlib
    import shutil
    import xml.etree.ElementTree as ET

    output = Path(output)
    geometry = project.parameters.get("copper_only_refs", {})
    if not isinstance(geometry, dict) or any(
            not isinstance(r, str) or not r or not isinstance(f, str) or not f
            for r, f in geometry.items()):
        raise ProjectError("copper_only_refs must map explicit references to full footprint IDs")
    native_xml = output / "bom-source.xml"
    components = {}
    for comp in ET.parse(native_xml).getroot().findall("components/comp"):
        ref = comp.get("ref")
        if not ref or ref in components:
            raise ProjectError("Duplicate or missing native BOM reference")
        components[ref] = {
            "value": comp.findtext("value", ""),
            "footprint": comp.findtext("footprint", ""),
            "mpn": comp.findtext("fields/field[@name='MPN']", ""),
            "flags": {p.get("name") for p in comp.findall("property")},
        }
    board = project.require_board()
    footprints = {}
    for form in extract_forms(board.read_text(encoding="utf-8"), "footprint"):
        ref = property_value(form.text, "Reference")
        if not ref or ref in footprints:
            raise ProjectError("Duplicate or missing PCB reference")
        flat = form.text
        for head in ("property", "pad", "fp_text", "fp_text_box", "fp_line", "fp_rect",
                     "fp_circle", "fp_arc", "fp_poly", "fp_curve", "zone", "group", "model"):
            flat = strip_form(flat, head)
        positions = extract_forms(flat, "at")
        layers = extract_forms(flat, "layer")
        if len(positions) != 1 or len(layers) != 1:
            raise ProjectError(f"{ref}: ambiguous native footprint pose")
        match = re.fullmatch(r"\(at\s+([-+\d.eE]+)\s+([-+\d.eE]+)(?:\s+([-+\d.eE]+))?\)", positions[0].text)
        layer = head_string(layers[0].text, "layer")
        if not match or layer not in {"F.Cu", "B.Cu"}:
            raise ProjectError(f"{ref}: unsupported native footprint pose")
        pose = [float(match[1]), -float(match[2]), float(match[3] or 0)]
        if not all(math.isfinite(v) for v in pose):
            raise ProjectError(f"{ref}: nonfinite native footprint pose")
        footprints[ref] = {"footprint": head_string(form.text, "footprint"),
                           "value": property_value(form.text, "Value"), "pose": pose,
                           "side": "top" if layer == "F.Cu" else "bottom"}
    unpurchased = {"", "TBD", "UNVERIFIED", "UNQUALIFIED"}
    for ref, fpid in geometry.items():
        if (ref not in components or ref not in footprints
                or components[ref]["footprint"] != fpid
                or footprints[ref]["footprint"] != fpid
                or components[ref]["mpn"].upper() not in unpurchased):
            raise ProjectError(f"{ref}: explicit copper-only identity is not proven")
    expected = {ref for ref, part in components.items() if ref not in geometry
                and not part["flags"] & {"dnp", "exclude_from_board", "exclude_from_bom"}}
    if not expected:
        raise ProjectError("Assembly contains no fitted purchased components")
    for ref in expected:
        part = components[ref]
        if part["mpn"].upper() in unpurchased:
            raise ProjectError(f"{ref}: fitted assembly MPN unqualified")
        if ref not in footprints or any(footprints[ref][k] != part[k] for k in ["value", "footprint"]):
            raise ProjectError(f"{ref}: native assembly identity mismatch")

    def read_csv(path, required):
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not set(required) <= set(reader.fieldnames):
                raise ProjectError("Incomplete native assembly CSV header")
            columns = reader.fieldnames
            rows = list(reader)
        refs = [r.get("Ref") for r in rows]
        if any(not ref for ref in refs) or len(set(refs)) != len(refs):
            raise ProjectError("Duplicate or missing assembly CSV reference")
        return columns, rows

    pos_path = output / "assembly.csv"
    pos_columns, positions = read_csv(pos_path, ["Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"])
    if {r["Ref"] for r in positions} - set(geometry) != expected:
        raise ProjectError("Native placement references disagree with fitted purchased BOM")
    for row in positions:
        ref = row["Ref"]
        if ref not in footprints:
            raise ProjectError(f"{ref}: placement has no actual footprint")
        fp = footprints[ref]
        if (row["Val"] != fp["value"] or row["Package"] != fp["footprint"].split(":")[-1]
                or row["Side"] != fp["side"]):
            raise ProjectError(f"{ref}: placement value/package/side mismatch")
        actual = [float(row[k]) for k in ["PosX", "PosY", "Rot"]]
        if (not all(math.isfinite(v) for v in actual)
                or any(abs(actual[i] - fp["pose"][i]) > 0.000002 for i in [0, 1])
                or abs((actual[2] - fp["pose"][2] + 180) % 360 - 180) > 0.0001):
            raise ProjectError(f"{ref}: placement centroid/orientation disagrees with native board")
    bom_path = output / "bom.csv"
    bom_columns, inventory = read_csv(bom_path, ["Ref", "Qty", "Value / Part", "MPN", "Package", "Status / note"])
    indexed = {r["Ref"]: r for r in inventory}
    if indexed.keys() != components.keys():
        raise ProjectError("Inventory BOM references disagree with complete fresh native XML")
    for ref in components:
        row, part = indexed[ref], components[ref]
        if (row["Value / Part"] != part["value"] or row["MPN"] != (part["mpn"] or "TBD")
                or row["Package"] != part["footprint"] or row["Qty"] != "1"):
            raise ProjectError(f"{ref}: inventory/native purchased identity mismatch")
    assembly_bom = [row for row in inventory if row["Ref"] in expected]
    assembly_positions = [row for row in positions if row["Ref"] in expected]
    for row in inventory:
        if row["Ref"] in geometry:
            row["Status / note"] = "PCB copper geometry; do not procure or place"
    raw = output / "assembly-native.csv"
    if raw.exists():
        raise ProjectError("Native placement evidence already exists; use a fresh export directory")
    shutil.copyfile(pos_path, raw)
    for path, columns, rows in [(pos_path, pos_columns, assembly_positions),
                                 (output / "assembly-bom.csv", bom_columns, assembly_bom),
                                 (bom_path, bom_columns, inventory)]:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
    proof = {"status": "PASS_AUTOMATED_ONLY", "purchased_fitted_refs": sorted(expected),
             "purchased_fitted_count": len(expected), "copper_only_refs": geometry,
             "native_pose_convention": "Native absolute PCB origin; X=x, Y=-y; native rotation modulo360; original side",
             "actual_board_sha256": hashlib.sha256(board.read_bytes()).hexdigest(),
             "native_xml_sha256": hashlib.sha256(native_xml.read_bytes()).hexdigest(),
             "unfiltered_native_positions_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
             "BOM_CPL_reference_sets_exact": True, "all_native_poses_and_identities_checked": True,
             "physical_orientation_and_assembly_process_review": "OPEN"}
    (output / "assembly-consistency.json").write_text(json.dumps(proof, indent=2)+"\n", encoding="utf-8")
    return proof


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
    if kind == "fabrication":
        from .manufacturing import export_fabrication
        report = export_fabrication(project, output, tools)
        save_run(report, Path(report.evidence["output"]))
        return report
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
