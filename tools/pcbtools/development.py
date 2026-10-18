"""Read-only development plans and non-overwriting project snapshots."""
from pathlib import Path
import hashlib
import json
import shutil
from .schematic import discover_sheets
from .verification import new_run_directory, source_hashes, save_run
from .report import Finding, RunReport
from .project import ProjectError, local_dependencies

def develop(project, operation, apply=False, output=None):
    if operation not in {"snapshot","sync"}: raise ProjectError("Unknown development operation")
    out=new_run_directory(project.safe_output(output or project.output))
    before=source_hashes(project)
    report=RunReport(project.id,[],{"output":str(out),"pcb_release":"BLOCKED","source_hashes_before":before,"mode":"apply" if apply else "preview"})
    try:
        if operation=="sync":
            report.evidence["plan"]={"schematic":str(project.schematic.relative_to(project.root)),"board":str(project.board.relative_to(project.root)) if project.board else None,"steps":["Export a fresh netlist using pcb.py export --kind netlist", "Back up the project using develop --operation snapshot --apply", "Open the configured project in KiCad; use native Update PCB from Schematic (F8)", "Review additions, removals, physical pads and mechanical references", "Run verify --scope pcb after the reviewed native operation"],"automatic_sync_available":False}
            report.findings.append(Finding("development.sync","FAIL" if apply else "NOT_RUN","No native automatic synchronization backend configured; review plan produced, no board changed"))
        else:
            paths=set(discover_sheets(project)) | set(project.libraries) | local_dependencies(project)
            paths.update(p for p in (project.board,project.bom) if p)
            for suffix in (".kicad_pro",".kicad_dru"):
                p=project.schematic.with_suffix(suffix)
                if p.is_file(): paths.add(p)
            paths.add(project.config)
            plan=[]
            for source in sorted(paths):
                relative=source.relative_to(project.root) if source.is_relative_to(project.root) else Path("configuration")/source.name
                digest=hashlib.sha256(source.read_bytes()).hexdigest()
                plan.append({"source":relative.as_posix(),"sha256":digest})
                if apply:
                    dest=out/"snapshot"/relative
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with dest.open("xb") as handle: handle.write(source.read_bytes())
                    if hashlib.sha256(dest.read_bytes()).hexdigest()!=digest: raise ValueError("Snapshot copy mismatch")
            report.evidence["plan"]=plan
            if apply: (out/"snapshot.json").write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
            report.findings.append(Finding("development.snapshot","PASS","Snapshot written" if apply else "Preview only; no source copies written"))
    except Exception as exc:
        report.findings.append(Finding("development."+operation,"FAIL",f"{type(exc).__name__}: {exc}"))
    after=source_hashes(project)
    report.evidence["source_hashes_after"]=after
    report.findings.append(Finding("source.unchanged","PASS" if before==after else "FAIL","Source identity checked"))
    save_run(report,out)
    return report
