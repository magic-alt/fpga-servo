"""Explicitly configured auxiliary-buck design calculations; never bench evidence."""
import csv
import json
import math
import re
from pathlib import Path
from ..kicad import extract_forms, property_value, head_string


def controller_internal_rule_errors(text):
    from .power_layout import vendor_api
    rules=[r for r in extract_forms(text,'rule') if head_string(r.text,'rule')=='U12 internal lands']
    if len(rules)!=1:
        return ['U12 requires exactly one reviewed internal Pad-Pad 0.45mm rule']
    return vendor_api().internal_pad_rule_errors(rules[0].text,'U12',.45)


def output_population_errors(profile, values, pins):
    """Reject unreviewed added capacitance on the complete converter rail."""
    actual = {ref: value for ref, value in values.items() if ref.startswith('C')
              and {pins.get((ref, '1')), pins.get((ref, '2'))} == {'/VA_5V', '/GND'}}
    if actual != profile.get('output_capacitor_population'):
        return ['5V complete output capacitor population changed; recompute stability/startup budget']
    return []


def controller_land_errors(text):
    """Bound U12 copper and mask/paste separately; ordinary vias are not filled."""
    errors = []
    if re.search(r'\(layer\s+"[FB]\.(?:Mask|Paste)"\)',text):
        errors.append('U12 extra mask/paste graphic bypasses the reviewed aperture union')
    pads = extract_forms(text, 'pad')
    numbered = {}
    apertures = []
    for form in pads:
        match = re.match(r'\(pad\s+"([^"]*)"\s+smd\s+(\w+)', form.text)
        if not match:
            errors.append('U12 unsupported pad type'); continue
        number, shape = match.groups()
        def pair(head):
            found = re.search(r'\('+head+r'\s+(-?[\d.]+)\s+(-?[\d.]+)\)', form.text)
            return tuple(float(v) for v in found.groups()) if found else None
        layers = extract_forms(form.text,'layers')
        record = (pair('at'), pair('size'), set(re.findall(r'"([^"]+)"',layers[0].text)) if layers else set(), shape)
        if number:
            if number in numbered: errors.append('U12 duplicate physical pad '+number)
            numbered[number] = record
        else: apertures.append(record)
    if set(numbered) != {str(i) for i in range(1,10)}:
        errors.append('U12 requires exactly physical pads 1..9')
    for number in range(1,9):
        index = number-1 if number<=4 else 8-number
        expected = ((-2.7 if number<=4 else 2.7, round(-1.905+1.27*index,3)),(1.55,.6),{'F.Cu','F.Mask','F.Paste'},'roundrect')
        if numbered.get(str(number)) != expected: errors.append('U12 signal land differs from reviewed DDA0008B')
    if numbered.get('9') != ((0.,0.),(2.95,4.9),{'F.Cu'},'roundrect'):
        errors.append('U12 EP metal must be copper-only 2.95x4.9; mask union must not expose thermal vias')
    if apertures != [((0.,0.),(2.71,3.4),{'F.Mask','F.Paste'},'roundrect')]:
        errors.append('U12 requires one unnumbered 2.71x3.4 mask/paste aperture')
    for form in pads:
        if re.match(r'\(pad\s+""',form.text):
            ratio = re.search(r'\(roundrect_rratio\s+([\d.]+)\)',form.text)
            if not ratio or not math.isclose(float(ratio[1])*2.71,.05,abs_tol=1e-6):
                errors.append('U12 aperture corner radius must be 0.05mm')
    return sorted(set(errors))


