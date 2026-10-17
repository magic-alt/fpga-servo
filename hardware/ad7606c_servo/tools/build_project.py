"""Reproduce the independent AD7606C schematic from the immutable Rev.A source.

Only writes inside this new project. Existing schematic objects are selected as
balanced native forms; no unrestricted coordinate or pin-number substitutions.
Run from the repository root. Requires the source SHA recorded in README.md.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
import build_levelshift

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
LEGACY_HW = ROOT / "hardware" / "ads8588s_servo"
sys.path.insert(0, str(ROOT / "tools"))
from kicad_native import (extract_forms, head_string, parse_at, parse_xy,
                          property_value, strip_form, _scan_balanced)

PROJECT = "ax7010_servo_ad7606c"
LIB = "ax7010_servo_reva"  # copied library name retained for reused symbols
BASE = "17166bc"
NAMESPACE = uuid.UUID("52638370-91a7-4c55-8f6e-ed051ab857d4")


def uid(key):
    return str(uuid.uuid5(NAMESPACE, key))


ROOT_ID = uid("system")
SHEETS = ["power_input", "aux_power", "gate_inverter", "current_adc",
          "adc_core", "adc_power", "ax7010_interface", "ocp_latch", "encoder", "adc_levelshift"]
sheet_ids = {name: uid("sheet-" + name) for name in SHEETS}
counter = 0


def fresh():
    global counter
    counter += 1
    return uid(f"generated-{counter}")


def q(s):
    return json.dumps(str(s), ensure_ascii=False)


def num(n):
    return f"{n:.6f}".rstrip("0").rstrip(".")


def at(x, y, angle=0):
    return f"(at {num(x)} {num(y)} {angle})"


def effects(size=1.016, more=""):
    return f"(effects (font (size {size} {size})) {more})"


def prop(name, value, x=0, y=0, visible=False):
    return f"(property {q(name)} {q(value)} {at(x,y)} {effects(1.016, '' if visible else '(hide yes)')})"


def children(text):
    """Return only direct child forms, preserving each form's source bytes."""
    pos = text.index("(") + 1
    while pos < len(text):
        if text[pos] == "(":
            end = _scan_balanced(text, pos)
            yield text[pos:end]
            pos = end
        elif text[pos] == '"':
            match = re.match(r'"(?:\\.|[^"\\])*"', text[pos:])
            pos += len(match[0])
        else:
            pos += 1


def head(form):
    return re.match(r"\(([^\s()]+)", form)[1]


def source(name):
    # BASE predates the directory reorganization; its historical Git path stays.
    return subprocess.check_output(["git", "show", f"{BASE}:hardware/{name}"],
                                   cwd=ROOT).decode("utf-8")


def rename_instances(text, name):
    # Each project/path form is bounded; component UUIDs and unaffected wires stay.
    old_root = re.search(r'\(uuid "([^"]+)"', source("ax7010_servo_reva.kicad_sch"))[1]
    text = text.replace('(project "ax7010_servo_reva"', f'(project "{PROJECT}"')
    for f in extract_forms(text, "path"):
        path = head_string(f.text, "path")
        if path and path.startswith("/" + old_root):
            text = text.replace(f.text, re.sub(r'\(path "[^"]+"',
                f'(path "/{ROOT_ID}/{sheet_ids[name]}"', f.text, count=1), 1)
    return text


def wire(a, b):
    assert a != b and (a[0] == b[0] or a[1] == b[1]), (a,b)
    return f'(wire (pts (xy {num(a[0])} {num(a[1])}) (xy {num(b[0])} {num(b[1])})) (stroke (width 0) (type default)) (uuid "{fresh()}"))'


def label(name, x, y, hierarchy=False, shape="input", angle=0, right=False):
    if hierarchy:
        return f'(hierarchical_label {q(name)} (shape {shape}) {at(x,y,angle)} {effects(1.016, "(justify left)" if angle == 0 else "(justify right)")} (uuid "{fresh()}"))'
    return f'(label {q(name)} {at(x,y,angle)} {effects(.9, "(justify right bottom)" if right else "(justify left bottom)")} (uuid "{fresh()}"))'


def text(value, x, y, size=1.27):
    return f'(text {q(value)} {at(x,y)} {effects(size, "(justify left bottom)")} (uuid "{fresh()}"))'


def junction(x,y):
    return f'(junction (at {num(x)} {num(y)}) (diameter 0) (color 0 0 0 0) (uuid "{fresh()}"))'


