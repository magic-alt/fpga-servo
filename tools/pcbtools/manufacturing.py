"""Fail-closed engineering-prototype gates and local manufacturing artifacts.

Review files are human engineering evidence, never generated approvals. CAD
prototype readiness is deliberately independent of physical release gates.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import os
import stat
from dataclasses import replace

from .kicad import extract_forms, direct_child_forms, head_string, property_value, run_native
from .project import ProjectError, local_dependencies, load_project
from .report import Finding

REQUIRED_REVIEWS = ("component", "footprint", "electrical", "thermal_budget",
                    "critical_layout", "mechanical", "dfm")
GERBER_LAYERS = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu", "F.Mask", "B.Mask",
                 "F.Paste", "B.Paste", "F.SilkS", "B.SilkS", "Edge.Cuts")
GERBER_NATIVE_SUFFIXES = {
    "F.Cu": "F_Cu", "In1.Cu": "In1_Cu", "In2.Cu": "In2_Cu", "B.Cu": "B_Cu",
    "F.Mask": "F_Mask", "B.Mask": "B_Mask", "F.Paste": "F_Paste",
    "B.Paste": "B_Paste", "F.SilkS": "F_Silkscreen",
    "B.SilkS": "B_Silkscreen", "Edge.Cuts": "Edge_Cuts",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fabrication_spec_sha256(profile):
    """Bind all manufacturing intent, excluding only the self-referencing registry."""
    if not isinstance(profile, dict):
        raise ProjectError("Fabrication profile must be an object")
    spec = {key: value for key, value in profile.items() if key != "reviews"}
    return hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def local_reference(project, name, home):
    """Resolve explicit local CAD references without reading environment values."""
    if not isinstance(name, str) or not name:
        raise ProjectError("Empty CAD dependency reference")
    if name.startswith("${KIPRJMOD}/"):
        name = name[len("${KIPRJMOD}/"):]
    if "$" in name or "~" in name:
        raise ProjectError("Actual CAD dependency must use an explicit project-local path")
    path = (home / name).resolve()
    if not path.is_relative_to(project.root) or not path.exists():
        raise ProjectError("Actual CAD dependency missing or outside project root")
    if any(part == ".env" or part.startswith(".env.") for part in path.parts):
        raise ProjectError("Sensitive files cannot be CAD dependencies")
    return path


def board_model_dependencies(project):
    """Only actual board-selected models are mandatory, not unused library models."""
    paths = set()
    if project.board:
        for form in extract_forms(project.board.read_text(encoding="utf-8"), "model"):
            path = local_reference(project, head_string(form.text, "model"), project.schematic.parent)
            if not path.is_file() or path.suffix.lower() not in {".step", ".stp", ".wrl"}:
                raise ProjectError("Actual model must be an existing local STEP/WRL file")
            paths.add(path)
    return paths


def relocated_project(project, root):
    def path(value):
        return root / value.relative_to(project.root) if value else None
    return replace(project, root=root, schematic=path(project.schematic), board=path(project.board),
                   libraries=tuple(path(p) for p in project.libraries), bom=path(project.bom),
                   config=path(project.config), output=path(project.output))


def freeze_design(project, destination, expected_source_hashes=None):
    """Copy verified inputs and rebase actual native references into a fresh snapshot."""
    destination = destination.resolve()
    before = design_source_hashes(project)
    if expected_source_hashes is not None and before != expected_source_hashes:
        raise ProjectError("Design differs from the reviewed inputs before freezing")
    destination.mkdir(parents=True, exist_ok=False)
    projects = [project]
    while projects[-1].parameters.get("baseline_config"):
        projects.append(load_project(input_path(projects[-1], projects[-1].parameters["baseline_config"])))
    # The review registry is intentionally outside design_source_hashes to
    # avoid self-referential review hashes. Native fabrication-intent checks
    # still consume the profile, so freeze it as a separately bound input.
    inputs = dict(before)
    for owner in projects:
        if owner.parameters.get("fabrication_profile"):
            profile = input_path(owner, owner.parameters["fabrication_profile"])
            inputs[profile.relative_to(project.root).as_posix()] = sha256(profile)
    for name, expected in inputs.items():
        source = project.root / name
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ProjectError("Design changed while copying frozen inputs")
        target.write_bytes(data)
    for name in inputs:
        source = project.root / name
        target = destination / name
        owner = max((p for p in projects if source.is_relative_to(p.schematic.parent)),
                    key=lambda p: len(p.schematic.parent.parts), default=project)
        if source.suffix == ".kicad_sch":
            text = target.read_text(encoding="utf-8")
            for form in extract_forms(text, "property"):
                if head_string(form.text, "property") != "Sheetfile":
                    continue
                match = re.match(r'\(property\s+"Sheetfile"\s+("(?:[^"\\]|\\.)*")', form.text)
                if not match:
                    raise ProjectError("Unsupported child schematic reference")
                dependency = local_reference(owner, json.loads(match[1]), source.parent)
                relative = os.path.relpath(destination / dependency.relative_to(project.root), target.parent).replace("\\", "/")
                new = form.text[:match.start(1)] + json.dumps(relative) + form.text[match.end(1):]
                text = text.replace(form.text, new)
            target.write_text(text, encoding="utf-8", newline="")
        heads = ("uri",) if source.name in {"fp-lib-table", "sym-lib-table"} else ("model",) if source.suffix in {".kicad_pcb", ".kicad_mod"} else ()
        if not heads:
            continue
        text = target.read_text(encoding="utf-8")
        for head in heads:
            for form in extract_forms(text, head):
                raw = head_string(form.text, head)
                try:
                    dependency = local_reference(owner, raw, owner.schematic.parent)
                except ProjectError:
                    # Unused library models never participate in native board export.
                    if head == "model" and source.suffix == ".kicad_mod":
                        continue
                    raise
                frozen_target = destination / dependency.relative_to(project.root)
                if not frozen_target.exists():
                    if head == "model" and source.suffix == ".kicad_mod":
                        continue
                    raise ProjectError("CAD dependency omitted from frozen inputs")
                relative = os.path.relpath(frozen_target, destination / owner.schematic.parent.relative_to(project.root)).replace("\\", "/")
                value = "${KIPRJMOD}/" + relative
                old = re.match(r'\(' + head + r'\s+"(?:[^"\\]|\\.)*"', form.text)
                if not old:
                    raise ProjectError("Unsupported CAD dependency reference")
                new = "(" + head + " " + json.dumps(value)
                text = text.replace(form.text, new + form.text[old.end():])
        target.write_text(text, encoding="utf-8", newline="")
    if design_source_hashes(project) != before:
        raise ProjectError("Design changed while freezing inputs")
    if any(sha256(project.root / name) != digest for name, digest in inputs.items()):
        raise ProjectError("Manufacturing inputs changed while freezing")
    files = {name: {"source_sha256": digest, "snapshot_sha256": sha256(destination / name)}
             for name, digest in inputs.items()}
    for name in files:
        (destination / name).chmod(stat.S_IREAD)
    evidence = {"root": str(destination), "files": files}
    return relocated_project(project, destination), evidence


def check_frozen_design(evidence):
    root = Path(evidence["root"]).resolve()
    for name, record in evidence["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != record["snapshot_sha256"]:
            raise ProjectError("Frozen native input changed or disappeared")


def input_path(project, name):
    if not isinstance(name, str) or not name.strip() or Path(name).is_absolute():
        raise ProjectError("Evidence path must be a nonempty root-relative file")
    path = (project.root / name).resolve()
    if not path.is_relative_to(project.root) or not path.is_file():
        raise ProjectError("Evidence file missing or outside project root")
    if any(p == ".env" or p.startswith(".env.") for p in path.parts):
        raise ProjectError("Sensitive files cannot be evidence")
    if not path.stat().st_size:
        raise ProjectError("Evidence file is empty")
    return path


def design_source_hashes(project):
    """Hash actual selected design inputs, including configured baseline inputs.

    No repository-wide tracked-file sweep: an unrelated board or tool edit must
    not be mistaken for a change to this engineering freeze.
    """
    from .schematic import discover_sheets
    paths = set()
    visited = set()

    def collect(p):
        if p.config in visited:
            raise ProjectError("Circular baseline configuration")
        visited.add(p.config)
        paths.update({p.config, p.schematic, *p.libraries})
        paths.update(discover_sheets(p))
        paths.update(local_dependencies(p))
        paths.update(board_model_dependencies(p))
        paths.update(x for x in (p.board, p.bom) if x)
        baseline = p.parameters.get("baseline_config")
        if baseline:
            collect(load_project(input_path(p, baseline)))

    collect(project)
    return {p.relative_to(project.root).as_posix(): sha256(p) for p in sorted(paths)}


def checked_evidence(project, record):
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise ProjectError("Evidence requires path and sha256")
    path = input_path(project, record["path"])
    if not re.fullmatch(r"[a-f0-9]{64}", str(record["sha256"])) or sha256(path) != record["sha256"]:
        raise ProjectError("Evidence SHA-256 mismatch")
    return path


def check_native_settings(project):
    """Reject disabled/ignored categories and exclusions in native project rules."""
    settings = json.loads(input_path(project, project.schematic.with_suffix(".kicad_pro").relative_to(project.root).as_posix()).read_text(encoding="utf-8-sig"))
    for section in (settings["board"]["design_settings"], settings["erc"]):
        severities = section.get("rule_severities")
        if not isinstance(severities, dict) or not severities:
            raise ProjectError("Complete native ERC/DRC severity settings required")
        if any(s not in {"error", "warning"} for s in severities.values()):
            raise ProjectError("Ignored or disabled native check")
    def inspect(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if ("exclusion" in key.lower() or key.lower().startswith("ignored")) and child:
                    raise ProjectError("Native exclusions or ignored checks are forbidden")
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
    inspect(settings)
    minima = project.parameters.get("native_manufacturing_minima", {})
    if not isinstance(minima, dict):
        raise ProjectError("Native manufacturing minima must be a mapping")
    native_rules = settings["board"]["design_settings"].get("rules", {})
    for key, minimum in minima.items():
        actual = native_rules.get(key)
        if (type(minimum) not in {int, float} or not math.isfinite(minimum)
                or minimum <= 0 or type(actual) not in {int, float}
                or not math.isfinite(actual) or actual < minimum):
            raise ProjectError(f"{key}: native manufacturing minimum missing or weakened")
    custom = project.schematic.with_suffix(".kicad_dru")
    if custom.exists() and re.search(r"\(severity\s+(?:ignore|exclusion)\b", custom.read_text(encoding="utf-8"), re.I):
        raise ProjectError("Custom DRC rule suppresses a check")
    if project.parameters.get("forbid_footprint_clearance_overrides"):
        text = project.require_board().read_text(encoding="utf-8")
        for footprint in extract_forms(text, "footprint"):
            owners = [footprint.text, *(pad.text for pad in direct_child_forms(footprint.text, "pad"))]
            if any(direct_child_forms(owner, "clearance") for owner in owners):
                ref = property_value(footprint.text, "Reference")
                raise ProjectError(f"{ref}: broad footprint/pad clearance override forbidden; use reviewed same-instance rules")


def check_stackup(project, stack):
    if not isinstance(stack, dict) or stack.get("copper_layers") != 4:
        raise ProjectError("Manufacturer four-layer stackup required")
    if not all(isinstance(stack.get(k), str) and stack[k].strip() for k in ("profile_id", "dielectric_material")):
        raise ProjectError("Actual manufacturer stackup ID and dielectric required")
    checked_evidence(project, stack.get("evidence"))
    oz = stack.get("copper_oz")
    if not isinstance(oz, list) or len(oz) != 4 or any(type(x) not in {int, float} or not math.isfinite(x) or x <= 0 for x in oz):
        raise ProjectError("Four physical copper weights required")
    copper = stack.get("copper_thickness_mm")
    if not isinstance(copper, list) or len(copper) != 4 or any(type(x) not in {int, float} or not math.isfinite(x) or x <= 0 for x in copper):
        raise ProjectError("Four actual manufacturer copper thicknesses required")
    thickness = stack.get("thickness_mm")
    if type(thickness) not in {int, float} or not math.isfinite(thickness) or thickness <= 0:
        raise ProjectError("Physical board thickness required")
    text = project.require_board().read_text(encoding="utf-8")
    layers = extract_forms(text, "layers")
    if not layers or re.findall(r'"([^"]+\.Cu)"', layers[0].text) != list(GERBER_LAYERS[:4]):
        raise ProjectError("Board must have the declared four copper layers")
    general = extract_forms(text, "general")
    actual = re.search(r"\(thickness\s+([\d.]+)\)", general[0].text if general else "")
    if not actual or abs(float(actual[1]) - thickness) > 0.001:
        raise ProjectError("Board thickness differs from manufacturer profile")
    forms = extract_forms(text, "stackup")
    if len(forms) != 1:
        raise ProjectError("Native board stackup must be explicitly frozen")
    native_forms = extract_forms(forms[0].text, "layer")
    native = {head_string(f.text, "layer"): f.text for f in native_forms}
    if len(native) != len(native_forms) or any(not isinstance(name, str) or not name for name in native):
        raise ProjectError("Duplicate or unnamed native stackup layer")
    copper_names = set(GERBER_LAYERS[:4])
    dielectric_names = {"dielectric 1", "dielectric 2", "dielectric 3"}
    artwork_names = {"F.SilkS", "F.Paste", "B.Paste", "B.SilkS"}
    mask_names = {"F.Mask", "B.Mask"}
    if {name for name in native if name.endswith(".Cu")} != copper_names or {name for name in native if name.startswith("dielectric ")} != dielectric_names:
        raise ProjectError("Four copper and three native dielectric layers required")
    if set(native) - copper_names - dielectric_names - artwork_names - mask_names:
        raise ProjectError("Unexpected native stackup layer")
    total = 0
    for name, layer in native.items():
        if name in artwork_names:
            continue  # Native silk/paste descriptors have no physical thickness.
        match = re.search(r"\(thickness\s+([\d.]+)\)", layer)
        if not match or not math.isfinite(float(match[1])) or float(match[1]) <= 0:
            raise ProjectError("Native stackup layer thickness missing")
        if name not in mask_names:
            total += float(match[1])
    for layer, finished_thickness in zip(GERBER_LAYERS[:4], copper):
        match = re.search(r"\(thickness\s+([\d.]+)\)", native.get(layer, ""))
        if not match or abs(float(match[1]) - finished_thickness) > 0.001:
            raise ProjectError("Native copper thickness differs from manufacturer profile")
    dielectrics = [native[name] for name in sorted(dielectric_names)]
    if not dielectrics or any(not extract_forms(v, "material") or head_string(extract_forms(v, "material")[0].text, "material") != stack["dielectric_material"] for v in dielectrics):
        raise ProjectError("Native dielectric differs from manufacturer profile")
    if abs(total - thickness) > 0.05:
        raise ProjectError("Native stackup thickness does not match board")
    declared = stack.get("dielectric_layers")
    if not isinstance(declared, list) or len(declared) != 3:
        raise ProjectError("Three explicit manufacturer dielectric layers required")
    for index, record in enumerate(declared, 1):
        name = "dielectric " + str(index)
        if not isinstance(record, dict) or record.get("name") != name or record.get("type") not in {"prepreg", "core"}:
            raise ProjectError("Manufacturer dielectric layer name/type missing")
        layer = native[name]
        types = extract_forms(layer, "type")
        if len(types) != 1 or head_string(types[0].text, "type") != record["type"]:
            raise ProjectError("Native dielectric type differs from manufacturer profile")
        for key, head in (("thickness_mm", "thickness"), ("epsilon_r", "epsilon_r")):
            value = record.get(key)
            match = re.search(r"\(" + head + r"\s+([\d.]+)\)", layer)
            if (type(value) not in {int, float} or not math.isfinite(value) or value <= 0
                    or not match or abs(float(match[1]) - value) > 1e-6):
                raise ProjectError("Native dielectric " + key + " differs from manufacturer profile")


def check_prototype_inputs(project):
    findings, evidence = [], {"prototype_ready": "BLOCKED", "pcb_release": "BLOCKED"}
    try:
        check_native_settings(project)
        findings.append(Finding("prototype.native_settings", "PASS", "Native checks enabled; no exclusions"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        findings.append(Finding("prototype.native_settings", "FAIL", str(exc)))
    try:
        hashes = design_source_hashes(project)
        evidence["design_source_hashes"] = hashes
        profile_path = input_path(project, project.parameters.get("fabrication_profile"))
        profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
        if profile.get("schema_version") != 1 or profile.get("project_id") != project.id or not str(profile.get("manufacturer", "")).strip():
            raise ProjectError("Invalid fabrication profile identity or manufacturer")
        evidence["fabrication_profile_sha256"] = sha256(profile_path)
        spec_digest = fabrication_spec_sha256(profile)
        evidence["fabrication_spec_sha256"] = spec_digest
        check_stackup(project, profile.get("stackup"))
        findings.append(Finding("prototype.stackup", "PASS", "Native four-layer manufacturer stackup matches profile"))
        evidence["engineering_reviews"] = {}
        reviews = profile.get("reviews", {})
        for subject in REQUIRED_REVIEWS:
            try:
                record = reviews.get(subject)
                review_path = checked_evidence(project, record)
                review = json.loads(review_path.read_text(encoding="utf-8-sig"))
                if (review.get("schema_version") != 1 or review.get("project_id") != project.id
                        or review.get("subject") != subject or review.get("status") != "PASS"
                        or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip()):
                    raise ProjectError("Signed engineering PASS review required")
                when = datetime.fromisoformat(review["reviewed_utc"].replace("Z", "+00:00"))
                if when.tzinfo is None or when > datetime.now(timezone.utc):
                    raise ProjectError("Invalid engineering review timestamp")
                if review.get("source_hashes") != hashes:
                    raise ProjectError("Engineering review is stale for actual design inputs")
                if review.get("fabrication_spec_sha256") != spec_digest:
                    raise ProjectError("Engineering review is stale for actual manufacturing specification")
                attachments = review.get("evidence")
                if not isinstance(attachments, list) or not attachments:
                    raise ProjectError("Review requires hashed engineering evidence files")
                for item in attachments:
                    checked_evidence(project, item)
                evidence["engineering_reviews"][subject] = {"review": record, "evidence": attachments}
                findings.append(Finding("prototype.review." + subject, "PASS", "Source-bound engineering review and evidence"))
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                findings.append(Finding("prototype.review." + subject, "FAIL", str(exc)))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        findings.append(Finding("prototype.profile", "FAIL", str(exc)))
    return findings, evidence


def validate_fabrication_outputs(output):
    """A successful subprocess without all nonempty deliverables is a failure."""
    required = [output / name for name in ("assembly.csv", "assembly-native.csv",
                "assembly-bom.csv", "assembly-consistency.json", "board.step",
                "drawing.pdf", "bom.csv", "bom-source.xml")]
    gerbers = set()
    for layer in GERBER_LAYERS:
        matches = list((output / "gerbers").glob("*-" + GERBER_NATIVE_SUFFIXES[layer] + ".gbr"))
        if len(matches) != 1:
            raise ProjectError("Missing or ambiguous Gerber layer " + layer)
        required.extend(matches)
        gerbers.update(matches)
    if set((output / "gerbers").glob("*.gbr")) != gerbers:
        raise ProjectError("Unexpected or ambiguous Gerber layer files")
    drills = list((output / "drill").glob("*.drl"))
    if not drills:
        raise ProjectError("Missing native Excellon drill")
    required.extend(drills)
    if any(not p.is_file() or not p.stat().st_size for p in required):
        raise ProjectError("Missing or empty fabrication output")
    return {p.relative_to(output).as_posix(): sha256(p) for p in required}


def export_fabrication(project, output, tools):
    """Run a new prototype verification; never accept a historical PASS manifest."""
    from .verification import verify
    from .export import export_bom, export_assembly
    from .report import exit_code
    report = verify(project, "prototype", output, tools)
    out = Path(report.evidence["output"])
    report.evidence["fabrication_export"] = "BLOCKED"
    if exit_code(report) or report.evidence.get("prototype_ready") != "PASS":
        report.findings.append(Finding("export.fabrication", "FAIL", "Fresh prototype verification blocked fabrication export"))
        return report
    try:
        before = design_source_hashes(project)
        if before != report.evidence["design_source_hashes"]:
            raise ProjectError("Design changed after prototype verification")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report.evidence["prototype_ready"] = "BLOCKED"
        report.findings.append(Finding("export.fabrication", "FAIL", str(exc)))
        return report
    try:
        frozen = report.evidence.get("frozen_design")
        if frozen is None:
            native_project, frozen = freeze_design(project, out / "frozen-design", before)
            report.evidence["frozen_design"] = frozen
        else:
            native_project = relocated_project(project, Path(frozen["root"]))
        check_frozen_design(frozen)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report.evidence["prototype_ready"] = "BLOCKED"
        report.findings.append(Finding("export.fabrication", "FAIL", str(exc)))
        return report
    cli = tools.get("kicad-cli", "kicad-cli")
    for folder in ("gerbers", "drill"):
        (out / folder).mkdir()
    commands = [
        ("gerbers", ["gerbers", "--no-protel-ext", "--check-zones", "--layers", ",".join(GERBER_LAYERS), "--output", str(out / "gerbers") + "/"]),
        ("drill", ["drill", "--format", "excellon", "--excellon-separate-th", "--generate-map", "--generate-report", "--output", str(out / "drill") + "/"]),
        ("position", ["pos", "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", "--output", str(out / "assembly.csv")]),
        ("step", ["step", "--output", str(out / "board.step")]),
        ("drawing", ["pdf", "--mode-single", "--layers", "F.Fab,B.Fab,Edge.Cuts,Dwgs.User", "--output", str(out / "drawing.pdf")]),
    ]
    try:
        for name, args in commands:
            check_frozen_design(frozen)
            command = [cli, "pcb", "export", *args, str(native_project.board)]
            result = run_native(command, native_project.root, 300)
            log = "fabrication-" + name + ".log"
            (out / log).write_text(result.get("stdout", "") + result.get("stderr", "") + result.get("error", ""), encoding="utf-8")
            report.evidence["steps"].append({"name": "fabrication-" + name, "command": [Path(cli).name, *command[1:]], "exit_code": result["exit_code"], "status": result["status"], "log": log})
            if result["exit_code"]:
                raise ProjectError("Native fabrication " + name + " failed")
        export_bom(native_project, out, cli)
        export_assembly(native_project, out, cli)
        report.evidence["steps"].append({"name": "fabrication-bom", "command": [Path(cli).name, "sch", "export", "netlist", "--format", "kicadxml", "--output", str(out / "bom-source.xml"), str(native_project.schematic)], "exit_code": 0, "status": "PASS"})
        report.evidence["fabrication_outputs_sha256"] = validate_fabrication_outputs(out)
        if design_source_hashes(project) != before:
            raise ProjectError("Frozen design changed during fabrication export")
        check_frozen_design(frozen)
        findings, evidence = check_prototype_inputs(project)
        if any(f.status != "PASS" for f in findings) or any(v != report.evidence.get(k) for k, v in evidence.items() if k != "prototype_ready"):
            raise ProjectError("Engineering evidence changed during fabrication export")
        report.evidence["fabrication_export"] = "PASS_LOCAL_EXPORT_PENDING_INDEPENDENT_CAM_REVIEW"
        report.findings.append(Finding("export.fabrication", "PASS", "Native local fabrication files exported; independent CAM/package review required"))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, SyntaxError) as exc:
        report.evidence["prototype_ready"] = "BLOCKED"
        report.findings.append(Finding("export.fabrication", "FAIL", str(exc)))
    return report
