"""Explicit, allowlisted project rule selection."""
import json
from pathlib import Path
from ..report import Finding
from ..project import KNOWN_RULES, ProjectError

def run_rules(project, scope, inputs):
    if set(project.rule_sets) - KNOWN_RULES: raise ProjectError("Unregistered rule set")
    findings = []
    def check(name, operation):
        try:
            errors = operation()
            findings.append(Finding(name, "FAIL" if errors else "PASS", "; ".join(errors) if errors else "Contract passed", {"errors": errors}))
        except Exception as exc:
            findings.append(Finding(name, "FAIL", f"{type(exc).__name__}: {exc}"))
    if "repository" in project.rule_sets:
        from .repository import check_repository
        check("repository.public_paths", lambda: check_repository(project))
    if "aux_power" in project.rule_sets:
        from .aux_power import check_project
        check("power.auxiliary_1a", lambda: check_project(project, inputs.get("xml")))
    if "servo" in project.rule_sets:
        from .servo import check_design, native_contract
        check("servo.native_contract", lambda: native_contract(project))
        check("servo.design", lambda: check_design(project, schematic_only=scope=="schematic"))
    if "adc_serial" in project.rule_sets:
        from .adc import serial_api
        check("adc.serial", lambda: serial_api(project).check())
    if "adc_fast" in project.rule_sets:
        from .adc import fast_api
        check("adc.fast_candidate", lambda: fast_api(project).check())
    if "ad7606c" in project.rule_sets:
        from .adc import ad7606c_api
        api = ad7606c_api(project)
        check("adc.ad7606c", api.source_checks)
        check("adc.profile", lambda: api.profile_errors(json.loads((project.schematic.parent/"adc_profile.json").read_text(encoding="utf-8")), (project.schematic.parent/"ax7010_servo_ad7606c.xdc").read_text(encoding="utf-8")))
        if inputs.get("xml") and inputs.get("baseline_xml"):
            def electrical():
                components,pins=api.load_xml(inputs["xml"])
                old=api.load_xml(inputs["baseline_xml"])
                errors=api.electrical_errors(components,pins)+api.inherited_errors(old,(components,pins))
                if not errors:
                    api.self_tests(components,pins,old)
                    from .protection import ocp_behavior
                    ocp_behavior(pins)
                return errors
            check("adc.ad7606c_electrical",electrical)
        elif inputs.get("require_netlist"):
            findings.append(Finding("adc.ad7606c_electrical","NOT_RUN","Fresh target and baseline XML required"))
    if "archived_pcb" in project.rule_sets and scope=="schematic":
        from .servo import baseline_api
        def archived():
            api=baseline_api(project)
            expected=json.loads(api.BASELINE.read_text(encoding="utf-8"))["snapshot"]
            return api.compare_snapshot(api.collect_snapshot(inputs.get("netlist")),expected,require_parity=bool(inputs.get("netlist")))
        check("pcb.archived_regression",archived)
    if "protection" in project.rule_sets:
        xml=inputs.get("xml")
        netlist=inputs.get("netlist")
        if xml:
            from .adc import validity_api
            check("adc.supply_validity",lambda: validity_api().verify(xml)[0])
            if "servo" in project.rule_sets:
                from .servo import selection_contract
                from .protection import electrical_api
                check("servo.selection",lambda: selection_contract(xml))
                check("protection.physical",lambda: _physical(electrical_api(),xml))
        if netlist and "servo" in project.rule_sets:
            from .protection import check_safety, ocp_behavior
            check("protection.safety",lambda:check_safety(project,netlist))
            def behavior():
                from .protection import electrical_api
                _,pins=electrical_api().read_netlist(xml)
                ocp_behavior(pins)
                return []
            if xml: check("protection.ocp_behavior",behavior)
        if inputs.get("require_netlist") and (not xml or not netlist):
            findings.append(Finding("protection.netlist","NOT_RUN","Fresh XML and native netlist required"))
    if scope=="pcb" and "power_layout" in project.rule_sets:
        from .power_layout import vendor_api, constraints_api, kelvin_api, escape_api
        from ..board import corners_api
        board_text=project.board.read_text(encoding="utf-8")
        check("pcb.vendor_lands",lambda:vendor_api().check(board_text))
        rules=project.board.with_suffix(".kicad_dru").read_text(encoding="utf-8")
        check("pcb.internal_pad_rules",lambda:vendor_api().check_internal_pad_rules(rules))
        if inputs.get("netlist"):
            check("pcb.constraints",lambda:constraints_api().check(board_text,json.loads(project.board.with_suffix(".kicad_pro").read_text(encoding="utf-8")),Path(inputs["netlist"]).read_text(encoding="utf-8")))
        try:
            import pcbnew
        except ImportError:
            findings.append(Finding("pcb.native_geometry","NOT_RUN","Run this command with pcbnew-enabled Python for copper geometry"))
        else:
            board=pcbnew.LoadBoard(str(project.board))
            check("pcb.kelvin",lambda:kelvin_api().audit(board)[1])
            check("pcb.escape",lambda:escape_api().audit(board)[1])
            check("pcb.corners",lambda:[str(r) for r in corners_api().audit(board) if r["category"]=="exposed_bend"])
    return findings

def _physical(api, path):
    try:
        values,pins=api.read_netlist(path)
        api.require_graph(values,pins)
        return []
    except api.TopologyError as exc:
        return [str(exc)]