def no_connect(x,y):
    return f'(no_connect (at {num(x)} {num(y)}) (uuid "{fresh()}"))'


all_defs = {}
templates = {}
for name in SHEETS:
    if name in {"adc_core", "adc_power", "adc_levelshift"}:
        continue
    raw = source(name + ".kicad_sch")
    for f in children(extract_forms(raw,"lib_symbols")[0].text):
        if head(f) == "symbol":
            all_defs[head_string(f,"symbol")] = f
    for f in children(raw):
        if head(f) == "symbol" and "(lib_id " in f:
            templates[property_value(f,"Reference")] = f


def component(name, ref, value, x,y,sheet,unit=1,angle=0,metadata=None):
    ident = uid("component-" + ref) if ref == "U6" else fresh()
    flags = "(in_bom yes) (on_board yes) (in_pos_files yes) (dnp no)"
    if ref.startswith("#"):
        flags = "(in_bom no) (on_board no) (in_pos_files no)"
    result = f'(symbol (lib_id "{LIB}:{name}") {at(x,y,angle)} (unit {unit}) {flags} (uuid "{ident}")'
    # Unit UUID must differ although all five units belong to the same U6.
    if ref == "U6":
        result = result.replace(ident, uid(f"U6-unit-{unit}"))
    result += prop("Reference", ref, x+2.54, y-2.54, not ref.startswith("#"))
    result += prop("Value", value, x+2.54, y+2.54, not ref.startswith("#"))
    for key,val in (metadata or {}).items():
        result += prop(key,val,x,y)
    result += f'(instances (project "{PROJECT}" (path "/{ROOT_ID}/{sheet_ids[sheet]}" (reference "{ref}") (unit {unit})))))'
    return result


def passive(template,ref,x,y,sheet,description=None,angle=0):
    t = templates[template]
    meta = {head_string(f.text,"property"): re.match(r'\(property\s+"(?:\\.|[^"\\])*"\s+"((?:\\.|[^"\\])*)"',f.text)[1]
            for f in extract_forms(t,"property")}
    meta = {k:json.loads('"'+v+'"') for k,v in meta.items()}
    name = re.search(r'\(lib_id "[^:]+:([^"]+)"',t)[1]
    value = meta.pop("Value")
    meta.pop("Reference")
    if description:
        meta["Description"] = description
    return component(name,ref,value,x,y,sheet,angle=angle,metadata=meta)


power_count = 5000


def power(net,x,y,sheet):
    global power_count
    power_count += 1
    return component("PWR_"+net,f"#PWR{power_count}","/"+net,x,y,sheet)


def header(name, title, definitions):
    return f'(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "{uid("page-"+name)}") (paper "A4") (title_block (title {q(title)}) (date "2026-10-17") (rev "B-DEV") (company "magic-alt/fpga-servo") (comment 1 "AD7606C independent development schematic; release gates OPEN")) (lib_symbols {definitions})'


# AD7606C Rev.A Table 9: every package pin appears in exactly one unit.
# Digital types describe the selected serial/software operating mode.
units = {i:[] for i in range(1,6)}
pins = {}


def pin(unit,number,name,kind,x,y,angle):
    assert number not in pins
    pins[number] = dict(number=number,name=name,type=kind,unit=unit,x=x,y=y,angle=angle)
    units[unit].append(f'(pin {kind} line {at(x,y,angle)} (length 7.62) (name {q(name)} {effects(.85)}) (number "{number}" {effects(.85)}))')


for ch in range(1,9):
    pin(1,47+ch*2,f"V{ch}+","input",-25.4,33.02-(ch-1)*7.62,0)
    pin(1,48+ch*2,f"V{ch}-","input",25.4,33.02-(ch-1)*7.62,180)
for i,(n,nm) in enumerate([(9,"CONVST"),(11,"RESET"),(12,"SCLK"),(13,"CS_N"),(29,"SDI")]):
    pin(2,n,nm,"input",-25.4,35.56-i*7.62,0)
for i,(n,nm) in enumerate([(24,"DOUTA"),(25,"DOUTB"),(27,"DOUTC"),(28,"DOUTD"),(14,"BUSY"),(15,"FRSTDATA"),(19,"DOUTE"),(20,"DOUTF"),(21,"DOUTG"),(22,"DOUTH")]):
    pin(2,n,nm,"output",25.4,35.56-i*7.62,180)
for i,n in enumerate([16,17,18,30,31,32,33]):
    pin(2,n,f"DB{n-16 if n < 19 else n-18}_SER_GND","input",-25.4,-10.16-i*2.54,0)
