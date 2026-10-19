"""Validate real copper/paste and IPC-4761 intent, not supplier order acceptance."""
import json
import math
import re
from pathlib import Path
from ..kicad import direct_child_forms, extract_forms, head_string, property_value

RPJ = 'Texas_RPJ0009A_VQFN-HR-9_1.5x2mm'
# TI 4224505/A centers, original stencil apertures. Copper-only ECO widens 1..6.
RPJ_PADS = {
    '1': (-.625, -.25, .65, .2), '2': (-.625, .25, .65, .2),
    '3': (-.625, .75, .65, .2), '4': (.45, .75, 1., .2),
    '5': (.625, .25, .65, .2), '6': (.45, -.25, 1., .2),
    '7': (.5, -.925, .25, .55), '8': (0., -.925, .25, .55),
    '9': (-.5, -.925, .25, .55),
}


def _geometry(pad):
    a = direct_child_forms(pad, 'at')
    s = direct_child_forms(pad, 'size')
    if len(a) != 1 or len(s) != 1:
        raise ValueError('Pad has ambiguous position/size')
    xy = re.fullmatch(r'\(at\s+([-+\d.eE]+)\s+([-+\d.eE]+)(?:\s+(0(?:\.0+)?))?\)', a[0].text)
    wh = re.fullmatch(r'\(size\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)', s[0].text)
    if not xy or not wh:
        raise ValueError('Unsupported RPJ local pad geometry')
    result = tuple(float(v) for v in (xy[1], xy[2], wh[1], wh[2]))
    if not all(math.isfinite(v) for v in result) or min(result[2:]) <= 0:
        raise ValueError('Invalid pad dimensions')
    return result


def rpj_errors(footprint):
    pads = extract_forms(footprint, 'pad')
    copper, paste = {}, []
    errors = []
    for pad in pads:
        layers = direct_child_forms(pad.text, 'layers')
        if len(layers) != 1:
            errors.append('RPJ ambiguous pad layers'); continue
        layers = re.findall(r'"([^"]+)"', layers[0].text)
        geom = _geometry(pad.text)
        pin = head_string(pad.text, 'pad')
        if 'F.Cu' in layers:
            if pin not in RPJ_PADS or pin in copper:
                errors.append('RPJ duplicated or unexpected copper pad')
            copper[pin] = geom
            if 'F.Mask' not in layers:
                errors.append('RPJ copper pad must retain mask opening')
        elif pin or layers != ['F.Paste'] or direct_child_forms(pad.text, 'net'):
            errors.append('RPJ paste-only apertures must be unnumbered and netless')
        if 'F.Paste' in layers:
            radius = direct_child_forms(pad.text, 'roundrect_rratio')
            if len(radius) != 1 or radius[0].text != '(roundrect_rratio 0.2)':
                errors.append('RPJ original paste corner radius changed')
            paste.append(geom)
    expected = {pin: (*g[:3], .25 if int(pin) <= 6 else g[3]) for pin, g in RPJ_PADS.items()}
    if copper != expected:
        errors.append('RPJ copper ECO must retain centers/pin identities and 0.25mm minimum')
    if sorted(paste) != sorted(RPJ_PADS.values()):
        errors.append('RPJ original stencil apertures must be preserved exactly')
    return errors


def board_errors(text, minimum=.25):
    errors = []
    setup = direct_child_forms(text, 'setup')
    if len(setup) != 1:
        return ['Missing or ambiguous native PCB setup']
    for key in ('filling', 'capping'):
        fields = direct_child_forms(setup[0].text, key)
        if len(fields) != 1 or fields[0].text != f'({key} yes)':
            errors.append(f'Type VII requires native {key}=yes, not mask tenting alone')
    for via in extract_forms(text, 'via'):
        for key in ('filling', 'capping'):
            fields = direct_child_forms(via.text, key)
            if len(fields) > 1 or fields and fields[0].text != f'({key} yes)':
                errors.append(f'Via override disables Type VII {key}')
    for footprint in extract_forms(text, 'footprint'):
        ref = property_value(footprint.text, 'Reference')
        for pad in extract_forms(footprint.text, 'pad'):
            if not re.match(r'\(pad\s+"[^"]*"\s+smd\s', pad.text):
                continue
            layers = direct_child_forms(pad.text, 'layers')
            if not layers or not any(x in layers[0].text for x in ('"F.Cu"', '"B.Cu"')):
                continue
            size = direct_child_forms(pad.text, 'size')
            numbers = re.findall(r'[-+]?\d+(?:\.\d+)?', size[0].text) if len(size) == 1 else []
            if len(numbers) != 2 or min(map(float, numbers)) + 1e-9 < minimum:
                errors.append(f'{ref}.{head_string(pad.text, "pad")}: SMD copper below {minimum}mm fab minimum')
        if ref == 'U13':
            errors.extend(rpj_errors(footprint.text))
    return errors


def check_project(project):
    profile = json.loads((project.schematic.parent / 'fabrication_profile.json').read_text())
    requirements = profile.get('manufacturing_requirements', {})
    if requirements.get('min_smd_copper_pad_mm') != .25:
        return ['Selected JLC SMD copper minimum must remain explicit at 0.25mm']
    if requirements.get('via_fill_material') != 'nonconductive_epoxy':
        return ['Type VII fill material must be explicit; KiCad fill flag is not a material approval']
    errors = board_errors(project.board.read_text(), .25)
    library = project.schematic.parent / 'fpga-servo.pretty' / (RPJ + '.kicad_mod')
    errors.extend(rpj_errors(library.read_text()))
    return errors
