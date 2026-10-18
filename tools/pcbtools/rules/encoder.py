"""AM26LV32E PW16 physical contract: TI SLLS849E, page 3, Table 5-1."""
from pathlib import Path
import math
import re
import xml.etree.ElementTree as ET
from ..kicad import extract_forms, head_string, property_value, parse_at

def esd_land_errors(text):
    """Reviewed RVZ variant: retained longitudinal lands, .25mm pad width."""
    pads = extract_forms(text, 'pad')
    expected = {str(i+1): (-.675, -1.5+.5*i) for i in range(7)}
    expected.update({str(14-i): (.675, -1.5+.5*i) for i in range(7)})
    if len(pads) != 14 or {head_string(f.text, 'pad') for f in pads} != set(expected):
        return ['U19 requires exactly reviewed physical pads 1..14']
    errors = []
    for pad in pads:
        number = head_string(pad.text, 'pad')
        size = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)\)', pad.text)
        actual = tuple(map(float, size.groups())) if size else ()
        if actual != (.75, .25) or any(not math.isclose(a,b,abs_tol=1e-8) for a,b in zip(parse_at(pad.text),expected[number])):
            errors.append(f'U19 pad {number}: reviewed .75x.25mm land/position changed')
        if any(f'"{layer}"' not in pad.text for layer in ['F.Cu', 'F.Mask', 'F.Paste']):
            errors.append(f'U19 pad {number}: copper/mask/paste coverage missing')
    return errors

PINOUT = {'1A+': '2', '1A-': '1', '1Y': '3', '2A+': '6', '2A-': '7',
          '2Y': '5', '3A+': '10', '3A-': '9', '3Y': '11', '4A+': '14',
          '4A-': '15', '4Y': '13', 'G': '4', 'G_N': '12', 'GND': '8', 'VCC': '16'}
NETS = {'1': 'ENC_A_N', '2': 'ENC_A_P', '3': 'ENC_A', '4': 'VIO_3V3',
        '5': 'ENC_B', '6': 'ENC_B_P', '7': 'ENC_B_N', '8': 'GND',
        '9': 'ENC_Z_N', '10': 'ENC_Z_P', '11': 'ENC_Z', '12': 'GND', '16': 'VIO_3V3'}

def pinout_errors(text, alias):
    symbols = [f.text for f in extract_forms(text, 'symbol') if head_string(f.text, 'symbol') == alias]
    if len(symbols) != 1:
        return [f'{alias}: exactly one manufacturer pin definition required']
    pins = {}
    for pin in extract_forms(symbols[0], 'pin'):
        names, numbers = extract_forms(pin.text, 'name'), extract_forms(pin.text, 'number')
        if not names or not numbers:
            return [f'{alias}: incomplete physical pin definition']
        name, number = head_string(names[0].text, 'name'), head_string(numbers[0].text, 'number')
        if name in pins:
            return [f'{alias}: duplicate logical pin {name}']
        pins[name] = number
    return [] if pins == PINOUT else [f'{alias}: physical pins differ from TI SLLS849E Table 5-1']

def physical_errors(xml):
    root = ET.parse(xml).getroot()
    components = [c for c in root.findall('components/comp') if c.get('ref') == 'U7']
    if len(components) != 1:
        return ['Fresh native netlist must contain exactly one U7']
    fields = {f.get('name'): f.text for f in components[0].findall('fields/field')}
    errors = []
    if fields.get('MPN') != 'AM26LV32EIPWR':
        errors.append('U7 exact PW16 MPN changed without pinout review')
    memberships = {}
    for net in root.findall('nets/net'):
        for node in net.findall('node'):
            if node.get('ref') == 'U7':
                number = node.get('pin')
                if number in memberships:
                    errors.append(f'U7.{number}: duplicate physical membership')
                memberships[number] = (net.get('name', ''), len(net.findall('node')))
    if set(memberships) != {str(n) for n in range(1, 17)}:
        errors.append('U7 native physical pin coverage must be 1..16')
    for number, expected in NETS.items():
        if memberships.get(number, ('', 0))[0].rsplit('/', 1)[-1] != expected:
            errors.append(f'U7.{number} must connect to {expected}')
    for number in ('13', '14', '15'):
        name, count = memberships.get(number, ('', 0))
        if not name.startswith('unconnected-(U7-') or count != 1:
            errors.append(f'U7.{number}: unused fourth-channel pin must remain an explicit NC')
    return errors

def check_project(project, xml=None):
    source = project.schematic.parent / 'encoder.kicad_sch'
    errors = pinout_errors(source.read_text(encoding='utf-8'), 'ax7010_servo_reva:AM26LV32E')
    errors += pinout_errors(project.libraries[0].read_text(encoding='utf-8'), 'AM26LV32E')
    footprint = project.parameters.get('encoder_esd_footprint')
    if footprint:
        raw = source.read_text(encoding='utf-8')
        u19 = [f.text for f in extract_forms(raw, 'symbol') if '(lib_id ' in f.text and property_value(f.text, 'Reference') == 'U19']
        if len(u19) != 1 or property_value(u19[0], 'Footprint') != footprint:
            errors.append('U19 source must use reviewed RVZ manufacturing land')
        library, name = footprint.split(':')
        errors += esd_land_errors((source.parent / (library+'.pretty') / (name+'.kicad_mod')).read_text(encoding='utf-8'))
        if xml:
            root = ET.parse(xml).getroot()
            comp = root.find("components/comp[@ref='U19']")
            if comp is None or comp.findtext('footprint') != footprint:
                errors.append('Fresh U19 physical footprint differs from reviewed RVZ land')
    if xml:
        errors += physical_errors(Path(xml))
    return errors
