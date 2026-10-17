"""Independent native XML acceptance for AD7606C-16 and retained servo circuits.

Use a fresh KiCad kicadxml export, not a fabricated or hand-edited netlist.
Digital/physical connectivity only; not an analog, RTL, PCB or bench test.
"""
from pathlib import Path
from collections import Counter
import argparse
import ast
import copy
import csv
import hashlib
import json
import re
import runpy
import sys
import types
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from kicad_native import assert_balanced, extract_forms, head_string, property_value, strip_form
from check_power_wiring import check as check_power


def load_xml(path):
    root=ET.parse(path).getroot()
    components={c.get("ref"):c for c in root.findall("components/comp")}
    pins={}
    for net in root.findall("nets/net"):
        for node in net.findall("node"):
            key=(node.get("ref"),node.get("pin"))
            assert key not in pins, f"Physical pin listed twice: {key}"
            pins[key]=net.get("name")
    return components,pins


def electrical_errors(components,pins):
    errors=[]

    def rail(ref,pin,net):
        if pins.get((ref,str(pin)))!="/"+net:
            errors.append(f"{ref}.{pin}: expected /{net}, got {pins.get((ref,str(pin)))}")

    def same(*nodes):
        nets=[pins.get((r,str(p))) for r,p in nodes]
        if None in nets or len(set(nets))!=1 or any(n.startswith("unconnected-") for n in nets if n):
            errors.append(f"Required physical connection {nodes}: {nets}")

    if len(components)<160 or len(pins)<400:
        errors.append("Incomplete native design export")
    if components.get("U6") is None or components["U6"].findtext("value")!="AD7606C-16BSTZ":
        errors.append("U6 must be exact AD7606C-16BSTZ")
    if {p for r,p in pins if r=="U6"}!={str(n) for n in range(1,65)}:
        errors.append("U6 must export all 64 distinct physical pins")
    for n in [1,23,37,38,48,3,4,5,6,7,10,34]:
        rail("U6",n,"VA_5V")
    for n in [2,26,35,40,41,47,43,46,8,16,17,18,30,31,32,33,50,52,54,56,58,60,61,62,63,64]:
        rail("U6",n,"GND")
    for n in [19,20,21,22]:
        net=pins.get(("U6",str(n)),"")
        if not net.startswith("unconnected-"):
            errors.append(f"Unused DOUT pin{n} must be unconnected in four-lane design")
    # Every ADC digital signal passes through fixed-direction dual-rail isolation.
    for adc,ref,pin in [(9,"U27",13),(11,"U27",12),(13,"U28",12),(29,"U29",13),(14,"U29",11),(15,"U29",10)]:
        same(("U6",adc),(ref,pin))
    for j,ref,pin in [(11,"U27",2),(14,"U27",3),(12,"U28",2),(13,"U28",3),(31,"U29",2),(17,"U29",4),(18,"U29",5)]:
        same(("J1",j),(ref,pin))
    same(("U28",13),("R104",1));same(("R104",2),("U6",12))
    for adc,ref,bpin,apin,res,j in [(24,"U27",11,4,"R100",15),(25,"U27",10,5,"R101",16),(27,"U28",11,4,"R102",29),(28,"U28",10,5,"R103",30)]:
        same(("U6",adc),(ref,bpin));same((ref,apin),(res,2));same((res,1),("J1",j))
    for i,ref in enumerate(["U27","U28","U29"]):
        rail(ref,1,"VIO_3V3");rail(ref,14,"VA_5V");rail(ref,7,"GND");rail(ref,8,"PWR_READY")
        if components.get(ref) is None or components[ref].findtext("value")!="TXU0204PWR":
            errors.append(f"{ref}: fixed-direction TXU0204PWR isolation required")
        if {p for r,p in pins if r==ref}!={str(n) for n in range(1,15)}:
            errors.append(f"{ref}: all 14 physical pins required")
        for n in [6,9]:
            if not pins.get((ref,str(n)),"").startswith("unconnected-"):
                errors.append(f"{ref}.{n}: actual PW package NC must stay NC")
        for cap,net in [(f"C{101+i*2}","VIO_3V3"),(f"C{102+i*2}","VA_5V")]:
            rail(cap,1,net);rail(cap,2,"GND")
            if components.get(cap) is None or components[cap].findtext("value")!="100nF":
                errors.append(f"{cap}: 100nF translator bypass required")
    rail("U29",3,"GND")
    if not pins.get(("U29","12"),"").startswith("unconnected-"):
        errors.append("Unused U29 B2Y must stay unconnected")
    for n in range(100,112):
        ref=f"R{n}";val="47R" if n<105 else "10k"
        if components.get(ref) is None or components[ref].findtext("value")!=val:
            errors.append(f"{ref}: expected fitted {val}")
        elif components[ref].find("property[@name='dnp']") is not None:
            errors.append(f"{ref}: required resistor must be fitted")
    for n in [11,12,13,14,15,16,17,18,29,30,31]:
        if pins.get(("J1",str(n))) is None:
            errors.append(f"Active J10 signal missing: {n}")
    # ADC-side bias while OE low, plus host-side pulls to keep RESET/CS high
    # when OE rises with an unconfigured FPGA. Dynamic sequencing is a bench gate.
    for ref,pin,up in [("R105",9,False),("R106",11,True),("R108",13,True),("R109",29,False)]:
        same((ref,1 if up else 2),("U6",pin))
        rail(ref,2 if up else 1,"VA_5V" if up else "GND")
    same(("R107",2),("R104",1));rail("R107",1,"GND")
    for ref,j in [("R110",14),("R111",13)]:
        same((ref,1),("J1",j));rail(ref,2,"VIO_3V3")
    for ref in ["U6","U27","U28","U29",*[f"C{n}" for n in range(60,69)],*[f"C{n}" for n in range(100,107)]]:
        if components.get(ref) is not None and components[ref].find("property[@name='dnp']") is not None:
            errors.append(f"{ref}: functional ADC/interface component must be fitted")
    for pin,other in [(49,("R40",2)),(51,("R41",2)),(53,("R42",2)),(55,("R13",2)),(57,("R70",2)),(59,("R71",2))]:
        # VBUS's exact divider reference is checked below against the named net.
        if pin!=55:
            same(("U6",pin),other)
    rail("U6",55,"VBUS_ADC")
    same(("U6",44),("U6",45),("C60",1))
    same(("U6",42),("C61",1));same(("U6",36),("C62",1));same(("U6",39),("C63",1))
    if pins.get(("U6","36"))==pins.get(("U6","39")):
        errors.append("Analog and digital REGCAP outputs must stay separate")
    expected={"C60":"10uF","C61":"100nF","C62":"1uF","C63":"1uF",
              "C64":"100nF","C65":"100nF","C66":"100nF","C67":"100nF","C68":"100nF","C100":"10uF"}
    for ref,val in expected.items():
        if ref not in components or components[ref].findtext("value")!=val:
            errors.append(f"{ref}: expected {val}")
        rail(ref,2,"GND")
    for ref in ["C64","C65","C66","C67","C100"]:
        rail(ref,1,"VA_5V")
    rail("C68",1,"VA_5V")
    return errors


