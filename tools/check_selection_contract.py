import xml.etree.ElementTree as ET
from pathlib import Path
import sys
r=ET.parse(sys.argv[1]).getroot()
refs={c.attrib['ref']: c for c in r.findall('./components/comp')}
pins={}
for net in r.findall('./nets/net'):
    for n in net.findall('node'):
        pins[(n.attrib['ref'],n.attrib['pin'])]=net.attrib['name']
e=[]
if 'J2' in refs: e.append('unused J2 is still fitted')
for i,phase in enumerate('UVW',1):
    ref=f'RSH{i}'
    actual={pin for comp,pin in pins if comp==ref}
    if actual!={'1','2'}:e.append(f'{ref}: SMD two-terminal shunt required, got {actual}')
    for pin,net in [('1',f'/SW_{phase}'),('2',f'/PH_{phase}')]:
        if pins.get((ref,pin))!=net:e.append(f'{ref}.{pin}: expected {net}')
    amp=f'U{i+1}'
    if refs[amp].findtext('value')!='INA240A1DR':e.append(f'{amp}: INA240A1DR required')
print('\n'.join(e) if e else 'Selection physical-pin contract PASS')
sys.exit(bool(e))