for i,(n,nm) in enumerate([(3,"OS0"),(4,"OS1"),(5,"OS2"),(6,"PAR_SER_SEL"),(7,"STBY"),(10,"WR_N"),(34,"REF_SELECT")]):
    pin(3,n,nm,"input",-22.86,20.32-i*5.08,0)
pin(3,8,"RANGE","input",22.86,-10.16,180)
for i,n in enumerate([1,37,38,48]):
    pin(4,n,"AVCC","power_in",-50.8+i*30.48,12.7,270)
pin(4,23,"VDRIVE","power_in",71.12,12.7,270)
for i,n in enumerate([2,26,35,40,41,47,43,46]):
    pin(4,n,"REFGND" if n in [43,46] else "AGND","power_in",-57.15+i*17.78,-33.02,90)
pin(5,36,"REGCAP_A","passive",-38.1,12.7,0)
pin(5,39,"REGCAP_D","passive",-38.1,-12.7,0)
pin(5,42,"REFIN_REFOUT","passive",38.1,12.7,180)
pin(5,44,"REFCAPA","passive",38.1,-12.7,180)
pin(5,45,"REFCAPB","passive",38.1,-20.32,180)
assert set(pins) == set(range(1,65))

ADC = '(symbol "AD7606C_16_SERIAL" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)'
ADC += prop("Reference","U",0,0) + prop("Value","AD7606C_16_SERIAL",0,0)
ADC += prop("Footprint","Package_QFP:LQFP-64_10x10mm_P0.5mm")
ADC += prop("Datasheet","https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf")
rects={1:(-17.78,40.64,17.78,-27.94),2:(-17.78,43.18,17.78,-40.64),3:(-15.24,27.94,15.24,-17.78),4:(-68.58,5.08,78.74,-25.4),5:(-30.48,20.32,30.48,-27.94)}
for unit,records in units.items():
    x1,y1,x2,y2=rects[unit]
    ADC += f'(symbol "AD7606C_16_SERIAL_{unit}_1" (rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width .254) (type default)) (fill (type background)))'+''.join(records)+')'
ADC += ')'
all_defs[LIB+":AD7606C_16_SERIAL"]=ADC.replace('(symbol "AD7606C_16_SERIAL"',f'(symbol "{LIB}:AD7606C_16_SERIAL"',1)
TXU=build_levelshift.symbol(prop,effects,at)
all_defs[LIB+":TXU0204PW"]=TXU.replace('(symbol "TXU0204PW"',f'(symbol "{LIB}:TXU0204PW"',1)
adcmeta={"Manufacturer":"Analog Devices","MPN":"AD7606C-16BSTZ","LCSC":"C5371769",
         "Alternative_MPN":"AD7606C-16BSTZ-RL","Alternative_LCSC":"C5240947",
         "Alternative_Status":"Packaging only; same silicon and ST-64-2 package",
         "Footprint":"Package_QFP:LQFP-64_10x10mm_P0.5mm",
         "Datasheet":"https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf",
         "Description":"8ch simultaneous 16-bit ADC; serial software mode, four DOUT lanes",
         "Sourcing_Status":"Development selection; refresh actual quote before purchasing"}


def adc(unit,x,y,sheet):
    return component("AD7606C_16_SERIAL","U6","AD7606C-16BSTZ",x,y,sheet,unit,metadata=adcmeta)


def write_sheet(name,records,title):
    used=set()
    for r in records:
        if head(r)=="symbol" and '(lib_id ' in r:
            alias=extract_forms(r,"lib_name")
            used.add(head_string(alias[0].text,"lib_name") if alias else re.search(r'\(lib_id "([^"]+)"',r)[1])
    definitions='\n'.join(all_defs[n] for n in sorted(used))
    (HERE/(name+".kicad_sch")).write_text(header(name,title,definitions)+'\n'+'\n'.join(records)+'\n(embedded_fonts no))\n',encoding="utf-8")


