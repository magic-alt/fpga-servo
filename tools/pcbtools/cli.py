"""Single CLI entry point. Missing capabilities fail explicitly."""
import argparse
from .project import ProjectError, load_project, resolve_project
from pathlib import Path

def parser():
    p = argparse.ArgumentParser(description="Project-configured KiCad development and verification")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("check", "verify", "export", "develop"):
        c = sub.add_parser(name)
        g = c.add_mutually_exclusive_group(required=True)
        g.add_argument("--project")
        g.add_argument("--config", type=Path)
        c.add_argument("--output", type=Path)
        if name in {"check", "verify"}:
            c.add_argument("--scope", choices=("schematic", "pcb", "release") if name == "verify" else ("schematic", "pcb"), required=True)
        if name == "check": c.add_argument("--netlist", type=Path)
        if name == "export": c.add_argument("--kind", choices=("bom", "procurement", "netlist", "pdf"), required=True)
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
    return p

def main(argv=None):
    try:
        args = parser().parse_args(argv)
        if args.command == "test":
            print("Test migration is not yet implemented")
            return 1
        project = load_project(args.config) if args.config else resolve_project(args.project)
        if getattr(args, "scope", "") in {"pcb", "release"}: project.require_board()
        print(f"{args.command}: implementation pending for {project.id}")
        return 1
    except ProjectError as exc:
        print(f"Configuration error: {exc}")
        return 64