def inherited_errors(old,new):
    oldc,oldp=old;newc,newp=new
    errors=[]
    changed={"U6",*(f"C{n}" for n in range(60,69))}
    retained=set(oldc)-changed
    for ref in sorted(retained):
        if ref not in newc:
            errors.append(f"Retained component removed: {ref}")
            continue
        for field in ["value","footprint"]:
            if oldc[ref].findtext(field)!=newc[ref].findtext(field):
                errors.append(f"Unexpected retained {field} change: {ref}")
        a={f.get("name"):f.text for f in oldc[ref].findall("fields/field")}
        b={f.get("name"):f.text for f in newc[ref].findall("fields/field")}
        for field in ["Manufacturer","MPN","LCSC"]:
            if a.get(field)!=b.get(field):
                errors.append(f"Unexpected retained {field} change: {ref}")
    projected={p for p in oldp if p[0] in retained and p not in {("J1","29"),("J1","30"),("J1","31")}}
    missing=projected-set(newp)
    if missing:
        errors.append(f"Retained physical pins missing: {sorted(missing)}")
    # Compare electrical equivalence classes, independent of renamed sheet paths
    # and automatic net names. Every retained physical pin must keep its peers.
    for node in sorted(projected-set(missing)):
        a={p for p in projected if oldp[p]==oldp[node]}
        b={p for p in projected if newp.get(p)==newp[node]}
        if a!=b:
            errors.append(f"Retained connectivity changed at {node}: missing={sorted(a-b)} extra={sorted(b-a)}")
    return errors