def evaluate_5v(profile, pins=None):
    """TPS62901 MODE=VIN, 2.5MHz, L=2.2uH reviewed engineering envelope.

    Effective capacitance uses an OEM combined AC/DC model plus reserves;
    this check never turns typical characteristics into guaranteed limits.
    """
    errors = []
    for key, minimum in [('input_effective_uf', 3), ('output_effective_uf', 10),
                         ('soft_start_min_ms', 1)]:
        value = profile.get(key, 0)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
            errors.append(f'5V {key} below reviewed minimum {minimum}')
    nominal = profile.get('output_nominal_max_uf', 0)
    if not 10 <= nominal < 100:
        errors.append('5V output population outside reviewed low-ESR / 2.2uH envelope')
    if profile.get('qualification_status') != 'TYPICAL_MODEL_WITH_RESERVES_BENCH_OPEN':
        errors.append('5V model must retain physical qualification boundary')
    if pins is not None:
        expected = {('C133', '2'): '/GND', ('C132', '1'): '/VA_5V',
                    ('C132', '2'): '/GND', ('C31', '1'): '/VA_5V',
                    ('C31', '2'): '/GND', ('C30', '1'): '/VDRV_12V',
                    ('C30', '2'): '/GND', ('U13', '7'): '/VDRV_12V'}
        for pin, net in expected.items():
            if pins.get(pin) != net:
                errors.append(f'5V {pin[0]}.{pin[1]} must connect to {net}')
        ss = pins.get(('U13', '8'), '')
        if not ss or ss.startswith('unconnected-') or ss in ['/GND', '/VA_5V', '/VDRV_12V'] or ss != pins.get(('C133', '1')):
            errors.append('U13 SS/TR requires its dedicated C133 soft-start node')
    return errors


