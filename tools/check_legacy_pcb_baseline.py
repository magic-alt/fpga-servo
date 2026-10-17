"""Detect changes to the preserved, unsynchronized PCB; never certify its release.

The exact known blockers are checked, not ignored. Fresh native netlists enable
full parity/constraint comparison. Default strict PCB tools remain unchanged.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

from check_vendor_lands import check as vendor_lands, check_internal_pad_rules
from check_pcb_parity import audit_text
from check_pcb_constraints import check as constraints

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware/ads8588s_servo"
BASELINE = HW / "evidence/pcb_ci_baseline.json"
CORE_KEYS = {"source_sha256", "design_errors", "vendor_lands", "internal_pad_rules"}


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return sorted((canonical(item) for item in value),
                      key=lambda item: json.dumps(item, sort_keys=True))
    return value


def collect_snapshot(netlist: Path | None = None) -> dict:
    sources = {name: (HW / ("ax7010_servo_reva" + suffix)).read_text(encoding="utf-8")
               for name, suffix in [("board", ".kicad_pcb"), ("project", ".kicad_pro"),
                                    ("rules", ".kicad_dru")]}
    snapshot = {"source_sha256": {name: hashlib.sha256(text.encode()).hexdigest()
                                  for name, text in sources.items()},
                "vendor_lands": vendor_lands(sources["board"]),
                "internal_pad_rules": check_internal_pad_rules(sources["rules"])}
    if netlist is not None:
        text = netlist.read_text(encoding="utf-8")
        parity = audit_text(text, sources["board"], {"H1", "H2", "H3", "H4"})
        if not parity["schematic_components"] or not parity["schematic_nets"]:
            raise ValueError("Empty netlist cannot establish archived PCB regression")
        if set(parity["mechanical_preserved"]) != {"H1", "H2", "H3", "H4"}:
            raise ValueError("Archived board mechanical features changed")
        snapshot["parity"] = parity
        snapshot["constraints"] = constraints(sources["board"], json.loads(sources["project"]), text)
    proc = subprocess.run([sys.executable, str(ROOT / "tools/check_design.py")],
                          cwd=ROOT, capture_output=True, text=True)
    lines = proc.stdout.splitlines()
    errors = [line[3:] for line in lines if line.startswith(" - ")]
    if proc.returncode != 1 or not lines or lines[0] != "DESIGN CHECK FAILED" or not errors or proc.stderr:
        raise ValueError("Strict design checker did not produce the recorded blocked result")
    snapshot["design_errors"] = errors
    return canonical(snapshot)


def compare_snapshot(actual: dict, expected: dict, *, require_parity: bool = False) -> list[str]:
    required = CORE_KEYS | ({"parity", "constraints"} if require_parity or "parity" in actual or "constraints" in actual else set())
    errors = []
    if set(actual) != required:
        errors.append("Missing or unexpected regression checks")
    for key in required:
        if key not in actual or key not in expected or canonical(actual[key]) != canonical(expected[key]):
            errors.append(key + ": differs from preserved PCB baseline; review required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netlist", type=Path, help="Fresh native netlist, required for parity coverage")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    if expected["pcb_release"] != "BLOCKED":
        raise ValueError("Archived PCB cannot claim release approval")
    snapshot = collect_snapshot(args.netlist)
    errors = compare_snapshot(snapshot, expected["snapshot"], require_parity=args.netlist is not None)
    report = {"regression": "FAILED" if errors else "UNCHANGED_KNOWN_BLOCKERS",
              "pcb_release": "BLOCKED", "fresh_parity_evaluated": args.netlist is not None,
              "snapshot": snapshot, "errors": errors}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("ARCHIVED PCB REGRESSION " + ("FAILED" if errors else "PASSED") + "; PCB release: BLOCKED")
    for error in errors:
        print(" - " + error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
