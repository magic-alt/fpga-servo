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
EXTERNAL_REMOVED_REFS = frozenset(['C1', 'C2', *[f'C{i}' for i in range(120, 128)],
                                    *[f'R{i}' for i in range(120, 130)]])


def evaluate_external(profile):
    """External assembly requirements, never an assertion of fitted hardware."""
    errors = []
    requirements = profile.get('external_requirements', {})
    keys = ('nominal_capacitance_uf', 'minimum_effective_capacitance_uf',
            'maximum_capacitance_uf', 'minimum_voltage_rating_v',
            'minimum_ripple_current_arms', 'maximum_bus_voltage_v',
            'discharge_target_v', 'maximum_discharge_time_s',
            'bleeder_resistance_ohm', 'bleeder_tolerance', 'bleeder_minimum_hot_power_w')
    for values, names in ((requirements, keys), (profile, (
            'continuous_phase_arms', 'peak_phase_amplitude_a', 'peak_duration_s', 'waveform_allowance'))):
        if not isinstance(values, dict) or any(
                not isinstance(values.get(k), (int, float)) or isinstance(values[k], bool)
                or not math.isfinite(values[k]) or values[k] <= 0 for k in names):
            return {}, ['External DC-link requires finite positive design inputs']
    if (profile['continuous_phase_arms'] < 10 or profile['peak_phase_amplitude_a'] < 20
            or profile['peak_duration_s'] < 30 or profile['waveform_allowance'] < 1.1):
        errors.append('Approved current, duration or waveform allowance was reduced')
    if profile.get('waveform') != 'BALANCED_SINUSOIDAL' or profile.get('branches') != []:
        errors.append('External mode requires balanced sinusoidal allocation and no onboard bank')
    if profile.get('qualification_status') != 'STATIC_DESIGN_ONLY_BENCH_OPEN':
        errors.append('External hardware qualification must remain open')
    demand = max(profile['continuous_phase_arms'] / math.sqrt(2),
                 profile['peak_phase_amplitude_a'] / 2) * profile['waveform_allowance']
    if (requirements['nominal_capacitance_uf'] < 1000
            or requirements['minimum_effective_capacitance_uf'] < 800
            or not requirements['minimum_effective_capacitance_uf'] <= requirements['nominal_capacitance_uf'] <= requirements['maximum_capacitance_uf']
            or requirements['minimum_voltage_rating_v'] < 100
            or requirements['minimum_ripple_current_arms'] < demand
            or not 48 <= requirements['maximum_bus_voltage_v'] <= 60):
        errors.append('External bank capacitance, voltage or allocated ripple requirement is insufficient')
    if not 0 < requirements['bleeder_tolerance'] < 1:
        return {}, errors + ['Invalid bleeder resistance tolerance']
    if not 0 < requirements['discharge_target_v'] <= 5 < requirements['maximum_bus_voltage_v']:
        return {}, errors + ['Discharge voltage must be within the reviewed envelope']
    resistance = requirements['bleeder_resistance_ohm']
    time = (resistance * (1 + requirements['bleeder_tolerance'])
            * requirements['maximum_capacitance_uf'] * 1e-6
            * math.log(requirements['maximum_bus_voltage_v'] / requirements['discharge_target_v']))
    power = requirements['maximum_bus_voltage_v'] ** 2 / (resistance * (1 - requirements['bleeder_tolerance']))
    if (requirements['maximum_discharge_time_s'] > 10 or time > requirements['maximum_discharge_time_s']
            or requirements['bleeder_minimum_hot_power_w'] < 2 * power):
        errors.append('External bleeder discharge time or hot power margin is insufficient')
    for key in ('independent_branch_protection_required', 'remain_connected_until_discharged',
                'bleeder_is_not_regeneration_sink'):
        if requirements.get(key) is not True:
            errors.append('Required external safety condition missing: ' + key)
    return {'required_external_ripple_arms': demand,
            'bleeder_worst_discharge_time_s': time, 'bleeder_worst_initial_power_w': power,
            'maximum_stored_energy_j': .5 * requirements['maximum_capacitance_uf'] * 1e-6
                                       * requirements['maximum_bus_voltage_v'] ** 2}, errors


def evaluate(profile):
    if profile.get('mode') == 'EXTERNAL_CAPACITOR_BLEEDER':
        return evaluate_external(profile)
    if profile.get('mode', 'DAMPED_ONBOARD_BANK') != 'DAMPED_ONBOARD_BANK':
        return {}, ['Unknown DC-link design mode']
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
    external = profile.get('mode') == 'EXTERNAL_CAPACITOR_BLEEDER'
    value = 'EXT_DC_LINK' if external else 'EXT_SINK'
    if parts.get('J7', {}).get('MPN') != '1714971' or parts.get('J7', {}).get('Value') != value:
        errors.append('J7: reviewed protected-bus sink connector is required')
    if pins.get(('J7', '1')) != '/VBUS_PROT' or pins.get(('J7', '2')) != '/GND':
        errors.append('External sink must connect directly after reverse protection')
    by_net = {}
    for node, net in pins.items():
        by_net.setdefault(net, set()).add(node)
    if pins.get(('RSH4', '1')) != '/VBUS_PROT' or pins.get(('RSH4', '2')) != '/VBUS_BRIDGE':
        errors.append('Bus shunt upstream/downstream force terminals changed')
    if external:
        if EXTERNAL_REMOVED_REFS.intersection(parts) or any(ref in EXTERNAL_REMOVED_REFS for ref, _ in pins):
            errors.append('Cancelled onboard DC-link bank must be absent')
        if {ref for ref, part in parts.items() if part.get('Value') in {'EXT_DC_LINK', 'EXT_SINK'}} != {'J7'}:
            errors.append('Exactly one external DC-link connector J7 is required')
        for ref, value in (('C3', '1uF'), ('C4', '100nF')):
            if (parts.get(ref, {}).get('Value') != value or pins.get((ref, '1')) != '/VBUS_PROT'
                    or pins.get((ref, '2')) != '/GND'):
                errors.append(ref + ': local high-frequency bus bypass must remain connected')
        return errors
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
    external = profile.get('mode') == 'EXTERNAL_CAPACITOR_BLEEDER'
    value = 'EXT_DC_LINK' if external else 'EXT_SINK'
    if authored.get('J7') != {'MPN': '1714971', 'Value': value} or rows.get('J7', {}).get('MPN') != '1714971':
        errors.append('J7: schematic/BOM must retain reviewed protected-bus sink interface')
    if external:
        if EXTERNAL_REMOVED_REFS.intersection(authored) or EXTERNAL_REMOVED_REFS.intersection(rows):
            errors.append('Cancelled onboard bank remains in schematic/BOM')
        if any(s.name == 'dc_link.kicad_sch' for s in discover_sheets(project)):
            errors.append('External mode must not retain the separate DC-link sheet')
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
