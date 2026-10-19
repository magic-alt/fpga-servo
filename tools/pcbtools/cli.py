"""Single CLI entry point. Missing capabilities fail explicitly."""
import argparse
from .project import ProjectError, load_project, resolve_project
from pathlib import Path

class ToolkitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProjectError(message)

def parser():
    p = ToolkitParser(description="Project-configured KiCad development and verification")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("check", "verify", "export", "develop"):
        c = sub.add_parser(name)
        g = c.add_mutually_exclusive_group(required=True)
        g.add_argument("--project")
        g.add_argument("--config", type=Path)
        c.add_argument("--output", type=Path)
        if name in {"check", "verify"}:
            c.add_argument("--scope", choices=("schematic", "pcb", "prototype", "release") if name == "verify" else ("schematic", "pcb"), required=True)
        if name == "check": c.add_argument("--netlist", type=Path)
        if name == "export": c.add_argument("--kind", choices=("bom", "procurement", "netlist", "pdf", "fabrication", "fabrication-review"), required=True)
        if name in {"verify", "export"}:
            c.add_argument("--kicad-cli", default="kicad-cli")
            c.add_argument("--ngspice", default="ngspice")
        if name == "develop":
            c.add_argument("--operation", choices=("snapshot", "sync"), required=True)
            mode = c.add_mutually_exclusive_group()
            mode.add_argument("--preview", action="store_true")
            mode.add_argument("--apply", action="store_true")
    t = sub.add_parser("test")
    t.add_argument("--pattern", default="test_*.py")
    t.add_argument("--lane", choices=("static","all","native"), default="all")
    t.add_argument("--kicad-cli", default="kicad-cli")
    t.add_argument("--ngspice", default="ngspice")
    t.add_argument("--pcb-python")
    return p

def main(argv=None):
    try:
        args = parser().parse_args(argv)
        if args.command == "test":
            from .testing import run_tests
            return run_tests(args.pattern,args.kicad_cli,args.ngspice,args.pcb_python,args.lane)
        project = load_project(args.config) if args.config else resolve_project(args.project)
        if getattr(args, "scope", "") in {"pcb", "prototype", "release"}: project.require_board()
        from .report import RunReport, exit_code
        if args.command == "verify":
            from .verification import verify
            report=verify(project,args.scope,args.output,{"kicad-cli":args.kicad_cli,"ngspice":args.ngspice})
        elif args.command == "export":
            from .export import export_project
            if args.kind == "fabrication-review":
                from .manufacturing_review import export_review
                from .verification import save_run
                report = export_review(project, args.output, {"kicad-cli":args.kicad_cli,"ngspice":args.ngspice})
                save_run(report, Path(report.evidence["output"]))
            else:
                report=export_project(project,args.kind,args.output,{"kicad-cli":args.kicad_cli,"ngspice":args.ngspice})
        elif args.command == "develop":
            from .development import develop
            report=develop(project,args.operation,args.apply,args.output or project.output)
        else:
            from .schematic import check_schematic
            from .board import check_board
            from .rules import run_rules
            from .verification import new_run_directory, save_run, source_hashes
            out=new_run_directory(project.safe_output(args.output or project.output))
            before=source_hashes(project)
            findings=check_schematic(project) if args.scope=="schematic" else check_board(project,args.netlist)
            findings+=run_rules(project,args.scope,{"netlist":args.netlist} if args.netlist else {})
            report=RunReport(project.id,findings,{"output":str(out),"pcb_release":"BLOCKED","source_hashes_before":before,"source_hashes_after":source_hashes(project)})
            save_run(report,out)
        for f in report.findings:
            print(f"{f.rule_id}: {f.status}" + (f" - {f.message}" if f.status!="PASS" else ""))
        print(f"Evidence: {report.evidence.get('output','')}\nPCB release: {report.evidence.get('pcb_release','BLOCKED')}")
        return exit_code(report)
    except ProjectError as exc:
        print(f"Configuration error: {exc}")
        return 64
