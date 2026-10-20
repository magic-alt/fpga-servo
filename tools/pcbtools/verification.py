"""Fresh native evidence pipelines for configured KiCad projects."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from .kicad import run_native, read_xml_summary, portable_netlist
from .report import Finding, RunReport, write_report
from .project import ProjectError, load_project, local_dependencies


def new_run_directory(output):
    output.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
    return Path(tempfile.mkdtemp(prefix=stamp,dir=output.resolve()))


def source_hashes(project):
    from .schematic import discover_sheets
    paths={project.schematic,project.config} | set(project.libraries) | local_dependencies(project)
    try:
        paths.update(discover_sheets(project))
    except (ProjectError,ValueError,OSError):
        pass  # The schematic rule records the actual hierarchy failure.
    for suffix in (".kicad_pro",".kicad_dru"):
        related=project.schematic.with_suffix(suffix)
        if related.is_file(): paths.add(related)
    if project.board: paths.add(project.board)
    if project.bom: paths.add(project.bom)
    # Cover tracked source inputs as well as external project sources; never env files.
    proc=run_native(["git","ls-files","-z"],project.root,30)
    if proc["exit_code"]==0:
        for name in proc["stdout"].split("\0"):
            path=project.root/name
            if name.startswith(("hardware/","tools/",".github/")) and path.is_file():
                if any(part==".env" or part.startswith(".env.") or part in {".history","__pycache__"} for part in path.parts): continue
                if path.suffix in {".pyc",".kicad_prl",".lck"} or path.is_relative_to(project.output): continue
                paths.add(path)
    return {p.relative_to(project.root).as_posix() if p.is_relative_to(project.root) else p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def save_run(report,out):
    report.evidence["finished_utc"]=datetime.now(timezone.utc).isoformat()
    report.evidence["artifacts_sha256"]={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob("*")) if p.is_file() and p.name!="manifest.json"}
    write_report(report,out/"manifest.json")


def native_summary(kind,path,code):
    try:
        d=json.loads(path.read_text(encoding="utf-8"))
        # Counts cannot override the actual native violation arrays. Reject
        # additional exclusion records/counts instead of trusting a zero summary.
        def reject_exclusions(value):
            if isinstance(value,dict):
                for key, child in value.items():
                    if "exclusion" in key.lower() and child:
                        raise ValueError("Native report contains exclusions")
                    if key.lower() in {"errors","warnings","error_count","warning_count","excluded_count"} and child:
                        raise ValueError("Native summary contains nonzero violation counts")
                    reject_exclusions(child)
            elif isinstance(value,list):
                for child in value: reject_exclusions(child)
        reject_exclusions(d)
        if kind=="erc":
            sheets=d.get("sheets")
            if not isinstance(sheets,list) or not sheets or any(not isinstance(s,dict) or not isinstance(s.get("violations"),list) for s in sheets):
                raise ValueError("ERC report has no complete sheet violation records")
            items=[v for sheet in sheets for v in sheet["violations"]]
            details={"errors":0,"warnings":0,"exclusions":0}
        else:
            keys=("violations","unconnected_items","schematic_parity")
            if any(not isinstance(d.get(k),list) for k in keys): raise ValueError("DRC report is incomplete")
            items=d["violations"]
            details={"errors":0,"warnings":0,"exclusions":0,"unconnected":len(d["unconnected_items"]),"schematic_parity":len(d["schematic_parity"])}
        for v in items:
            if not isinstance(v,dict) or v.get("severity") not in {"error","warning"}: raise ValueError("Native violation has invalid severity")
            details["errors" if v["severity"]=="error" else "warnings"]+=1
            details["exclusions"]+=bool(v.get("excluded",False))
        valid=code==0 and not items and not details.get("unconnected",0) and not details.get("schematic_parity",0)
        return Finding("native."+kind,"PASS" if valid else "FAIL","Native all-severity report",details)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        return Finding("native."+kind,"FAIL",str(exc),{"exit_code":code})


def qualify(netlist, output, ngspice=None, strict=False):
    """Retain Gate A/B and failure-file behavior through a direct API."""
    from .rules.protection import electrical_api
    api=electrical_api()
    try:
        report=api.gate_report(Path(netlist))
        report["status"]="PASS_AUTOMATED_ONLY"
        if ngspice:
            values,pins=api.read_netlist(Path(netlist))
            numeric=api.require_graph(values,pins)
            report["spice"]=api.run_spice(numeric,output.parent/"spice",ngspice)
        code=2 if strict and any(report[k]["status"]=="BLOCKED" for k in ("gate_a","gate_b")) else 0
    except Exception as exc:
        report={"status":"FAILED","error":f"{type(exc).__name__}: {exc}","gate_a":{"status":"BLOCKED"},"gate_b":{"status":"BLOCKED"}}
        code=1
    output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report,code


def verify(project, scope, output=None, tools=None):
    from .schematic import check_schematic
    from .board import check_board
    from .rules import run_rules
    tools=tools or {}
    if scope not in {"schematic","pcb","prototype","release"}: raise ProjectError("Unknown verification scope")
    if scope in {"pcb","prototype","release"}: project.require_board()
    out=new_run_directory(project.safe_output(output or project.output))
    evidence={"schema_version":1,"output":str(out),"started_utc":datetime.now(timezone.utc).isoformat(),"steps":[],"tools":{"python":__import__("sys").version.split()[0]},"erc":{"status":"NOT_RUN"},"drc":{"status":"NOT_RUN"},"gate_a":{"status":"BLOCKED"},"gate_b":{"status":"BLOCKED"},"pcb_release":"BLOCKED","delivery_scope":"SCHEMATIC_BOM" if scope=="schematic" else "FULL_DESIGN"}
    report=RunReport(project.id,[],evidence,"BLOCKED" if scope=="release" else "NOT_EVALUATED")
    hash_inputs=source_hashes
    prototype_evidence=None
    if scope=="prototype":
        from .manufacturing import check_prototype_inputs, design_source_hashes
        hash_inputs=design_source_hashes
        findings,prototype_evidence=check_prototype_inputs(project)
        report.findings+=findings;evidence.update(prototype_evidence)
        evidence["delivery_scope"]="ENGINEERING_PROTOTYPE_ONLY"
    before=None
    native_root=None
    audit_project=project
    cli=tools.get("kicad-cli","kicad-cli")
    def run(name,command,timeout=180):
        if native_root is not None and command[0]==cli:
            mapped=[]
            for arg in command:
                candidate=Path(str(arg))
                if candidate.is_absolute() and candidate.is_relative_to(project.root) and candidate.relative_to(project.root).as_posix() in before:
                    arg=str(native_root/candidate.relative_to(project.root))
                mapped.append(arg)
            command=mapped
        r=run_native(command,project.root,timeout)
        # Portable logs contain no inherited environment and no local installation prefix.
        log=r.get("stdout","")+r.get("stderr","")+r.get("error","")
        log=log.replace(str(project.root),".").replace(project.root.as_posix(),".")
        (out/(name+".log")).write_text(log,encoding="utf-8")
        shown=[Path(str(command[0])).name]+[str(x).replace(str(project.root),".") for x in command[1:]]
        evidence["steps"].append({"name":name,"command":shown,"exit_code":r["exit_code"],"status":r["status"],"log":name+".log"})
        return r
    def export_inputs(p,prefix=""):
        inputs={"require_netlist":True}
        for fmt,key,filename in (("kicadxml","xml","netlist.xml"),("kicadsexpr","netlist","board.net")):
            target=out/(prefix+filename)
            r=run(prefix+"export_"+key,[cli,"sch","export","netlist","--format",fmt,"--output",str(target),str(p.schematic)])
            try:
                if r["exit_code"]: raise ValueError("Native export failed")
                if key=="xml":
                    evidence[prefix+"netlist_counts"]=read_xml_summary(target)
                else:
                    from .kicad import read_native_netlist_summary
                    read_native_netlist_summary(target)
                portable_netlist(target,p.schematic.relative_to(p.root).as_posix())
                inputs[key]=target
                report.findings.append(Finding(prefix+"native.export_"+key,"PASS","Fresh native export"))
            except Exception as exc:
                report.findings.append(Finding(prefix+"native.export_"+key,"FAIL" if r["status"]!="NOT_RUN" else "NOT_RUN",str(exc)))
        target=out/(prefix+"erc.json")
        r=run(prefix+"erc",[cli,"sch","erc","--severity-all","--exit-code-violations","--format","json","--output",str(target),str(p.schematic)])
        f=native_summary("erc",target,r["exit_code"])
        if r["status"]=="NOT_RUN":f=Finding("native.erc","NOT_RUN",r.get("error","Native ERC not executed"))
        evidence[prefix+"erc"]={"status":f.status,**f.details}
        f.rule_id=prefix+f.rule_id;report.findings.append(f)
        return inputs
    try:
        before=hash_inputs(project);evidence["source_hashes_before"]=before
        if scope=="prototype":
            from .manufacturing import freeze_design
            if before!=prototype_evidence.get("design_source_hashes"):
                raise ProjectError("Design changed after prototype input review")
            audit_project, frozen=freeze_design(project,out/"frozen-design",before)
            native_root=Path(frozen["root"])
            evidence["frozen_design"]=frozen
        commit=run("source_commit",["git","rev-parse","HEAD"],30)
        evidence["source_commit"]=commit.get("stdout","").strip() if commit["exit_code"]==0 else "UNAVAILABLE"
        if scope=="prototype":
            evidence["tool_sources_sha256"]={p.relative_to(project.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.rglob("*.py")) if p.is_relative_to(project.root)}
        version=run("kicad_version",[cli,"--version"],30)
        if version["exit_code"] or not version["stdout"].strip().startswith("10."):
            report.findings.append(Finding("native.version",version["status"] if version["status"]!="PASS" else "FAIL","KiCad 10 required"))
            report.findings += check_schematic(audit_project)+run_rules(audit_project,"schematic",{})
            return report
        evidence["tools"]["kicad"]=version["stdout"].strip()
        inputs=export_inputs(project)
        reference=project.parameters.get("baseline_config")
        if reference:
            config=(project.root/reference).resolve()
            if not config.is_relative_to(project.root): raise ProjectError("Baseline configuration outside root")
            baseline=load_project(config)
            if scope=="prototype":
                from .manufacturing import relocated_project
                baseline=relocated_project(baseline,native_root)
            if scope=="prototype":
                from .manufacturing import check_native_settings
                try:
                    check_native_settings(baseline)
                    report.findings.append(Finding("baseline.prototype.native_settings","PASS","Baseline native checks enabled"))
                except (OSError,ValueError,KeyError,TypeError) as exc:
                    report.findings.append(Finding("baseline.prototype.native_settings","FAIL",str(exc)))
            baseline_inputs=export_inputs(baseline,"baseline-")
            inputs["baseline_xml"]=baseline_inputs.get("xml")
            for f in check_schematic(baseline)+run_rules(baseline,"schematic",baseline_inputs):
                f.rule_id="baseline."+f.rule_id;report.findings.append(f)
        report.findings += check_schematic(audit_project)+run_rules(audit_project,"schematic" if scope=="schematic" else "pcb",inputs)
        pdf=out/"schematic.pdf"
        r=run("pdf",[cli,"sch","export","pdf","--output",str(pdf),str(project.schematic)])
        valid=r["exit_code"]==0 and pdf.is_file() and pdf.stat().st_size>0
        report.findings.append(Finding("native.pdf","PASS" if valid else "FAIL","Native schematic export"))
        if scope in {"pcb","prototype","release"}:
            report.findings += check_board(audit_project,inputs.get("netlist"))
            target=out/"drc.json"
            r=run("drc",[cli,"pcb","drc","--schematic-parity","--refill-zones","--severity-all","--exit-code-violations","--format","json","--output",str(target),str(project.board)],300)
            f=native_summary("drc",target,r["exit_code"])
            evidence["drc"]={"status":f.status,**f.details};report.findings.append(f)
        if "servo" in project.rule_sets and inputs.get("xml"):
            q,code=qualify(inputs["xml"],out/"qualification.json",tools.get("ngspice","ngspice"))
            evidence["gate_a"]=q["gate_a"];evidence["gate_b"]=q["gate_b"]
            report.findings.append(Finding("protection.qualification",("NOT_RUN" if "unavailable" in q.get("error","") else "FAIL") if code==1 else "PASS",q.get("error","Static/ideal-model qualification only; dynamic engineering gates remain BLOCKED"),{"report":"qualification.json"}))
    except Exception as exc:
        report.findings.append(Finding("workflow","FAIL",f"{type(exc).__name__}: {exc}"))
    finally:
        try:
            after=hash_inputs(project);evidence["source_hashes_after"]=after
            if before is None or before!=after:report.findings.append(Finding("source.unchanged","FAIL","Source files changed or unavailable during verification"))
            else:report.findings.append(Finding("source.unchanged","PASS","Sources unchanged"))
            if native_root is not None:
                from .manufacturing import check_frozen_design
                check_frozen_design(evidence["frozen_design"])
        except (OSError,ValueError,KeyError,TypeError) as exc:
            report.findings.append(Finding("source.unchanged","FAIL",str(exc)))
        if scope=="prototype":
            findings,current=check_prototype_inputs(project)
            if current!=prototype_evidence:
                report.findings.append(Finding("prototype.evidence_unchanged","FAIL","Engineering evidence changed during verification"))
            required={"native.export_xml","native.export_netlist","native.erc","native.drc","native.pdf","source.unchanged"}
            passes={f.rule_id for f in report.findings if f.status=="PASS"}
            if not required.issubset(passes):
                report.findings.append(Finding("prototype.native_complete","FAIL","Fresh complete native evidence required"))
            evidence["prototype_ready"]="PASS" if report.findings and all(f.status in {"PASS","NOT_APPLICABLE"} for f in report.findings) else "BLOCKED"
        save_run(report,out)
    return report
