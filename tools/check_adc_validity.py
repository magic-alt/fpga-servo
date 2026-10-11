"""Physical-pin and static-corner contract for the ADC supply inhibit.

This is not an analog transient model or a guarantee of gate-off timing.
TPS3890 SLVSD65A: 1.15 V +/-1%, hysteresis <=0.825%, ISENSE <=100 nA.
TPS62901 SLVSFS7A: external FB 0.6 V +/-0.9%, IFB <=70 nA.
R93..R95: 0.05% initial, 10 ppm/C *100 C, 0.1% drift allocation.
R92: 0.1% /25ppm primary or 0.1% /10ppm alternate, common0.702% bound
covering reviewed individual qualification-test drift. This is not a lifetime guarantee.
"""
from pathlib import Path
import argparse
import itertools
import json
import xml.etree.ElementTree as ET


def verify(path):
    root = ET.parse(path).getroot()
    comps = {c.attrib['ref']: c for c in root.findall('./components/comp')}
    pins = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
            for net in root.findall('./nets/net') for n in net.findall('node')}
    errors = []
    for ref, value in {'U13': 'TPS62901RPJR', 'U25': 'TPS389001DSER',
                       'R92': '3.24k', 'R93': '1k', 'R94': '75k',
                       'R95': '10k', 'C94': '100nF'}.items():
        if ref not in comps or comps[ref].findtext('value') != value:
            errors.append(f'{ref}: ADC validity requires {value}')

    def same(*terms):
        nets = [pins.get((r, str(p))) for r, p in terms]
        if None in nets or len(set(nets)) != 1 or any(n and n.startswith('unconnected-') for n in nets):
            errors.append(f'ADC validity connection {terms}: {nets}')

    def rail(ref, pin, name):
        if pins.get((ref, str(pin))) != '/' + name:
            errors.append(f'{ref}.{pin}: ADC validity requires /{name}')

    for ref in ('R92', 'R93', 'R94', 'R95'):
        fields = {f.attrib['name']: f.text for f in comps.get(ref, ET.Element('comp')).findall('./fields/field')}
        tolerance, tcr = ('0.1%', '25ppm/C') if ref == 'R92' else ('0.05%', '10ppm/C')
        if fields.get('Tolerance') != tolerance or fields.get('TCR') != tcr:
            errors.append(f'{ref}: controlled {tolerance}, {tcr} resistor specification missing')
    # Actual TPS3890 DSE package numbering; not TPS3808-compatible.
    rail('U25', 4, 'VIO_3V3')
    rail('U25', 2, 'GND')
    rail('U25', 3, 'VIO_3V3')
    same(('U25', 6), ('U24', 1), ('U26', 1))
    same(('U25', 4), ('C91', 1))
    same(('U25', 2), ('C91', 2), ('C94', 2), ('R93', 2))
    same(('U25', 1), ('R92', 2), ('R93', 1))
    same(('U25', 5), ('C94', 1))
    rail('R92', 1, 'VA_5V')
    # External FB, forced PWM, 2.5 MHz with discharge; SS/TR deliberately open.
    for pin, name in ((6, 'VDRV_12V'), (5, 'VDRV_12V'), (7, 'VDRV_12V'),
                      (4, 'GND'), (1, 'PWR_GOOD'), (3, 'VA_5V')):
        rail('U13', pin, name)
    same(('U13', 2), ('L2', 1))
    same(('U13', 9), ('R94', 2), ('R95', 1))
    rail('R94', 1, 'VA_5V')
    rail('R95', 2, 'GND')
    if not pins.get(('U13', '8'), '').startswith('unconnected-'):
        errors.append('U13.SS/TR must be open for documented internal soft start')
    same(('U26', 7), ('U23', 6))
    same(('U23', 4), ('U20', 6))
    same(('U20', 5), ('U11', 6))

    tol = .0025  # R93..95 initial + temperature + allocated application drift
    r92_tol = .00702  # conservative common envelope; see sourcing qualification notes
    def bounds(ref, top, bottom, accuracy, leakage, top_tol=tol):
        values = [v * (1 + a / b) + current * a
                  for v, a, b, current in itertools.product(
                      (ref*(1-accuracy), ref*(1+accuracy)),
                      (top*(1-top_tol), top*(1+top_tol)),
                      (bottom*(1-tol), bottom*(1+tol)), (-leakage, leakage))]
        return min(values), max(values)
    fall = bounds(1.15, 3240, 1000, .01, 100e-9, r92_tol)
    recovery_max = fall[1] * 1.00825
    supply = bounds(.6, 75000, 10000, .009, 70e-9)
    if fall[0] <= 4.75 or recovery_max >= supply[0] - .01 or supply[1] + .01 >= 5.25:
        errors.append('static ADC inhibit/recovery margin insufficient')
    numeric = {'resistor_fractional_bounds': {'R92': r92_tol, 'R93_R94_R95': tol},
               'drift_scope': 'Prototype budget based on separate qualification tests/allocations; combined aging/environment and dynamic shutdown remain unqualified.',
               'falling_threshold_V': fall, 'rising_threshold_max_V': recovery_max,
               'regulated_static_V': supply, 'normal_negative_ripple_budget_V': .01,
               'adc_min_V': 4.75, 'adc_max_V': 5.25,
               'static_shutdown_headroom_V': fall[0] - 4.75,
               'transient_gate_off_qualified': False,
               'delay_note': '18us TPS3890 typical at 5% overdrive is NOT a guaranteed maximum; rapid droop and full-chain delay remain open.'}
    return errors, numeric


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    errors, numeric = verify(args.netlist)
    result = {'status': 'FAIL' if errors else 'PASS_STATIC_ONLY', 'errors': errors, 'calculations': numeric}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(errors))
