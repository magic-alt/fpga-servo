"""Check exported KiCad netlist for critical safety and acquisition paths."""
from pathlib import Path
import sys
from kicad_native import extract_forms, head_string

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/ax7010_servo_reva.net")
text = path.read_text(encoding="utf-8")
errors = []
pin_nets = {}
net_nodes = {}
values = {}

def field(text, key):
    forms = extract_forms(text, key)
    return head_string(forms[0].text, key) if forms else None

for comp in extract_forms(text, "comp"):
    values[field(comp.text, "ref")] = field(comp.text, "value")
for net in extract_forms(text, "net"):
    name = field(net.text, "name")
    nodes = set()
    for node in extract_forms(net.text, "node"):
        key = (field(node.text, "ref"), field(node.text, "pin"))
        pin_nets[key] = name
        nodes.add(key)
    net_nodes[name] = nodes

def same(*pins):
    nets = [pin_nets.get(pin) for pin in pins]
    if None in nets or len(set(nets)) != 1 or nets[0].startswith("unconnected-"):
        errors.append(f"required connection missing: {pins}: {nets}")

def rail(ref, pin, name):
    if pin_nets.get((ref, pin)) != "/" + name:
        errors.append(f"{ref}.{pin} must connect to {name}")

if len(values) != 158 or len(net_nodes) != 180:
    errors.append(f"expected 158 components / 180 nets, got {len(values)} / {len(net_nodes)}")
for i, pin in enumerate(["3", "4", "5", "6", "7", "8", "9"]):
    ref = f"R{80 + i}"
    same(("J1", pin), (ref, "1"))
    rail(ref, "2", "GND")
    if values.get(ref) != "10k":
        errors.append(f"{ref}: required 10k reset-state pull-down missing")
for cap, ic, power, ground, supply in [
    ("C80", "U8", "8", "4", "VIO_3V3"),
    ("C81", "U9", "8", "4", "VIO_3V3"),
    ("C82", "U10", "8", "4", "VIO_3V3"),
    ("C83", "U11", "5", "2", "VIO_3V3"),
    ("C84", "U15", "3", "12", "VA_5V"),
    ("C85", "U16", "3", "12", "VA_5V"),
]:
    same((cap, "1"), (ic, power))
    same((cap, "2"), (ic, ground))
    rail(cap, "1", supply)
    rail(cap, "2", "GND")
    if values.get(cap) != "100nF":
        errors.append(f"{ic}: required 100nF local decoupling missing")
for cap in ["C43", "C44", "C45"]:
    rail(cap, "1", "VA_5V")
    rail(cap, "2", "GND")
for ref in values:
    if ref.startswith(("C", "R", "L")):
        nets = [net for (component, pin), net in pin_nets.items() if component == ref]
        if len(nets) > 1 and len(set(nets)) == 1:
            errors.append(f"{ref}: all terminals are on the same net")
for i in range(1, 7):
    same((f"RG{i}", "2"), (f"Q{i}", "4"), (f"RGS{i}", "1"))
for amp, resistor, adc_pin in [("U2", "R40", "49"), ("U3", "R41", "51"), ("U4", "R42", "53")]:
    # TI SBOSA30D Table 5-1: reserved pin 4 must connect to ground.
    rail(amp, "4", "GND")
    same((amp, "5"), (resistor, "1"))
    same((resistor, "2"), ("U6", adc_pin))
rail("U11", "1", "GATE_EN")
rail("U11", "3", "PWR_READY")
rail("U11", "6", "ARMED")
# Physical pins checked against the TI DCU/DBV/DCK package tables.
for ref, part in [("U20", "SN74LVC1G74"), ("U21", "SN74LVC1G17"),
                  ("U22", "SN74LVC1G14"), ("U23", "SN74LVC1G11"),
                  ("U24", "TPS3808G33"), ("U25", "TPS3808G50")]:
    if values.get(ref) != part:
        errors.append(f"{ref}: latch function requires {part}")

