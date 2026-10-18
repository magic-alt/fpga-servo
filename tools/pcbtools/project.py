"""Strict project configuration; paths never depend on the caller's cwd."""
from dataclasses import dataclass
from pathlib import Path
import json

KNOWN_RULES = frozenset({"repository", "servo", "adc_serial", "adc_fast", "ad7606c", "protection", "power_layout", "archived_pcb", "aux_power", "dc_link"})
class ProjectError(ValueError):
    pass

@dataclass(frozen=True)
class Project:
    id: str
    root: Path
    schematic: Path
    board: Path | None
    libraries: tuple[Path, ...]
    bom: Path | None
    output: Path
    rule_sets: tuple[str, ...]
    parameters: dict
    config: Path

    def require_board(self) -> Path:
        if self.board is None or not self.board.is_file():
            raise ProjectError(f"{self.id}: requested PCB workflow requires a board")
        return self.board

    def safe_output(self, output: Path) -> Path:
        output = output.resolve()
        sources = [self.schematic, *self.libraries]
        sources += [p for p in (self.board, self.bom) if p]
        sources += list(local_dependencies(self))
        # Evidence directories must be separate from source directories.
        for source in sources:
            if output == source or output == source.parent or output in source.parents:
                raise ProjectError("Output overlaps project sources")
        if output.exists() and not output.is_dir():
            raise ProjectError("Output must be a directory")
        for dependency in local_dependencies(self):
            if dependency.suffix.lower() in {".kicad_mod",".step",".stp",".wrl"} and output.is_relative_to(dependency.parent):
                raise ProjectError("Output overlaps local library sources")
        return output

def load_project(path: Path) -> Project:
    path = path.resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        fields = {"schema_version", "id", "root", "schematic", "board", "libraries", "bom", "output", "rule_sets", "parameters"}
        if not isinstance(data, dict) or set(data) - fields:
            raise ProjectError("Unknown project configuration fields")
        if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
            raise ProjectError("schema_version must be 1")
        for key in ("id", "root", "schematic", "output"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                raise ProjectError(f"Missing or invalid {key}")
        root = (path.parent / data["root"]).resolve()
        def source(name, value):
            if not isinstance(value, str) or not value or Path(value).is_absolute():
                raise ProjectError(f"{name} must be a relative file path")
            result = (root / value).resolve()
            if not result.is_relative_to(root) or not result.is_file():
                raise ProjectError(f"Missing or outside-root {name}")
            if result.name == ".env" or result.name.startswith(".env."):
                raise ProjectError("Sensitive files cannot be project inputs")
            return result
        rules = data.get("rule_sets", [])
        if not isinstance(rules, list) or any(not isinstance(r, str) or r not in KNOWN_RULES for r in rules) or len(rules) != len(set(rules)):
            raise ProjectError("Unknown or duplicate rule sets")
        params = data.get("parameters", {})
        if not isinstance(params, dict): raise ProjectError("parameters must be an object")
        libs = data.get("libraries", [])
        if not isinstance(libs, list): raise ProjectError("libraries must be an array")
        output_value = Path(data["output"])
        if output_value.is_absolute() or ".." in output_value.parts:
            raise ProjectError("output must stay within the project root")
        p = Project(data["id"], root, source("schematic", data["schematic"]),
                    source("board", data["board"]) if data.get("board") else None,
                    tuple(source("library", x) for x in libs),
                    source("bom", data["bom"]) if data.get("bom") else None,
                    (root / output_value).resolve(), tuple(rules), params, path)
        p.safe_output(p.output)
        return p
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        raise ProjectError(f"Cannot load project configuration: {type(exc).__name__}") from exc

def resolve_project(name: str) -> Project:
    if name not in {"ads8588s", "ad7606c"}:
        raise ProjectError(f"Unknown project: {name}; use --config for another board")
    return load_project(Path(__file__).resolve().parents[1] / "projects" / (name + ".json"))


def local_dependencies(project: Project) -> set[Path]:
    """Collect declared local tables, lands/models and adjacent project metadata.

    Installed libraries using other KiCad variables remain external dependencies;
    no environment values are read or expanded.
    """
    from .kicad import extract_forms, head_string
    home=project.schematic.parent
    paths=set()
    directories={p for p in home.iterdir() if p.is_dir() and p.suffix in {".pretty",".3dshapes"}}
    for name in ("sym-lib-table","fp-lib-table"):
        table=home/name
        if not table.is_file():continue
        paths.add(table)
        for form in extract_forms(table.read_text(encoding="utf-8"),"uri"):
            uri=head_string(form.text,"uri") or ""
            if uri.startswith("${KIPRJMOD}"):
                target=(home/uri.replace("${KIPRJMOD}/","",1)).resolve()
            elif "$" not in uri and Path(uri).is_absolute() and Path(uri).resolve().is_relative_to(project.root):
                target=Path(uri).resolve()
            elif "$" not in uri and not Path(uri).is_absolute():target=(home/uri).resolve()
            else:continue
            if not target.is_relative_to(project.root):raise ProjectError("Project-local library outside root")
            if target.is_dir():directories.add(target)
            elif target.is_file():paths.add(target)
    for directory in directories:
        for p in directory.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".kicad_mod",".kicad_sym",".step",".stp",".wrl"}:
                if not p.resolve().is_relative_to(project.root): raise ProjectError("Local library symlink outside root")
                paths.add(p)
    for suffix in (".kicad_pro",".kicad_dru"):
        path=project.schematic.with_suffix(suffix)
        if path.is_file(): paths.add(path)
    extras=project.parameters.get("source_files",[])
    if not isinstance(extras,list): raise ProjectError("source_files must be an array")
    for name in extras:
        if not isinstance(name,str) or not name or Path(name).is_absolute(): raise ProjectError("Invalid source_files path")
        path=(project.root/name).resolve()
        if not path.is_relative_to(project.root) or not path.is_file() or any(part==".env" or part.startswith(".env.") for part in path.parts):
            raise ProjectError("Missing, sensitive or outside-root source_files input")
        paths.add(path)
    return paths
