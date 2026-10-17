"""Test discovery with fresh optional native inputs and explicit execution lanes."""
from pathlib import Path
import fnmatch
import sys
import tempfile
import unittest
from .kicad import run_native, read_xml_summary

NETLIST = None
NGSPICE = "ngspice"

def run_tests(pattern="test_*.py", cli="kicad-cli", ngspice="ngspice", pcb_python=None, lane="all"):
    global NETLIST, NGSPICE
    NGSPICE=ngspice
    tools=Path(__file__).resolve().parents[1]
    root=tools.parent
    if lane=="native":
        executable=pcb_python or sys.executable
        probe=run_native([executable,"-c","import pcbnew"],root,30)
        if probe["exit_code"]:
            print("Native geometry NOT_RUN: requested interpreter has no pcbnew")
            return 1
        r=run_native([executable,"-X","utf8","-m","unittest","discover","-s",str(tools/"tests"),"-p","test_pcb_*.py","-v"],root,300)
        print(r["stdout"]+r["stderr"])
        return 0 if r["exit_code"]==0 else 1
    errors=[]
    with tempfile.TemporaryDirectory(prefix="pcb-tests-") as folder:
        needs_xml=lane!="static" and any(fnmatch.fnmatch(name,pattern) for name in ("test_adc_validity.py","test_gate_ab_verify.py"))
        NETLIST=None
        if needs_xml:
            target=Path(folder)/"fresh.xml"
            r=run_native([cli,"sch","export","netlist","--format","kicadxml","--output",str(target),str(root/"hardware/ads8588s_servo/ax7010_servo_reva.kicad_sch")],root,180)
            try:
                if r["exit_code"]: raise ValueError(r.get("error","native export failed"))
                read_xml_summary(target)
                NETLIST=target
            except Exception as exc: errors.append(f"Fresh native test fixture NOT_RUN: {type(exc).__name__}: {exc}")
        sys.path.insert(0,str(tools/"tests"))
        suite=unittest.defaultTestLoader.discover(str(tools/"tests"),pattern=pattern)
        # Keep tutorial provenance and independent XML audit regression coverage.
        if pattern=="test_*.py":
            loader=unittest.TestLoader()
            suite.addTests(loader.discover(str(tools/"ai_pcb_guide/tests"),pattern="test_*.py"))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        native_code=0
        if pcb_python:
            probe=run_native([pcb_python,"-c","import pcbnew"],root,30)
            if probe["exit_code"]:
                errors.append("Native geometry NOT_RUN: requested interpreter has no pcbnew")
                native_code=1
            else:
                r=run_native([pcb_python,"-X","utf8","-m","unittest","discover","-s",str(tools/"tests"),"-p","test_pcb_*.py","-v"],root,300)
                print(r["stdout"]+r["stderr"])
                native_code=r["exit_code"]
        for message in errors: print(message)
        NETLIST=None
        return 0 if result.wasSuccessful() and not errors and not native_code else 1
