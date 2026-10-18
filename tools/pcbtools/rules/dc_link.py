"""Explicit dual-servo damped DC-link contract; calculations are not bench evidence."""
import csv
import json
import math
import xml.etree.ElementTree as ET
from ..kicad import extract_forms, property_value
from ..schematic import discover_sheets

CAP_MPN = 'EKZN101ELL101MJ20S'
RES_MPN = 'WSL2512R3300FEA'
CAP_RIPPLE_100KHZ_A = 1.57  # Exact NCC 2026 KZNLL row; not a neighbouring value.
FREQUENCY_FACTOR = .90  # Conservative 10 kHz factor for the 56–180 uF group.
SERIES_R_OHM = .33


def evaluate(profile):
    errors = []
    keys = ('continuous_phase_arms', 'peak_phase_amplitude_a', 'peak_duration_s',
            'sharing_factor', 'waveform_allowance', 'resistor_hot_power_limit_w')
    if any(not isinstance(profile.get(k), (int, float)) or isinstance(profile[k], bool)
           or not math.isfinite(profile[k]) or profile[k] <= 0 for k in keys):
        return {}, ['DC-link budget must contain finite positive inputs']
    if profile['continuous_phase_arms'] < 10 or profile['peak_phase_amplitude_a'] < 20 or profile['peak_duration_s'] < 30:
        errors.append('Approved phase-current/duration requirement was reduced')
    if profile.get('waveform') != 'BALANCED_SINUSOIDAL':
        errors.append('This ripple bound requires explicitly balanced sinusoidal phase current')
    if not 0 < profile['sharing_factor'] <= .8 or profile['waveform_allowance'] < 1.1:
        errors.append('Current-sharing and waveform allocation was weakened')
    if profile['resistor_hot_power_limit_w'] > .708:
        errors.append('Hot resistor allowance exceeds reviewed 90 C design allocation')
    branches = profile.get('branches', [])
    caps = [b['capacitor'] for b in branches]
    resistors = [b['resistor'] for b in branches]
    if len(caps) != len(set(caps)) or len(resistors) != len(set(resistors)):
        errors.append('Every capacitor requires its own unique series damping resistor')
    count = len(branches)
    if count < 10:
        errors.append('At least ten individually damped 100 uF cans are required')
    if not count:
        return {}, errors
    continuous = profile['continuous_phase_arms'] / math.sqrt(2)
    peak = profile['peak_phase_amplitude_a'] / 2
    demand = max(continuous, peak) * profile['waveform_allowance']
    allocated = count * CAP_RIPPLE_100KHZ_A * FREQUENCY_FACTOR * profile['sharing_factor']
    branch_peak = demand / (count * profile['sharing_factor'])
    branch_power = branch_peak ** 2 * SERIES_R_OHM * 1.01
    if allocated < demand:
        errors.append('Frequency/sharing-allocated capacitor ripple rating is insufficient')
    if branch_power > profile['resistor_hot_power_limit_w']:
        errors.append('Worst allocated branch exceeds hot damping-resistor power budget')
    if profile.get('qualification_status') != 'STATIC_DESIGN_ONLY_BENCH_OPEN':
        errors.append('Static calculation must retain physical qualification as open')
    return {'continuous_capacitor_bank_arms_bound': continuous,
            'peak_phase_arms': profile['peak_phase_amplitude_a'] / math.sqrt(2),
            'peak_capacitor_bank_arms_bound': peak,
            'allocated_ripple_arms': allocated, 'demand_with_waveform_allowance_arms': demand,
            'worst_allocated_branch_arms': branch_peak,
            'worst_branch_resistor_w': branch_power,
            'nominal_bank_uf': count * 100,
            'nominal_energy_48v_j': .5 * count * 100e-6 * 48 ** 2}, errors


def physical_errors(profile, parts, pins):
    errors = []
    if parts.get('J7', {}).get('MPN') != '1714971' or parts.get('J7', {}).get('Value') != 'EXT_SINK':
        errors.append('J7: reviewed protected-bus sink connector is required')
    if pins.get(('J7', '1')) != '/VBUS_PROT' or pins.get(('J7', '2')) != '/GND':
        errors.append('External sink must connect directly after reverse protection')
    by_net = {}
    for node, net in pins.items():
        by_net.setdefault(net, set()).add(node)
    if pins.get(('RSH4', '1')) != '/VBUS_PROT' or pins.get(('RSH4', '2')) != '/VBUS_BRIDGE':
        errors.append('Bus shunt upstream/downstream force terminals changed')
    for branch in profile['branches']:
        c, r = branch['capacitor'], branch['resistor']
        for ref, mpn, value in ((c, CAP_MPN, '100uF'), (r, RES_MPN, '0.33R')):
            if parts.get(ref, {}).get('MPN') != mpn or parts.get(ref, {}).get('Value') != value:
                errors.append(f'{ref}: unreviewed DC-link identity/value')
        internal = pins.get((c, '1'))
        if internal in (None, '/GND', '/VBUS_PROT', '/VBUS_BRIDGE') or by_net.get(internal) != {(c, '1'), (r, '2')}:
            errors.append(f'{c}: require exclusive capacitor-positive to damping-resistor branch')
        if pins.get((r, '1')) != '/VBUS_PROT' or pins.get((c, '2')) != '/GND':
            errors.append(f'{c}: bank must remain upstream of fast bus shunt with correct polarity')
    return errors


def check_project(project, xml=None):
    path = project.root / project.parameters['dc_link_profile']
    profile = json.loads(path.read_text(encoding='utf-8'))
    _, errors = evaluate(profile)
    authored = {}
    for sheet in discover_sheets(project):
        for f in extract_forms(sheet.read_text(encoding='utf-8'), 'symbol'):
            if '(lib_id ' in f.text:
                authored[property_value(f.text, 'Reference')] = {
                    k: property_value(f.text, k) for k in ('MPN', 'Value')}
    rows = {r['Ref']: r for r in csv.DictReader(project.bom.open(encoding='utf-8-sig', newline=''))}
    if authored.get('J7') != {'MPN': '1714971', 'Value': 'EXT_SINK'} or rows.get('J7', {}).get('MPN') != '1714971':
        errors.append('J7: schematic/BOM must retain reviewed protected-bus sink interface')
    for branch in profile['branches']:
        for ref, mpn, value in ((branch['capacitor'], CAP_MPN, '100uF'),
                                (branch['resistor'], RES_MPN, '0.33R')):
            if authored.get(ref) != {'MPN': mpn, 'Value': value} or rows.get(ref, {}).get('MPN') != mpn:
                errors.append(f'{ref}: schematic/BOM identity differs from reviewed damped bank')
    if xml:
        tree = ET.parse(xml).getroot()
        parts = {c.attrib['ref']: {'Value': c.findtext('value'), **{
            f.attrib['name']: f.text for f in c.findall('fields/field')}}
                 for c in tree.findall('components/comp')}
        pins = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                for net in tree.findall('nets/net') for n in net.findall('node')}
        errors += physical_errors(profile, parts, pins)
    return errors