def evaluate(profile):
    errors = []
    r, c, ind = (profile[k] for k in ('requirement', 'controller', 'inductor'))
    load = r['continuous_total_a']
    if load < 1.0:
        errors.append('Required total continuous output must remain at least 1 A')
    effective = ind['nominal_uh'] * 1e-6
    for name in ('tolerance_fraction', 'bias_allowance_fraction', 'temperature_allowance_fraction'):
        if not 0 <= ind[name] < 1:
            raise ValueError('Invalid inductance allowance')
        effective *= 1 - ind[name]
    freq = c['frequency_design_min_khz'] * 1e3
    if effective <= 0 or freq <= 0:
        raise ValueError('Inductance and frequency must be positive')
    corners = []
    for vin in (r['vin_min_v'], r['vin_max_v']):
        vout = r['vout_max_v']
        if not 0 < vout < vin:
            raise ValueError('Buck output must be below input')
        ripple = vout * (1 - vout / vin) / (freq * effective)
        peak = load + ripple / 2
        rms = math.sqrt(load ** 2 + ripple ** 2 / 12)
        corners.append({'vin_v': vin, 'ripple_pp_a': ripple, 'peak_a': peak, 'rms_a': rms})
    peak = max(x['peak_a'] for x in corners)
    rms = max(x['rms_a'] for x in corners)
    margin = c['peak_limit_min_a'] - peak
    if margin < profile['minimum_peak_margin_a']:
        errors.append('Minimum peak current-limit margin insufficient')
    if rms > ind['rated_rms_a'] * ind['rms_derating_factor']:
        errors.append('Derated inductor RMS rating insufficient')
    fault_peak = c['peak_limit_max_a'] + r['vin_max_v'] / effective * c['propagation_delay_ns'] * 1e-9
    if fault_peak >= ind['saturation_10pct_typical_a'] * ind['saturation_derating_factor']:
        errors.append('Derated typical saturation below estimated fault peak')
    if profile['qualification_status'] != 'DESIGN_CALCULATION_ONLY_BENCH_OPEN':
        errors.append('Calculation must not claim bench qualification')
    if not profile.get('required_bench') or not profile.get('engineering_allowances_not_guaranteed_datasheet_limits'):
        errors.append('Explicit engineering allowances and bench gates required')
    fb = profile['feedback']
    def number(value):
        match = re.fullmatch(r'(\d+(?:\.\d+)?)([pnumkM]?)(?:H|F|ohm)?', value)
        if not match:
            raise ValueError('Unsupported engineering value')
        return float(match[1]) * {'':1, 'p':1e-12, 'n':1e-9, 'u':1e-6, 'm':1e-3, 'k':1e3, 'M':1e6}[match[2]]
    parts = {part['ref']: part for part in (ind, *profile['support_components'])}
    bindings = [(ind['ref'], ind['nominal_uh'] * 1e-6),
                (fb['upper_ref'], fb['upper_ohm']), (fb['lower_ref'], fb['lower_ohm']),
                (fb['ripple_resistor_ref'], fb['ripple_resistance_ohm']),
                (fb['ripple_capacitor_ref'], fb['ripple_capacitance_nf'] * 1e-9)]
    if any(not math.isclose(number(parts[ref]['value']), value, rel_tol=1e-9) for ref, value in bindings):
        errors.append('Calculation parameters do not match actual component values')
    programmed_khz = r['vout_nominal_v'] * 2500 / (c['ron_resistance_ohm'] / 1000)
    if not math.isclose(programmed_khz, c['frequency_nominal_khz'], rel_tol=1e-9):
        errors.append('Nominal frequency does not match actual RON value')
    def injected(vin, vout, frequency, resistance, capacitance):
        return vout * (1 - vout / vin) / (frequency * resistance * capacitance)
    ra, ca = fb['ripple_resistance_ohm'], fb['ripple_capacitance_nf'] * 1e-9
    ra_tol, ca_tol = fb['ripple_resistance_total_fraction'], fb['ripple_capacitance_total_fraction']
    ripple_min = min(injected(vin, vout, c['frequency_design_max_khz'] * 1e3,
                             ra * (1 + ra_tol), ca * (1 + ca_tol)) * fb['coupling_gain_min']
                     for vin in (r['vin_min_v'], r['vin_max_v'])
                     for vout in (r['vout_min_v'], r['vout_max_v']))
    ripple_max = max(injected(vin, vout, freq, ra * (1 - ra_tol), ca * (1 - ca_tol))
                     for vin in (r['vin_min_v'], r['vin_max_v'])
                     for vout in (r['vout_min_v'], r['vout_max_v']))
    if ripple_min < fb['required_ripple_v']:
        errors.append('Minimum FB injected ripple below controller recommendation')
    tolerance = fb['resistance_total_fraction']
    gain_min = 1 + fb['upper_ohm'] * (1 - tolerance) / (fb['lower_ohm'] * (1 + tolerance))
    gain_max = 1 + fb['upper_ohm'] * (1 + tolerance) / (fb['lower_ohm'] * (1 - tolerance))
    output_min = fb['vref_min_v'] * gain_min
    output_max = (fb['vref_max_v'] + ripple_max / 2) * gain_max
    if output_min < r['vout_min_v'] or output_max > r['vout_max_v']:
        errors.append('Feedback tolerance and ripple-derived output envelope exceeded')
    return errors, {'effective_l_min_uh': effective * 1e6, 'peak_a': peak, 'rms_a': rms,
                    'minimum_peak_margin_a': margin, 'estimated_fault_peak_a': fault_peak,
                    'injected_ripple_min_v': ripple_min, 'injected_ripple_max_v': ripple_max,
                    'output_calculated_min_v': output_min, 'output_calculated_max_v': output_max,
                    'corners': corners, 'status': 'CALCULATION_ONLY_BENCH_OPEN'}