def build():
    HERE.mkdir(exist_ok=True)
    branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()
    if not branch or branch in {"main","master"}:
        raise RuntimeError("Generate hardware only on a topic branch")
    # Save source file hashes; reject dirty source drift rather than copying it.
    manifest={"base_commit":subprocess.check_output(["git","rev-parse",BASE],cwd=ROOT,text=True).strip(),"files":{},"text_sha256_lf":{},"original_paths":{},"text_hash_policy":"UTF-8 with LF line endings; files retains original byte hashes"}
    for path in sorted(LEGACY_HW.iterdir()):
        if path.is_file() and (path.suffix in {".kicad_sch",".kicad_sym",".kicad_pro",".kicad_pcb",".kicad_dru"} or path.name in {"bom.csv","sym-lib-table","fp-lib-table"}):
            name=path.relative_to(ROOT).as_posix()
            manifest["files"][name]=hashlib.sha256(path.read_bytes()).hexdigest()
            manifest["text_sha256_lf"][name]=hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            manifest["original_paths"][name]="hardware/"+path.name
    (HERE/"source_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    for name in SHEETS:
        if name in {"adc_core","adc_power","adc_levelshift","current_adc","ax7010_interface"}:
            continue
        (HERE/(name+".kicad_sch")).write_text(rename_instances(source(name+".kicad_sch"),name),encoding="utf-8")
    shutil.copytree(LEGACY_HW/"fpga-servo.pretty",HERE/"fpga-servo.pretty",dirs_exist_ok=True)
    for name in ["sym-lib-table","fp-lib-table"]:
        shutil.copy2(LEGACY_HW/name,HERE/name)
    lib=source("ax7010_servo_reva.kicad_sym")
    # Keep all reused library definitions and append the new vendor-audited symbol.
    lib=lib.rstrip()[:-1]+"\n"+ADC+"\n"+TXU+"\n)\n"
    (HERE/"ax7010_servo_reva.kicad_sym").write_text(lib,encoding="utf-8")
    project=json.loads(source("ax7010_servo_reva.kicad_pro"))
    project["meta"]["filename"]=PROJECT+".kicad_pro"
    project["sheets"]=[]
    project["text_variables"]={"DESIGN_STATUS":"DEVELOPMENT - NOT FOR FABRICATION","ADC":"AD7606C-16BSTZ"}
    (HERE/(PROJECT+".kicad_pro")).write_text(json.dumps(project,indent=2)+"\n")

    # Retain the authored current sensing / bus OCP region. Remove the bounded
    # x>=185 mm ADC block, including its now obsolete references and wiring.
    raw=source("current_adc.kicad_sch")
    kept=[]
    removed=[]
    for form in children(raw):
        h=head(form)
        if h in {"lib_symbols","version","generator","generator_version","uuid","paper","title_block","embedded_fonts"}:
            continue
        pts=parse_xy(form) if h=="wire" else ([parse_at(form)] if parse_at(form) else [])
        if pts and any(p[0]>=185 for p in pts):
            removed.append(h)
            continue
        if h=="label" and head_string(form,"label") in {"IU_ADC","IV_ADC","IW_ADC","NTC_BOARD","NTC_BOARD_AUX"}:
            x,y=parse_at(form)
            # A separate port stub avoids placing the hierarchy arrow over C40-42.
            end=101.6 if y<160 else 50.8
            if y<160:
                kept.append(wire((91.44,y),(end,y)))
                kept.append(junction(91.44,y))
                form=label(head_string(form,"label"),end,y,True,"output",180)
            else:
                kept += [wire((x,y),(x,y-5.08)),wire((x,y-5.08),(end,y-5.08)),junction(x,y)]
                form=label(head_string(form,"label"),end,y-5.08,True,"output",180)
        kept.append(form)
    kept.append(text("ADC moved to dedicated core + power sheets",195.58,30.48,1.016))
    kept += [wire((170.18,104.14),(182.88,104.14)),label("VIO_3V3",182.88,104.14,True,angle=180)]
    kept.append(text("Phase RC: 47R / 1nF retained for first prototype; tune after PWM-noise tests",17.78,13.97,1.016))
    write_sheet("current_adc",kept,"Rev.B - current sensing / independent bus OCP")
    p=HERE/"current_adc.kicad_sch"
    p.write_text(rename_instances(p.read_text(encoding="utf-8"),"current_adc"),encoding="utf-8")

    # New core: two explicit input/return pins per channel, four DOUTs, mode
    # straps, and defined startup states independent of FPGA configuration.
    r=[text("AD7606C-16 / ANALOG INPUTS",17.78,17.78),text("4-LANE / 5 MHz BRING-UP / 20 MHz QUALIFICATION TARGET",132.08,17.78),adc(1,66.04,81.28,"adc_core"),adc(2,193.04,81.28,"adc_core")]
    signals=["IU_ADC","IV_ADC","IW_ADC","VBUS_ADC","NTC_BOARD","NTC_BOARD_AUX"]
    for i,sig in enumerate(signals):
        y=48.26+i*7.62
        r += [wire((17.78,y),(40.64,y)),label(sig,17.78,y,True)]
    for y in [93.98,101.6]:
        r += [wire((35.56,y),(40.64,y))]
    r += [wire((35.56,93.98),(35.56,101.6)),wire((35.56,101.6),(35.56,107.95)),junction(35.56,101.6),power("GND",35.56,107.95,"adc_core"),label("GND",35.56,107.95)]
    for i in range(8):
        y=48.26+i*7.62
        r += [wire((91.44,y),(99.06,y))]
        if i<7:
            r += [wire((99.06,y),(99.06,y+7.62))]
        if i>0:
            r += [junction(99.06,y)]
    r += [wire((99.06,101.6),(99.06,109.22)),label("GND",99.06,109.22,True),power("GND",99.06,109.22,"adc_core")]
    inputs=["ADC_CONVST","ADC_RESET","ADC_SCLK","ADC_CS_N","ADC_SDI"]
    for i,sig in enumerate(inputs):
        y=45.72+i*7.62
        r += [label(sig,132.08,y,True)]
        if sig=="ADC_SCLK":
            r += [wire((132.08,y),(140.97,y)),passive("R40","R104",148.59,y,"adc_core","47R source damping; place adjacent to U28 B1Y clock output"),wire((156.21,y),(167.64,y))]
        else:
            r += [wire((132.08,y),(167.64,y))]
    for i,sig in enumerate(["ADC_DOUTA","ADC_DOUTB","ADC_DOUTC","ADC_DOUTD","ADC_BUSY","ADC_FRSTDATA"]):
        y=45.72+i*7.62
        r += [wire((218.44,y),(266.7,y))]
        r += [label(sig,266.7,y,True,"output",180)]
    for i in range(4):
        r += [no_connect(218.44,91.44+i*7.62)]
    for i in range(7):
        y=91.44+i*2.54
        r += [wire((162.56,y),(167.64,y))]
        if i<6:
            r += [wire((162.56,y),(162.56,y+2.54))]
        if i>0:
            r += [junction(162.56,y)]
    r += [wire((162.56,106.68),(162.56,111.76)),power("GND",162.56,111.76,"adc_core"),label("GND",162.56,111.76)]
    r += [text("DOUTE-H unused in 4-lane mode; DB0-2 / DB12-15 tied to GND",132.08,121.92,.95),text("MODE STRAPS: software / serial / internal reference",17.78,120.65,1.016),adc(3,66.04,156.21,"adc_core")]
    for i in range(7):
        y=135.89+i*5.08
        r += [wire((30.48,y),(43.18,y))]
        if i<6:
            r += [wire((30.48,y),(30.48,y+5.08))]
        r += [junction(30.48,y)]
    r += [wire((30.48,128.27),(30.48,135.89)),wire((17.78,128.27),(30.48,128.27)),label("VIO_3V3",17.78,128.27,True),power("VIO_3V3",30.48,128.27,"adc_core"),wire((88.9,166.37),(96.52,166.37)),wire((96.52,166.37),(96.52,171.45)),power("GND",96.52,171.45,"adc_core"),label("GND",96.52,171.45)]
    r += [text("BIAS WITH OE LOW: RESET / CS high; others low",132.08,128.27,1.016)]
    for i,sig in enumerate(inputs):
        x=139.7+i*27.94
        r += [passive("R80",f"R{105+i}",x,143.51,"adc_core",f"10k startup bias for {sig}",90)]
        if sig in {"ADC_RESET","ADC_CS_N"}:
            r += [wire((x,130.81),(x,135.89)),power("VIO_3V3",x,130.81,"adc_core"),label("VIO_3V3",x,130.81),wire((x,151.13),(x,158.75)),label(sig,x,158.75)]
        else:
            r += [wire((x,130.81),(x,135.89)),label(sig,x,130.81),wire((x,151.13),(x,156.21)),power("GND",x,156.21,"adc_core"),label("GND",x,156.21)]
    r += [text("Hold GATE_EN low until reset + configuration readback pass.",17.78,180.34,1.016),text("Unipolar ADC codes: straight binary. See adc_profile.json.",17.78,185.42,1.016),text("Register writes are required after power-up; straps alone do not configure ranges.",17.78,190.5,.85)]
    # ADC-domain pins run at AVCC. Only translated ADC5_* signals reach them.
    isolated=[]
    for record in r:
        h=head(record)
        if h in {"hierarchical_label","label"}:
            name=head_string(record,h)
            if name.startswith("ADC_"):
                record=record.replace(q(name),q(name.replace("ADC_","ADC5_",1)),1)
            elif name=="VIO_3V3":
                record=record.replace(q(name),q("VA_5V"),1)
        elif h=="symbol" and f'(lib_id "{LIB}:PWR_VIO_3V3")' in record:
            record=record.replace(f'(lib_id "{LIB}:PWR_VIO_3V3")',f'(lib_id "{LIB}:PWR_VA_5V")')
            record=record.replace('"/VIO_3V3"','"/VA_5V"')
        isolated.append(record)
    write_sheet("adc_core",isolated,"Rev.B - AD7606C input / serial / startup")

    r=[text("ADC SUPPLIES: 100 nF AT EACH AVCC + 10 uF LOCAL BULK",17.78,15.24),adc(4,147.32,76.2,"adc_power")]
    railpoints=[25.4,50.8,76.2,86.36,96.52,116.84,127,147.32,157.48,177.8,187.96]
    for a,b in zip(railpoints,railpoints[1:]):
        r += [wire((a,25.4),(b,25.4))]
    r += [label("VA_5V",25.4,25.4,True),power("VA_5V",76.2,25.4,"adc_power")]
    for i,(px,cx) in enumerate([(96.52,86.36),(127,116.84),(157.48,147.32),(187.96,177.8)]):
        r += [wire((px,25.4),(px,63.5)),wire((cx,25.4),(cx,39.37)),passive("C43",f"C{64+i}",cx,45.72,"adc_power",f"100nF local bypass at U6 physical pin {pins[[1,37,38,48][i]]['number']}"),wire((cx,52.07),(cx,55.88)),power("GND",cx,55.88,"adc_power"),label("GND",cx,55.88),junction(cx,25.4)]
        if px!=187.96:
            r += [junction(px,25.4)]
    r += [wire((50.8,25.4),(50.8,39.37)),passive("C60","C100",50.8,45.72,"adc_power","10uF AVCC local bulk; verify effective capacitance"),wire((50.8,52.07),(50.8,55.88)),power("GND",50.8,55.88,"adc_power"),label("GND",50.8,55.88),junction(50.8,25.4)]
    r += [wire((187.96,25.4),(218.44,25.4)),junction(187.96,25.4),junction(218.44,25.4),wire((218.44,25.4),(233.68,25.4)),wire((233.68,25.4),(248.92,25.4)),wire((248.92,25.4),(269.24,25.4)),wire((218.44,25.4),(218.44,63.5)),wire((233.68,25.4),(233.68,39.37)),passive("C43","C68",233.68,45.72,"adc_power","100nF VDRIVE bypass at physical pin 23; AVCC and VDRIVE on same rail"),wire((233.68,52.07),(233.68,55.88)),power("GND",233.68,55.88,"adc_power"),label("GND",233.68,55.88),label("VA_5V",269.24,25.4,angle=180),power("VA_5V",248.92,25.4,"adc_power"),junction(233.68,25.4)]
    gx=[90.17+i*17.78 for i in range(8)]
    for i,x in enumerate(gx):
        r += [wire((x,109.22),(x,116.84))]
        if i<len(gx)-1:
            r += [wire((x,116.84),(gx[i+1],116.84))]
        r += [junction(x,116.84)]
    r += [wire((66.04,116.84),(gx[0],116.84)),label("GND",66.04,116.84,True),wire((gx[-1],116.84),(228.6,116.84)),power("GND",228.6,116.84,"adc_power")]
    r += [text("REGCAP A/D SEPARATE; REFCAPA/B SHORTED; NO EXTERNAL LOAD ON THESE NODES",17.78,129.54,1.016),adc(5,86.36,156.21,"adc_power")]
    for ref,x,y,px,desc,template in [("C62",30.48,149.86,48.26,"REGCAP_A pin36 only; 1uF", "C62"),("C63",30.48,175.26,48.26,"REGCAP_D pin39 only; 1uF","C63"),("C61",142.24,149.86,124.46,"100nF REFIN_REFOUT pin42","C43")]:
        r += [wire((min(x,px),y-6.35),(max(x,px),y-6.35)),passive(template,ref,x,y,"adc_power",desc),wire((x,y+6.35),(x,y+10.16)),power("GND",x,y+10.16,"adc_power"),label("GND",x,y+10.16)]
    r += [wire((124.46,168.91),(132.08,168.91)),wire((132.08,168.91),(132.08,176.53)),wire((124.46,176.53),(132.08,176.53)),wire((132.08,176.53),(156.21,176.53)),junction(132.08,176.53),passive("C60","C60",156.21,182.88,"adc_power","10uF low-ESR ceramic at shorted pins44/45; effective capacitance qualification open"),wire((156.21,189.23),(156.21,193.04)),power("GND",156.21,193.04,"adc_power"),label("GND",156.21,193.04)]
    write_sheet("adc_power",r,"Rev.B - AD7606C supply / reference / LDO bypass")
    write_sheet("adc_levelshift",build_levelshift.records(sys.modules[__name__]),"Rev.B - ADC voltage / partial-power isolation")

    # Expose J1.29/30/31 on the copied interface; remove only those NC markers.
    raw=source("ax7010_interface.kicad_sch")
    jd=all_defs[LIB+":HDR_2x20"]
    additions=[]
    nc_positions=[]
    for n,sig in [(29,"ADC_DOUTC"),(30,"ADC_DOUTD"),(31,"ADC_SDI")]:
        p=next(p.text for p in extract_forms(jd,"pin") if property_value(p.text,"unused") is None and head_string(extract_forms(p.text,"number")[0].text,"number")==str(n))
        px,py=parse_at(p);x=round(121.92+px,6);y=round(88.9-py,6)
        nc_positions.append((x,y))
        hx=27.94 if px<0 else 203.2
        additions += [wire((min(hx,x),y),(max(hx,x),y)),label(sig,hx,y,True,"output" if sig=="ADC_SDI" else "input",0 if px<0 else 180)]
    records=[]
    for f in children(raw):
        if head(f) in {"lib_symbols","version","generator","generator_version","uuid","paper","title_block","embedded_fonts"}:
            continue
        if head(f)=="no_connect" and parse_at(f) in nc_positions:
            continue
        records.append(f)
    records+=additions
    # Host-side pull-ups override TXU's weak internal input pulldowns while the
    # FPGA is unconfigured, even after the supervised OE signal becomes high.
    for ref,sig,x in [("R110","ADC_RESET",231.14),("R111","ADC_CS_N",259.08)]:
        records += [passive("R80",ref,x,139.7,"ax7010_interface","10k host-side startup pull-up before TXU A2",90),
                    wire((x,124.46),(x,132.08)),power("VIO_3V3",x,124.46,"ax7010_interface"),label("VIO_3V3",x,124.46),
                    wire((x,147.32),(x,156.21)),label(sig,x,156.21)]
    records.append(text("R110/R111: hold RESET/CS high at TXU inputs while FPGA is Hi-Z.",16.51,186.69,.9))
    records.append(text("AD7606C: J10.29=DOUTC (U12), .30=DOUTD (T12), .31=SDI (T10)",16.51,180.34,1.016))
    write_sheet("ax7010_interface",records,"Rev.B - AX7010 2022 J10 / four-lane ADC")
    p=HERE/"ax7010_interface.kicad_sch"
    p.write_text(rename_instances(p.read_text(encoding="utf-8"),"ax7010_interface"),encoding="utf-8")

    # Hierarchy assembled from actual child ports, with labels on visible stubs.
    top=header("system","AX7010 servo - AD7606C Rev.B","")
    top=top.replace(uid("page-system"),ROOT_ID)
    top+=text("INDEPENDENT AD7606C ENGINEERING VARIANT - ORIGINAL REV.A RETAINED",17.78,13.97,1.27)
    for i,name in enumerate(SHEETS):
        # Nine sheets: 3 columns x3 rows, ports split across both sides.
        # The bottom-right encoder block stops above the drawing title block.
        x=[40.64,132.08,223.52][i%3]
        y=[30.48,87.63,144.78][(i//3)%3]
        width=40.64;height=17.78 if name=="encoder" else 43.18
        if name=="power_input":
            y=24.13;height=12.7
        elif name=="adc_levelshift":
            x=40.64;y=44.45;height=35.56
        raw=(HERE/(name+".kicad_sch")).read_text(encoding="utf-8")
        ports=[f.text for f in extract_forms(strip_form(raw,"lib_symbols"),"hierarchical_label")]
        left=ports[:(len(ports)+1)//2];right=ports[len(left):]
        block=f'(sheet (at {num(x)} {num(y)}) (size {width} {height}) (stroke (width .1524) (type default)) (fill (color 0 0 0 0)) (uuid "{sheet_ids[name]}")'
        block+=f'(property "Sheetname" {q(name)} {at(x,y-1.27)} {effects(.9,"(justify left bottom)")})'
        block+=f'(property "Sheetfile" "{name}.kicad_sch" {at(x,y+height+1.27)} {effects(.8,"(justify left top)")})'
        for group,side in [(left,"left"),(right,"right")]:
            for j,port in enumerate(group):
                signal=head_string(port,"hierarchical_label")
                typ=re.search(r'\(shape ([^ )]+)',port)[1]
                # Power ports intentionally remain passive to match inherited sheets.
                py=round(y+3.81+j*2.54,6)
                px=x if side=="left" else round(x+width,6)
                angle=180 if side=="left" else 0
                block+=f'(pin {q(signal)} {typ} {at(px,py,angle)} {effects(.7)} (uuid "{fresh()}"))'
                end=round(px+(-3.81 if side=="left" else 3.81),6)
                canonical={"BUS_SENSE_P":"VBUS_PROT","BUS_SENSE_N":"VBUS_BRIDGE"}.get(signal,signal)
                top+=wire((px,py),(end,py))+label(canonical,end,py,right=side=="left")
        block+=f'(instances (project "{PROJECT}" (path "/{ROOT_ID}" (page "{i+2}")))))'
        top+=block
    top+='(sheet_instances (path "/" (page "1"))) (embedded_fonts no))\n'
    (HERE/(PROJECT+".kicad_sch")).write_text(top,encoding="utf-8")

    # Separate real interface constraints; original XDC remains unchanged.
    xdc=(ROOT/"fpga/ax7010_servo_reva.xdc").read_text(encoding="utf-8")
    xdc+="\n# AD7606C independent schematic only; Vivado STA and physical J10 validation OPEN.\n"
    for pad,sig in [("U12","ADC_DOUTC"),("T12","ADC_DOUTD"),("T10","ADC_SDI")]:
        xdc+=f"set_property PACKAGE_PIN {pad} [get_ports {sig}]; set_property IOSTANDARD LVCMOS33 [get_ports {sig}]\n"
    (HERE/(PROJECT+".xdc")).write_text(xdc,encoding="utf-8")
    profile=json.loads((ROOT/"fpga/ad7606c_fast_candidate_profile_2026-10-12.json").read_text())
    profile["status"]="IMPLEMENTED_IN_INDEPENDENT_SCHEMATIC_ONLY"
    profile["schematic"]=PROJECT+".kicad_sch"
    profile["hardware"]["adc_supply_digital"]="VA_5V, same physical rail as AVCC; U27-U29 TXU0204PWR translate to AX7010 VIO_3V3"
    profile["hardware"]["interface_enable"]="PWR_READY drives all TXU0204 OE pins"
    profile["timing"]["initial_sclk_hz"]=5000000
    profile["timing"]["initial_frame_time_us"]=6.4
    profile["timing"]["qualification_target_sclk_hz"]=20000000
    profile["timing"]["qualification_target_frame_time_us"]=1.6
    profile["timing"]["translator_round_trip_timing"]="OPEN: SCLK A->B + ADC tD_SCK_DO + DOUT B->A + cable + FPGA capture margin"
    profile["blocking_gates"]=[
        "ADC/connector footprint and new PCB placement, routing, parity, DRC/DFM closure",
        "ADC register readback, frame alignment, error handling and AX7010 Vivado STA",
        "PWM switching noise, calibrated current response and measured loop stability",
        "Regulator load, AVCC rapid undervoltage and full OCP dynamic shutdown qualification"]
    profile["startup"]={"full_reset_min_high_ns":3200,"post_full_reset_min_us":274,
        "stable_rails_before_first_reset_min_ms":10,
        "first_reset_note":"Rev.A Table3 footnote3: tPOWER-UP + tDEVICE_SETUP > 2 seconds",
        "development_first_reset_wait_ms":2100,
        "gate_enable_policy":"Keep GATE_EN low until rail/setup timing, device ID, config readback and fresh frames pass"}
    (HERE/"adc_profile.json").write_text(json.dumps(profile,indent=2)+"\n")
    (HERE/"adc_pin_map.json").write_text(json.dumps([pins[n] for n in sorted(pins)],indent=2)+"\n")
    # Source whitespace only; native rendering/connectivity are unchanged.
    for path in [*HERE.glob("*.kicad_sch"),*HERE.glob("*.kicad_sym")]:
        lines=path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(line.rstrip() for line in lines)+"\n",encoding="utf-8")
    print(f"Generated {PROJECT}: {len(SHEETS)+1} A4 sheets; 64 explicit ADC physical pins.")


if __name__ == "__main__":
    build()
