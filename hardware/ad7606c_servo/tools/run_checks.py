"""Refresh new/legacy native evidence without changing either electrical source."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--kicad-cli",default="E:/Software/KiCad/bin/kicad-cli.exe")
    args=ap.parse_args()
    evidence=HERE/"evidence";evidence.mkdir(exist_ok=True)
    logs=evidence/"logs";logs.mkdir(exist_ok=True)
    cli=args.kicad_cli
    top=HERE/"ax7010_servo_ad7606c.kicad_sch"
    old=ROOT/"hardware/ads8588s_servo/ax7010_servo_reva.kicad_sch"
    steps=[]

    def run(name,cmd,scope):
        result=subprocess.run([str(x) for x in cmd],cwd=ROOT,capture_output=True,encoding="utf-8",errors="replace")
        (logs/(name+".log")).write_text(result.stdout+result.stderr,encoding="utf-8")
        steps.append({"name":name,"scope":scope,"exit_code":result.returncode})
        print(f"{name}: {'PASS' if result.returncode==0 else 'FAIL'} ({result.returncode})",flush=True)
        return result.returncode==0

    version=subprocess.check_output([cli,"version"],text=True).strip()
    # Fresh exports precede graph checks; stop if exports cannot be produced.
    exports=[("legacy_xml",old,"kicadxml",evidence/"legacy-baseline.xml"),
             ("legacy_netlist",old,"kicadsexpr",evidence/"legacy-baseline.net"),
             ("new_xml",top,"kicadxml",evidence/"ad7606c.xml"),
             ("new_netlist",top,"kicadsexpr",evidence/"ad7606c.net")]
    for name,src,fmt,out in exports:
        if not run(name,[cli,"sch","export","netlist","--format",fmt,"--output",out,src],"native_export"):
            return 1
    run("new_static_and_ocp",[sys.executable,"-X","utf8",HERE/"tools/check_project.py"],"new_schematic")
    run("new_visible_power",[sys.executable,"-X","utf8",ROOT/"tools/check_power_wiring.py",HERE],"new_schematic")
    run("new_erc",[cli,"sch","erc","--severity-all","--exit-code-violations","--format","json","--output",evidence/"erc.json",top],"new_schematic")
    run("new_adc_supply_validity",[sys.executable,"-X","utf8",ROOT/"tools/check_adc_validity.py",evidence/"ad7606c.xml","--output",evidence/"adc-supply-validity.json"],"new_schematic")
    for name in ["check_native_schematic","check_kicad_grid","check_schematic_layout","check_schematic_connectivity","check_power_wiring","check_design",
                 "check_adc_serial_contract","check_ad7606c_fast_profile"]:
        run("legacy_"+name,[sys.executable,"-X","utf8",ROOT/"tools"/(name+".py")],"legacy_regression")
    for name in ["check_adc_validity","check_selection_contract"]:
        run("legacy_"+name,[sys.executable,"-X","utf8",ROOT/"tools"/(name+".py"),evidence/"legacy-baseline.xml"],"legacy_regression")
    run("legacy_safety",[sys.executable,"-X","utf8",ROOT/"tools/check_netlist_safety.py",evidence/"legacy-baseline.net"],"legacy_regression")
    run("legacy_ocp",[sys.executable,"-X","utf8",ROOT/"tools/check_ocp_behavior.py",evidence/"legacy-baseline.net"],"legacy_regression")
    run("legacy_erc",[cli,"sch","erc","--severity-all","--exit-code-violations","--format","json","--output",evidence/"legacy-erc.json",old],"legacy_regression")
    run("pdf",[cli,"sch","export","pdf","--output",evidence/"schematic.pdf",top],"new_schematic")
    run("svg",[cli,"sch","export","svg","--output",evidence/"svg",top],"new_schematic")
    source_files=[*HERE.glob("*.kicad_sch"),*HERE.glob("*.kicad_sym"),*HERE.glob("*.kicad_pro"),*HERE.glob("*.xdc"),HERE/"adc_profile.json"]
    erc=json.loads((evidence/"erc.json").read_text(encoding="utf-8"))
    violations=[v for s in erc["sheets"] for v in s["violations"]]
    summary={"kicad_version":version,"python":sys.executable,"python_version":sys.version.split()[0],
             "new_erc_errors":sum(v["severity"]=="error" for v in violations),
             "new_erc_warnings":sum(v["severity"]=="warning" for v in violations),
             "new_erc_exclusions":sum(bool(v.get("excluded",False)) for v in violations),
             "inherited_ignored_erc_categories":["footprint_filter","four_way_junction","simulation_model_issue","single_global_label"],
             "steps":steps,"source_sha256":{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}}
    (evidence/"verification.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    new_ok=all(s["exit_code"]==0 for s in steps if s["scope"]!="legacy_regression")
    legacy_ok=all(s["exit_code"]==0 for s in steps if s["scope"]=="legacy_regression")
    print(f"New schematic checks: {'PASS' if new_ok else 'FAIL'}; existing project regression: {'PASS' if legacy_ok else 'FAIL - see logs'}")
    return 0 if new_ok and legacy_ok else 1


if __name__=="__main__":
    sys.exit(main())
