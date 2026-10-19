"""Source-bound manufacturing review packets, explicitly NOT an order release."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from .project import ProjectError
from .report import Finding
from .kicad import run_native
from .manufacturing import (GERBER_LAYERS, GERBER_NATIVE_SUFFIXES, check_native_settings,
                            check_prototype_inputs, design_source_hashes, freeze_design,
                            check_frozen_design, validate_fabrication_outputs, sha256)


def validate_pdf(path, expected_pages):
    data = Path(path).read_bytes()
    if not data.startswith(b'%PDF-') or not data.rstrip().endswith(b'%%EOF'):
        raise ProjectError('Invalid or truncated PDF header/EOF')
    try:
        from pypdf import PdfReader
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted or len(reader.pages) != expected_pages:
            raise ValueError('PDF encryption or page count mismatch')
        for page in reader.pages:
            if min(float(page.mediabox.width), float(page.mediabox.height)) <= 0:
                raise ValueError('PDF page has no physical extent')
            content = page.get_contents()
            if content is None or not content.get_data().strip():
                raise ValueError('Missing/blank PDF page stream')
    except ImportError as exc:
        raise ProjectError('pypdf is required for manufacturing-review export') from exc
    except Exception as exc:
        raise ProjectError('PDF structural validation failed: ' + str(exc)) from exc
    return {'pages': expected_pages, 'sha256': sha256(Path(path)),
            'streams_decoded': True, 'visual_review': 'REQUIRED_SEPARATELY'}


def check_cam_terminator(path):
    text = Path(path).read_text(encoding='utf-8-sig').strip()
    if not text.endswith('M02*'):
        raise ProjectError('Truncated Gerber: ' + Path(path).name)


def parse_decimal_drill(text, plated):
    """Strict reader for the explicitly requested KiCad metric decimal circular XNC.

    Reject slots/routing, units changes and undeclared tools rather than infer
    their geometry. Gerbonara independently parses/renders populated files too.
    """
    attributes = re.findall(r'^;\s*#@!\s+TF\.FileFunction,([^,\r\n]+)', text, re.M)
    expected_plating = 'Plated' if plated else 'NonPlated'
    if attributes and attributes != [expected_plating]:
        raise ProjectError('Excellon plating attribute contradicts the selected drill file')
    lines = [x.strip() for x in text.splitlines() if x.strip() and not x.lstrip().startswith(';')]
    if not lines or lines[0] != 'M48' or lines[-1] != 'M30':
        raise ProjectError('Incomplete Excellon header/termination')
    tools, current, x, y, metric, body = {}, None, None, None, False, False
    holes, format2 = [], False
    for line in lines[1:-1]:
        if line == 'FMAT,2':
            if body or format2: raise ProjectError('Duplicate or mid-body Excellon format declaration')
            format2 = True; continue
        if line.startswith('METRIC'):
            if body: raise ProjectError('Mid-file drill unit change')
            metric = True; continue
        if line.startswith('INCH') or line == 'M72':
            raise ProjectError('Review drill must use explicit metric units')
        tool = re.fullmatch(r'T(\d+)C([0-9.]+)', line)
        if tool:
            if body or int(tool[1]) in tools: raise ProjectError('Ambiguous drill tool')
            value = float(tool[2])
            if not math.isfinite(value) or value <= 0: raise ProjectError('Invalid drill size')
            tools[int(tool[1])] = value; continue
        if line in {'%', 'M95'}:
            body = True; continue
        if line in {'G90', 'G05', 'M71'}: continue
        selected = re.fullmatch(r'T(\d+)', line)
        if selected:
            current = int(selected[1]); continue
        coords = re.fullmatch(r'(?:X([-+]?\d+(?:\.\d*)?))?(?:Y([-+]?\d+(?:\.\d*)?))?', line)
        if not body or not metric or not coords or current not in tools:
            raise ProjectError('Unsupported or ambiguous drill record: ' + line)
        x = float(coords[1]) if coords[1] is not None else x
        y = float(coords[2]) if coords[2] is not None else y
        if x is None or y is None: raise ProjectError('Uninitialized drill coordinate')
        holes.append((x, y, tools[current], plated))
    if not metric or not body: raise ProjectError('Missing metric drill body')
    return holes


def native_hole_inventory(project, output):
    import pcbnew as p
    board = p.LoadBoard(str(project.board))
    rows = []
    for item in board.GetTracks():
        if isinstance(item, p.PCB_VIA):
            pos = item.GetPosition()
            rows.append({'uuid': item.m_Uuid.AsString(), 'ref_pin': '', 'kind': 'electrical_via',
                         'x_mm': p.ToMM(pos.x), 'y_mm': p.ToMM(pos.y),
                         'drill_mm': p.ToMM(item.GetDrillValue()), 'plated': True,
                         'net': item.GetNetname(), 'treatment': 'Type VII epoxy fill / planarize / copper cap'})
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            size = pad.GetDrillSize()
            if not size.x: continue
            if size.x != size.y: raise ProjectError('Circular-hole review cannot qualify slots')
            pos = pad.GetPosition()
            plated = pad.GetAttribute() != p.PAD_ATTRIB_NPTH
            rows.append({'uuid': pad.m_Uuid.AsString(), 'ref_pin': fp.GetReference()+'.'+pad.GetNumber(),
                         'kind': 'component_hole', 'x_mm': p.ToMM(pos.x), 'y_mm': p.ToMM(pos.y),
                         'drill_mm': p.ToMM(size.x), 'plated': plated,
                         'net': pad.GetNetname(), 'treatment': 'Open component/mounting hole; NOT epoxy filled'})
    if not rows: raise ProjectError('Native drill inventory is empty')
    with (output/'hole-treatment.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    expected = Counter((round(r['x_mm'],3), round(-r['y_mm'],3), round(r['drill_mm'],3), r['plated']) for r in rows)
    actual = []
    for file in (output/'drill').glob('*.drl'):
        plated = not file.stem.endswith('-NPTH')
        actual.extend(parse_decimal_drill(file.read_text(), plated))
    exported = Counter((round(x,3), round(y,3), round(d,3), plated) for x,y,d,plated in actual)
    if exported != expected:
        raise ProjectError('Drill/native mismatch: '+str({'missing': list((expected-exported).items())[:5], 'extra':list((exported-expected).items())[:5]}))
    return {'native_holes':len(rows), 'electrical_vias':sum(r['kind']=='electrical_via' for r in rows),
            'component_holes':sum(r['kind']=='component_hole' for r in rows),
            'drill_xy_diameter_plating_exact_at_0p001mm':True,
            'coordinate_convention':'Absolute PCB origin; Excellon X=x, Y=-y; millimeters',
            'supplier_treatment_acceptance':'OPEN'}


def validate_review_conditions(findings):
    from .manufacturing import REQUIRED_REVIEWS
    human = {'prototype.review.' + subject for subject in REQUIRED_REVIEWS}
    if any(f.status not in {'PASS','NOT_APPLICABLE'} and f.rule_id not in human for f in findings):
        raise ProjectError('Static manufacturing settings/profile/stackup are invalid; review export refused')
    return [{'rule':f.rule_id,'status':f.status,'message':f.message} for f in findings]


def export_review(project, output, tools):
    from .verification import verify
    from .export import export_bom, export_assembly
    from .schematic import discover_sheets
    report = verify(project, 'pcb', output, tools)
    out = Path(report.evidence['output'])
    report.evidence.update({'delivery_scope':'MANUFACTURING_REVIEW_NOT_RELEASED',
                            'prototype_ready':'BLOCKED', 'pcb_release':'BLOCKED',
                            'order_authorized':False})
    if any(f.status not in {'PASS','NOT_APPLICABLE'} for f in report.findings):
        report.findings.append(Finding('export.fabrication_review','FAIL','Current native PCB verification failed'))
        return report
    cli = tools.get('kicad-cli','kicad-cli')
    try:
        check_native_settings(project)
        before = design_source_hashes(project)
        verified = report.evidence['source_hashes_after']
        if any(verified.get(name) != digest for name, digest in before.items()):
            raise ProjectError('Design changed between native verification and freezing')
        frozen, frozen_evidence = freeze_design(project, out/'frozen-design', before)
        report.evidence['review_frozen_design'] = frozen_evidence
        pending, _ = check_prototype_inputs(project)
        report.evidence['release_conditions'] = validate_review_conditions(pending)
        # Review export does NOT replace or alter any signed release evidence.
        for folder in ('gerbers','drill','cam'):(out/folder).mkdir()
        def run(name, command, timeout=300):
            check_frozen_design(frozen_evidence)
            result = run_native(command, frozen.root, timeout)
            (out/(name+'.log')).write_text(result.get('stdout','')+result.get('stderr','')+result.get('error',''), encoding='utf-8')
            if result['exit_code']:raise ProjectError(name+' failed; see native log')
            return result['stdout']
        commands = [
            ('gerbers',['gerbers','--no-protel-ext','--check-zones','--layers',','.join(GERBER_LAYERS),'--output',str(out/'gerbers')+'/']),
            ('drill',['drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-map','--generate-report','--output',str(out/'drill')+'/']),
            ('position',['pos','--format','csv','--units','mm','--side','both','--exclude-dnp','--output',str(out/'assembly.csv')]),
            ('step',['step','--output',str(out/'board.step')]),
            ('drawing',['pdf','--mode-single','--layers','F.Fab,B.Fab,Edge.Cuts,Dwgs.User','--output',str(out/'drawing.pdf')]),
        ]
        for name,args in commands:run('review-'+name,[cli,'pcb','export',*args,str(frozen.board)])
        export_bom(frozen,out,cli)
        report.evidence['assembly_review'] = export_assembly(frozen,out,cli)
        report.evidence['native_output_hashes'] = validate_fabrication_outputs(out)
        report.evidence['drill_review'] = native_hole_inventory(frozen,out)
        report.evidence['pdf_review'] = {'schematic':validate_pdf(out/'schematic.pdf',len(discover_sheets(project))),
                                       'drawing':validate_pdf(out/'drawing.pdf',1)}
        from importlib.metadata import version
        report.evidence['independent_parser_versions'] = {name: version(name) for name in ('gerbonara','pypdf')}
        cam = {}
        for layer in GERBER_LAYERS:
            f = next((out/'gerbers').glob('*-'+GERBER_NATIVE_SUFFIXES[layer]+'.gbr'))
            check_cam_terminator(f)
            populated = bool(re.search(r'D0[13]\*', f.read_text()))
            if not populated and layer in (*GERBER_LAYERS[:4], 'Edge.Cuts'):
                raise ProjectError('Required CAM layer is empty: '+layer)
            item = {'sha256':sha256(f),'populated':populated}
            if populated:
                name='cam-'+GERBER_NATIVE_SUFFIXES[layer]
                bounds=run(name+'-bounds',[sys.executable,'-m','gerbonara','bounding-box',str(f)])
                values = [float(v) for v in bounds.split()]
                if len(values) != 4 or not all(math.isfinite(v) for v in values):
                    raise ProjectError('Independent CAM bounds are incomplete')
                item['independent_bounds_mm']=values
                svg=out/'cam'/(layer+'.svg')
                run(name+'-render',[sys.executable,'-m','gerbonara','render',str(f),str(svg)])
                if not svg.is_file() or not svg.stat().st_size:raise ProjectError('Empty independent CAM render')
            cam[layer]=item
        for f in (out/'drill').glob('*.drl'):
            if parse_decimal_drill(f.read_text(), not f.stem.endswith('-NPTH')):
                run('cam-'+f.stem,[sys.executable,'-m','gerbonara','render',str(f),str(out/'cam'/(f.stem+'.svg'))])
        report.evidence['independent_cam']=cam
        check_frozen_design(frozen_evidence)
        if design_source_hashes(project)!=before:raise ProjectError('Sources changed during review export')
        report.evidence['design_source_hashes']=before
        report.evidence['review_tool_sha256']={p.relative_to(project.root).as_posix():sha256(p) for p in Path(__file__).parent.rglob('*.py')}
        (out/'READ_BEFORE_ORDER.txt').write_text('MANUFACTURING REVIEW CANDIDATE - NOT A FABRICATION RELEASE\n'
            'Native CAD, source identity, BOM/CPL and CAM checks are attached.\n'
            'Obtain source-bound engineering signoff and written vendor acceptance of\n'
            'stackup, copper, Type VII filled/capped vias, controlled finished holes,\n'
            'U13 customized copper land and assembly/stencil before ordering.\n'
            'Electrical vias are filled; component/mounting holes MUST stay open.\n'
            'Bench, dynamic protection, thermal, EMC and FPGA STA are not certified.\n',encoding='utf-8')
        report.findings.append(Finding('export.fabrication_review','PASS','Verified review files only; no order/release authorization'))
        from dataclasses import asdict
        (out/'review-status.json').write_text(json.dumps(asdict(report),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        files=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS','review-package.zip'})
        (out/'SHA256SUMS').write_text(''.join(sha256(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in files),encoding='utf-8')
        with zipfile.ZipFile(out/'review-package.zip','x',zipfile.ZIP_DEFLATED) as z:
            for p in [*files,out/'SHA256SUMS']:z.write(p,p.relative_to(out))
        report.evidence['package_sha256']=sha256(out/'review-package.zip')
    except Exception as exc:
        report.findings.append(Finding('export.fabrication_review','FAIL',str(exc)))
    return report