def check_project(project, xml=None):
    path = project.root / project.parameters['aux_power_profile']
    profile = json.loads(path.read_text(encoding='utf-8'))
    errors, _ = evaluate(profile)
    if 'downstream_5v' in profile:
        errors += evaluate_5v(profile['downstream_5v'])
    ind, controller = profile['inductor'], profile['controller']
    expected_parts = {part['ref']: {'Value':part['value'], 'Footprint':part['footprint'],
                                  **{k:part[k] for k in ('Manufacturer','MPN','LCSC')}}
                      for part in (ind, *profile['support_components'])}
    symbols = {}
    for source in project.schematic.parent.glob('*.kicad_sch'):
        for form in extract_forms(source.read_text(encoding='utf-8'), 'symbol'):
            if '(lib_id ' in form.text:
                ref = property_value(form.text, 'Reference')
                if ref in expected_parts or ref in (controller['ref'], controller['ron_ref']):
                    symbols[ref] = form.text
    for ref, expected in expected_parts.items():
        for field, value in expected.items():
            if (property_value(symbols.get(ref, ''), field) or '') != value:
                errors.append(f"{ref} schematic {field} differs from reviewed design candidate")
    if property_value(symbols.get(controller['ref'], ''), 'Value') != controller['value']:
        errors.append('Auxiliary controller changed without recalculation')
    if property_value(symbols.get(controller['ref'], ''), 'MPN') != controller['value']:
        errors.append('Auxiliary controller MPN differs from model')
    land = controller.get('footprint')
    if land != 'fpga-servo:TI_DDA0008B_LM5164':
        errors.append('U12 reviewed Footprint selection missing from controller profile')
    if property_value(symbols.get(controller['ref'], ''),'Footprint') != land:
        errors.append('U12 schematic Footprint differs from reviewed DDA0008B land')
    local = project.schematic.parent/'fpga-servo.pretty/TI_DDA0008B_LM5164.kicad_mod'
    if not local.is_file(): errors.append('U12 local Footprint missing')
    else: errors += controller_land_errors(local.read_text(encoding='utf-8'))
    rules=project.schematic.with_suffix('.kicad_dru')
    if not rules.is_file():errors.append('U12 reviewed internal pad rule file missing')
    elif land=='fpga-servo:TI_DDA0008B_LM5164':
        errors += controller_internal_rule_errors(rules.read_text(encoding='utf-8'))
    if property_value(symbols.get(controller['ron_ref'], ''), 'Value') != f"{controller['ron_resistance_ohm'] / 1000:g}k":
        errors.append('Actual RON resistor differs from frequency model')
    with project.bom.open(encoding='utf-8-sig', newline='') as stream:
        bom = {row['Ref']: row for row in csv.DictReader(stream)}
    if bom.get(controller['ref'],{}).get('Package') != land:
        errors.append('U12 BOM Package differs from reviewed Footprint')
    for ref, expected in expected_parts.items():
        row = bom.get(ref, {})
        for field, value in expected.items():
            column = {'Value': 'Value / Part', 'Footprint': 'Package'}.get(field, field)
            if row.get(column) != value:
                errors.append(f"{ref} BOM {column} differs from design candidate")
    if xml:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml).getroot()
        comps = {x.attrib['ref']: x for x in tree.findall('components/comp')}
        if comps.get(controller['ref']) is None or comps[controller['ref']].findtext('footprint') != land:
            errors.append('U12 fresh native Footprint differs from reviewed DDA0008B land')
        for ref, expected in expected_parts.items():
            comp = comps.get(ref)
            if comp is None:
                errors.append(f'Fresh netlist lacks {ref}')
                continue
            fields = {f.attrib['name']: f.text or '' for f in comp.findall('fields/field')}
            actual = {'Value': comp.findtext('value'), 'Footprint': comp.findtext('footprint'), **fields}
            for field, value in expected.items():
                if actual.get(field, '') != value:
                    errors.append(f"Fresh netlist {ref} {field} mismatch")
        pins = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                for net in tree.findall('nets/net') for n in net.findall('node')}
        if 'downstream_5v' in profile:
            errors += evaluate_5v(profile['downstream_5v'], pins)
            errors += output_population_errors(profile['downstream_5v'],
                                               {ref: comp.findtext('value') for ref, comp in comps.items()}, pins)
        if pins.get((ind['ref'], '1')) != pins.get((controller['ref'], '8')):
            errors.append('Auxiliary SW-to-L1 physical pin connection changed')
        if pins.get((ind['ref'], '2')) != '/VDRV_12V':
            errors.append('Auxiliary L1 output physical pin connection changed')
    return errors