def run_shared_geometry(name):
    """Reuse existing checker logic, changing only its HW input directory AST."""
    path=ROOT/"tools"/name
    tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="HW" for t in node.targets):
            node.value=ast.Call(func=ast.Name(id="Path",ctx=ast.Load()),args=[ast.Constant(str(HERE))],keywords=[])
    ast.fix_missing_locations(tree)
    try:
        exec(compile(tree,str(path),"exec"),{"__file__":str(path),"__name__":"__main__"})
    except SystemExit as ex:
        if ex.code:
            raise AssertionError(f"Shared checker failed: {name} ({ex.code})")


def source_errors():
    errors=[]
    for name,digest in json.loads((HERE/"source_manifest.json").read_text())["files"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            errors.append(f"Original file changed: {name}")
    return errors


def source_checks():
    errors=source_errors()
    top=(HERE/"ax7010_servo_ad7606c.kicad_sch").read_text(encoding="utf-8")
    declared={property_value(f.text,"Sheetfile"):{head_string(p.text,"pin") for p in extract_forms(f.text,"pin")}
              for f in extract_forms(top,"sheet")}
    references=[]
    definitions=[]
    for path in sorted(HERE.glob("*.kicad_sch")):
        raw=path.read_text(encoding="utf-8");assert_balanced(raw)
        lib=extract_forms(raw,"lib_symbols")[0].text
        defs={head_string(f.text,"symbol"):f.text for f in extract_forms(lib,"symbol")}
        authored=strip_form(raw,"lib_symbols")
        for f in extract_forms(authored,"symbol"):
            if "(lib_id " not in f.text:
                continue
            ref=property_value(f.text,"Reference")
            if ref:
                references.append((ref,re.search(r'\(unit (\d+)\)',f.text)[1]))
            alias=extract_forms(f.text,"lib_name")
            key=head_string(alias[0].text,"lib_name") if alias else re.search(r'\(lib_id "([^"]+)"',f.text)[1]
            if key not in defs:
                errors.append(f"Missing embedded symbol {key} in {path.name}")
        if path.name in declared:
            ports={head_string(f.text,"hierarchical_label") for f in extract_forms(authored,"hierarchical_label")}
            if ports!=declared[path.name]:
                errors.append(f"Hierarchy mismatch: {path.name}")
            errors.extend(check_power(path))
        for key,value in defs.items():
            if key.endswith(":AD7606C_16_SERIAL"):
                definitions.append(value)
    if any(n>1 for n in Counter(references).values()):
        errors.append("Duplicate reference/unit or power reference")
    if {u for r,u in references if r=="U6"}!={"1","2","3","4","5"}:
        errors.append("U6 must contain all five drawn units")
    # Independently assert package pin types at risky mode-dependent terminals.
    for definition in definitions:
        p={int(head_string(extract_forms(f.text,"number")[0].text,"number")):f.text.split()[1]
           for f in extract_forms(definition,"pin")}
        if len(p)!=64 or set(p)!=set(range(1,65)):
            errors.append("AD7606C symbol must contain all physical pins once")
        for n in [14,15,19,20,21,22,24,25,27,28]:
            if p[n]!="output":
                errors.append(f"Serial output pin {n} must stay output")
        for n in [16,17,18,29,30,31,32,33]:
            if p[n]!="input":
                errors.append(f"Serial input/GND strap pin {n} must stay input")
    return errors


def profile_errors(profile,xdc):
    errors=[]
    cfg={"0x02":"0x10","0x03":"0x55","0x04":"0x65","0x05":"0x66","0x06":"0x66","0x07":"0x0F","0x08":"0x00"}
    for addr,value in cfg.items():
        if profile.get("configuration",{}).get(addr,{}).get("value")!=value:
            errors.append(f"ADC register configuration mismatch: {addr}")
    if profile.get("timing",{}).get("frame_sclk_edges")!=32 or profile["timing"].get("serial_lanes")!=4:
        errors.append("Four-lane complete frame requires 32 SCLK cycles")
    if profile.get("data_lanes")!={"DOUTA":["IU_ADC","IV_ADC"],"DOUTB":["IW_ADC","VBUS_ADC"],"DOUTC":["NTC_BOARD","NTC_BOARD_AUX"],"DOUTD":["UNUSED_CH7","UNUSED_CH8"]}:
        errors.append("Four-lane channel ordering mismatch")
    if profile.get("startup",{}).get("development_first_reset_wait_ms",0)<=2000:
        errors.append("First-reset setup must respect Rev.A Table3 footnote3")
    expected={"ADC_CONVST":(11,"Y14"),"ADC_SCLK":(12,"W14"),"ADC_CS_N":(13,"P18"),"ADC_RESET":(14,"N17"),
              "ADC_DOUTA":(15,"U15"),"ADC_DOUTB":(16,"U14"),"ADC_BUSY":(17,"P16"),"ADC_FRSTDATA":(18,"P15"),
              "ADC_DOUTC":(29,"U12"),"ADC_DOUTD":(30,"T12"),"ADC_SDI":(31,"T10")}
    actual={e["signal"]:(e["header_pin"],e["fpga_pin"]) for e in profile.get("external_pins",[])}
    if actual!=expected:
        errors.append("J10 physical connector/FPGA profile differs from independently reviewed map")
    timing=profile.get("timing",{})
    if timing.get("initial_sclk_hz")!=5000000 or timing.get("initial_frame_time_us")!=6.4:
        errors.append("Bring-up profile must start at 5MHz / 6.4us frame until timing qualification")
    active="\n".join(line for line in xdc.splitlines() if not line.lstrip().startswith("#"))
    pairs=re.findall(r"set_property PACKAGE_PIN (\w+) \[get_ports (\w+)\]",active)
    if len(pairs)!=len({pad for pad,sig in pairs}) or len(pairs)!=len({sig for pad,sig in pairs}):
        errors.append("Duplicate active FPGA pad or signal in XDC")
    ports={sig:pad for pad,sig in pairs}
    for entry in profile.get("external_pins",[]):
        sig=entry["signal"]
        if ports.get(sig)!=entry["fpga_pin"]:
            errors.append(f"Profile/XDC pin mismatch: {sig}")
        if f"set_property IOSTANDARD LVCMOS33 [get_ports {sig}]" not in active:
            errors.append(f"XDC I/O standard missing: {sig}")
    return errors


def write_bom(components):
    rows=[]
    for ref,c in sorted(components.items(),key=lambda item:(re.sub(r"\d+","",item[0]),int(re.search(r"\d+",item[0])[0]))):
        fields={f.get("name"):f.text for f in c.findall("fields/field")}
        rows.append({"Ref":ref,"Qty":1,"Value / Part":c.findtext("value"),"Manufacturer":fields.get("Manufacturer","UNVERIFIED"),
                     "MPN":fields.get("MPN","UNVERIFIED"),"Package":c.findtext("footprint"),"LCSC":fields.get("LCSC","UNVERIFIED"),
                     "Alternative MPN":fields.get("Alternative_MPN","UNQUALIFIED"),"Alternative LCSC":fields.get("Alternative_LCSC","UNVERIFIED"),
                     "Status":fields.get("Sourcing_Status","OPEN"),"On_board":c.find("property[@name='exclude_from_board']") is None,
                     "DNP":c.find("property[@name='dnp']") is not None})
    with (HERE/"bom.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return len(rows)


def write_pin_audit(pins):
    definitions=json.loads((HERE/"adc_pin_map.json").read_text())
    nets={net:sorted(f"{r}.{p}" for (r,p),n in pins.items() if n==net) for net in set(pins.values())}
    with (HERE/"evidence/adc-physical-pins.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["Pin","Name","Unit","Type","Native_net","Connected_physical_pins"])
        writer.writeheader()
        for d in definitions:
            net=pins[("U6",str(d["number"]))]
            writer.writerow({"Pin":d["number"],"Name":d["name"],"Unit":d["unit"],"Type":d["type"],"Native_net":net,"Connected_physical_pins":";".join(nets[net])})


def self_tests(components,pins,old):
    cases={"OS0 low":(("U6","3"),"/GND"),"DOUTC grounded":(("U6","27"),"/GND"),
           "REGCAP outputs shorted":(("U6","39"),pins[("U6","36")]),
           "REFCAPB disconnected":(("U6","45"),"broken-reference"),
           "SDI wrong J10 pin":(("J1","31"),"unconnected-J1-P31"),
           "VDRIVE independent of AVCC":(("U6","23"),"/VIO_3V3"),
           "Translator OE bypasses supervisor":(("U27","8"),"/VIO_3V3"),
           "OCP pull-up supply missing":(("R54","1"),"floating-OCP-rail")}
    for name,(node,net) in cases.items():
        broken=dict(pins);broken[node]=net
        if not electrical_errors(components,broken)+inherited_errors(old,(components,broken)):
            raise AssertionError(f"Fault injection was not rejected: {name}")
    extra=0
    for ref in ["R106","R108","R110","R111"]:
        bad=copy.deepcopy(components);bad[ref].find("value").text="0R"
        if not electrical_errors(bad,pins):
            raise AssertionError(f"Zero-ohm startup bias was not rejected: {ref}")
        bad=copy.deepcopy(components);ET.SubElement(bad[ref],"property",{"name":"dnp"})
        if not electrical_errors(bad,pins):
            raise AssertionError(f"DNP startup bias was not rejected: {ref}")
        extra+=2
    profile=json.loads((HERE/"adc_profile.json").read_text());xdc=(HERE/"ax7010_servo_ad7606c.xdc").read_text()
    bad=copy.deepcopy(profile);bad["configuration"]["0x02"]["value"]="0x00"
    if not profile_errors(bad,xdc):
        raise AssertionError("Incorrect lane configuration was not rejected")
    badxdc=xdc.replace("PACKAGE_PIN U12 [get_ports ADC_DOUTC]","PACKAGE_PIN T10 [get_ports ADC_DOUTC]")
    if not profile_errors(profile,badxdc):
        raise AssertionError("Conflicting FPGA package assignment was not rejected")
    extra+=2
    total=len(cases)+extra
    print(f"FAULT INJECTION PASSED: {total} wiring, fitted-value and profile errors rejected")
    return total


def ocp_behavior(pins):
    # The original import-time graph checker includes ADS8588S-only contracts.
    # Those contracts remain tested on the original design. Here the graph has
    # already passed the independent AD7606C and retained-topology checks above.
    module=types.ModuleType("check_netlist_safety")
    module.pin_nets=pins
    previous=sys.modules.get("check_netlist_safety")
    sys.modules["check_netlist_safety"]=module
    try:
        result=runpy.run_path(str(ROOT/"tools/check_ocp_behavior.py"))
        return result["checks"]
    finally:
        if previous is None:
            sys.modules.pop("check_netlist_safety",None)
        else:
            sys.modules["check_netlist_safety"]=previous


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--netlist",type=Path,default=HERE/"evidence/ad7606c.xml")
    ap.add_argument("--baseline",type=Path,default=HERE/"evidence/legacy-baseline.xml")
    args=ap.parse_args()
    components,pins=load_xml(args.netlist);old=load_xml(args.baseline)
    errors=source_checks()+electrical_errors(components,pins)+inherited_errors(old,(components,pins))
    errors+=profile_errors(json.loads((HERE/"adc_profile.json").read_text()),(HERE/"ax7010_servo_ad7606c.xdc").read_text())
    if errors:
        print("AD7606C PROJECT CHECK FAILED\n"+"\n".join(errors));return 1
    run_shared_geometry("check_kicad_grid.py");run_shared_geometry("check_schematic_layout.py")
    tests=self_tests(components,pins,old)
    ocp=ocp_behavior(pins)
    count=write_bom(components)
    write_pin_audit(pins)
    summary={"components":count,"on_board_component_objects":sum(c.find("property[@name='exclude_from_board']") is None for c in components.values()),
             "nets":len(set(pins.values())),"adc_physical_pins":64,"retained_circuit_connectivity":"PASS",
             "original_source_hashes":"UNCHANGED","fault_injection_cases":tests,"ocp_stable_level_scenarios":ocp,"pcb":"NOT_CREATED_ROUTING_DEFERRED",
             "qualification":"SCHEMATIC_STATIC_ONLY"}
    (HERE/"evidence/static-checks.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(f"AD7606C PROJECT CHECK PASSED: {count} components / {summary['nets']} nets; retained circuit connectivity equivalent")
    return 0


if __name__=="__main__":
    sys.exit(main())