same(("U20", "5"), ("U11", "6"), ("R90", "1"), ("TP5", "1"))
same(("U20", "2"), ("U22", "4"))
same(("U20", "1"), ("U21", "4"))
same(("U20", "6"), ("U23", "4"), ("R91", "1"))
rail("U20", "7", "VIO_3V3")
rail("U22", "2", "GATE_EN")
same(("J1", "10"), ("R87", "1"), ("R88", "1"))
same(("R88", "2"), ("C92", "1"), ("U21", "2"))
same(("U23", "1"), ("U26", "5"))
rail("U26", "3", "OCP_N")
same(("U23", "3"), ("U26", "2"), ("U11", "3"))
rail("U26", "6", "PWR_GOOD")
rail("R55", "1", "PWR_GOOD")
rail("R55", "2", "VIO_3V3")
rail("R54", "1", "OCP_N")
rail("R54", "2", "VIO_3V3")
same(("U26", "1"), ("U24", "1"), ("U25", "1"), ("R89", "2"))
same(("U26", "7"), ("U23", "6"))
rail("U26", "8", "VIO_3V3")
rail("U26", "4", "GND")
same(("U26", "8"), ("C93", "1"))
same(("U26", "4"), ("C93", "2"))
if values.get("U26") != "SN74LVC3G17" or values.get("C93") != "100nF":
    errors.append("supervisor reset release requires U26 Schmitt conditioning and C93")
rail("R89", "1", "VIO_3V3")
for ref in ["R87", "R90", "R91", "C92"]:
    rail(ref, "2", "GND")
for ref, value in [("R87", "10k"), ("R88", "1k"), ("R89", "100k"),
                   ("R90", "10k"), ("R91", "10k"), ("C92", "1nF")]:
    if values.get(ref) != value:
        errors.append(f"{ref}: required latch bias/filter {value} missing")
for ic, cap, power, ground in [("U20", "C86", "8", "4"),
                               ("U21", "C87", "5", "3"),
                               ("U22", "C88", "5", "3"),
                               ("U23", "C89", "5", "2"),
                               ("U24", "C90", "6", "2"),
                               ("U25", "C91", "6", "2")]:
    rail(ic, power, "VIO_3V3")
    rail(ic, ground, "GND")
    same((ic, power), (cap, "1"))
    same((ic, ground), (cap, "2"))
    if values.get(cap) != "100nF":
        errors.append(f"{ic}: required 100nF latch decoupling missing")
for ic, sense in [("U24", "VIO_3V3"), ("U25", "VA_5V")]:
    rail(ic, "5", sense)
    rail(ic, "3", "VIO_3V3")
    if not (pin_nets.get((ic, "4")) or "").startswith("unconnected-"):
        errors.append(f"{ic}.CT must be open for fixed reset timeout")
if not (pin_nets.get(("U20", "3")) or "").startswith("unconnected-"):
    errors.append("U20 inverted Q must remain unconnected")

for gate, output, driver, pull in [("U8", "7", "1", "R56"), ("U9", "7", "2", "R58"),
                                   ("U10", "7", "3", "R60"), ("U8", "3", "4", "R57"),
                                   ("U9", "3", "5", "R59"), ("U10", "3", "6", "R61")]:
    same((gate, output), ("U1", driver), (pull, "1"))
    rail(pull, "2", "GND")
for gate in ["U8", "U9", "U10"]:
    same(("U11", "4"), (gate, "2"), (gate, "6"))
for esd_pin, receiver_pin in [("14", "1"), ("13", "2"), ("12", "4"), ("11", "5"), ("9", "10"), ("8", "11")]:
    same(("U19", esd_pin), ("U7", receiver_pin))
for esd_pin in ["5", "10"]:
    rail("U19", esd_pin, "GND")
for esd_pin in ["1", "2", "3", "4", "6", "7"]:
    if not (pin_nets.get(("U19", esd_pin)) or "").startswith("unconnected-"):
        errors.append(f"U19.{esd_pin}: RVZ NC pin must remain unconnected")
for phase, amp in [("U", "U2"), ("V", "U3"), ("W", "U4")]:
    rail(amp, "8", f"SW_{phase}")
    rail(amp, "1", f"PH_{phase}")
if errors:
    print("NETLIST SAFETY CHECK FAILED")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print(f"NETLIST SAFETY CHECK PASSED: {len(values)} components / {len(net_nodes)} nets")
